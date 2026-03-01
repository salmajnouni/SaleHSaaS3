#!/usr/bin/env python3
"""
SaleH SaaS - Knowledge Watcher Service
Monitors knowledge_inbox folder and saves new files to ChromaDB automatically
"""

import os
import time
import logging
import requests
import hashlib
import shutil
from pathlib import Path

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
log = logging.getLogger("KnowledgeWatcher")

# Settings
INBOX_DIR       = Path(os.getenv("INBOX_DIR",       "/knowledge_inbox"))
PROCESSED_DIR   = Path(os.getenv("PROCESSED_DIR",   "/knowledge_processed"))
FAILED_DIR      = Path(os.getenv("FAILED_DIR",      "/knowledge_failed"))
TIKA_URL        = os.getenv("TIKA_URL",              "http://tika:9998/tika")
CHROMADB_URL    = os.getenv("CHROMADB_URL",          "http://chromadb:8000")
OLLAMA_URL      = os.getenv("OLLAMA_URL",            "http://host.docker.internal:11434")
EMBED_MODEL     = os.getenv("EMBED_MODEL",           "nomic-embed-text:latest")
COLLECTION_NAME = os.getenv("COLLECTION_NAME",       "saleh_legal_knowledge")
SCAN_INTERVAL   = int(os.getenv("SCAN_INTERVAL",     "10"))

# Supported file types (no .md to avoid processing README)
SUPPORTED_EXTENSIONS = {
    '.pdf', '.docx', '.doc', '.txt', '.xlsx', '.xls',
    '.pptx', '.ppt', '.rtf', '.odt', '.csv'
}

# ─────────────────────────────────────────────────────────────────────────────

def ensure_dirs():
    for d in [INBOX_DIR, PROCESSED_DIR, FAILED_DIR]:
        d.mkdir(parents=True, exist_ok=True)

def get_file_hash(file_path: Path) -> str:
    h = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()

def extract_text_tika(file_path: Path) -> str:
    try:
        with open(file_path, 'rb') as f:
            response = requests.put(
                TIKA_URL,
                data=f,
                headers={
                    'Content-Type': 'application/octet-stream',
                    'Accept': 'text/plain',
                    'X-Tika-OCRLanguage': 'ara+eng'
                },
                timeout=120
            )
        if response.status_code == 200:
            return response.text
        else:
            log.error(f"Tika error {response.status_code}: {response.text[:200]}")
            return ""
    except Exception as e:
        log.error(f"Tika connection error: {e}")
        return ""

def chunk_text(text: str, chunk_size: int = 400, overlap: int = 40) -> list:
    clean = ' '.join(text.split()).strip()
    if len(clean) < 80:
        return []
    words = clean.split(' ')
    chunks = []
    step = chunk_size - overlap
    for i in range(0, len(words), step):
        chunk = ' '.join(words[i:i + chunk_size])
        if len(chunk) > 80:
            chunks.append(chunk)
    return chunks

def get_embedding(text: str) -> list:
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/embeddings",
            json={"model": EMBED_MODEL, "prompt": text},
            timeout=300
        )
        if response.status_code == 200:
            return response.json().get("embedding", [])
        log.warning(f"Ollama returned {response.status_code}")
        return []
    except Exception as e:
        log.error(f"Ollama embedding error: {e}")
        return []

def detect_chromadb_api_version() -> str:
    for version in ["v2", "v1"]:
        try:
            r = requests.get(f"{CHROMADB_URL}/api/{version}/collections", timeout=5)
            if r.status_code in [200, 401, 403]:
                log.info(f"ChromaDB API version detected: {version}")
                return version
        except Exception:
            pass
    return "v1"

CHROMA_API_VERSION = None

def get_chroma_api():
    global CHROMA_API_VERSION
    if CHROMA_API_VERSION is None:
        CHROMA_API_VERSION = detect_chromadb_api_version()
    return CHROMA_API_VERSION

def ensure_collection():
    api = get_chroma_api()
    try:
        r = requests.get(
            f"{CHROMADB_URL}/api/{api}/collections/{COLLECTION_NAME}",
            timeout=10
        )
        if r.status_code == 404:
            resp = requests.post(
                f"{CHROMADB_URL}/api/{api}/collections",
                json={
                    "name": COLLECTION_NAME,
                    "metadata": {"description": "SaleH Legal Knowledge Base"}
                },
                timeout=10
            )
            if resp.status_code in [200, 201]:
                log.info(f"Collection created: {COLLECTION_NAME}")
            else:
                log.warning(f"Collection create: {resp.status_code} - {resp.text[:100]}")
        elif r.status_code == 200:
            log.info(f"Collection exists: {COLLECTION_NAME}")
    except Exception as e:
        log.warning(f"ChromaDB collection check error: {e}")

def save_to_chromadb(chunks: list, metadata_base: dict) -> int:
    api = get_chroma_api()
    saved = 0

    for i, chunk in enumerate(chunks):
        embedding = get_embedding(chunk)
        doc_id = f"{metadata_base['source']}_{i}_{int(time.time())}"
        metadata = {**metadata_base, "chunk_index": i, "has_embedding": bool(embedding)}

        payload = {
            "ids": [doc_id],
            "documents": [chunk],
            "metadatas": [metadata]
        }
        if embedding:
            payload["embeddings"] = [embedding]
        else:
            log.warning(f"  Chunk {i}: saving without embedding (fallback)")

        try:
            response = requests.post(
                f"{CHROMADB_URL}/api/{api}/collections/{COLLECTION_NAME}/add",
                json=payload,
                timeout=30
            )
            if response.status_code in [200, 201]:
                saved += 1
            else:
                log.error(f"  ChromaDB error chunk {i}: {response.status_code} - {response.text[:150]}")
        except Exception as e:
            log.error(f"  ChromaDB save error chunk {i}: {e}")

    return saved

def move_file_safe(src: Path, dest_dir: Path):
    dest = dest_dir / src.name
    if dest.exists():
        dest = dest_dir / f"{src.stem}_{int(time.time())}{src.suffix}"
    try:
        shutil.copy2(str(src), str(dest))
        src.unlink()
        log.info(f"  Moved to: {dest_dir.name}/{dest.name}")
    except PermissionError:
        log.warning(f"  Cannot move {src.name} (permission denied) - skipping")
    except Exception as e:
        log.error(f"  Move error: {e}")

def process_file(file_path: Path):
    log.info(f"[PROCESSING] {file_path.name}")

    log.info(f"  Extracting text via Tika...")
    text = extract_text_tika(file_path)

    if not text or len(text.strip()) < 50:
        log.warning(f"  Text too short or empty - moving to failed/")
        move_file_safe(file_path, FAILED_DIR)
        return False

    log.info(f"  Extracted {len(text)} characters")

    chunks = chunk_text(text)
    log.info(f"  Split into {len(chunks)} chunks")

    if not chunks:
        log.warning(f"  No chunks generated - moving to failed/")
        move_file_safe(file_path, FAILED_DIR)
        return False

    ensure_collection()

    metadata = {
        "source": file_path.name,
        "file_type": file_path.suffix.lower(),
        "file_hash": get_file_hash(file_path),
        "ingested_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }

    log.info(f"  Saving to ChromaDB...")
    saved = save_to_chromadb(chunks, metadata)
    log.info(f"  Saved {saved}/{len(chunks)} chunks to ChromaDB")

    move_file_safe(file_path, PROCESSED_DIR)
    log.info(f"[DONE] {file_path.name}")
    return True

def scan_inbox():
    files = [
        f for f in INBOX_DIR.iterdir()
        if f.is_file()
        and f.suffix.lower() in SUPPORTED_EXTENSIONS
        and not f.name.startswith('.')
        and f.name.upper() not in ('README.MD', 'README.TXT', 'README')
    ]
    return files

def main():
    log.info("=" * 55)
    log.info("SaleH SaaS - Knowledge Watcher started")
    log.info(f"Inbox   : {INBOX_DIR}")
    log.info(f"Done    : {PROCESSED_DIR}")
    log.info(f"Failed  : {FAILED_DIR}")
    log.info(f"Interval: {SCAN_INTERVAL}s")
    log.info(f"Model   : {EMBED_MODEL}")
    log.info("=" * 55)

    ensure_dirs()

    api = get_chroma_api()
    log.info(f"ChromaDB API: /api/{api}/")

    while True:
        try:
            files = scan_inbox()

            if files:
                log.info(f"Found {len(files)} new file(s)")
                for file_path in files:
                    try:
                        process_file(file_path)
                    except Exception as e:
                        log.error(f"Error processing {file_path.name}: {e}")
                        try:
                            move_file_safe(file_path, FAILED_DIR)
                        except Exception:
                            pass

        except Exception as e:
            log.error(f"Scan error: {e}")

        time.sleep(SCAN_INTERVAL)

if __name__ == "__main__":
    main()
