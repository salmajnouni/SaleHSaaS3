#!/usr/bin/env python3
"""
SaleH SaaS - Knowledge Watcher Service v3.0
============================================
Professional document ingestion pipeline:
  1. Monitors /knowledge_inbox for new files
  2. Extracts text via Apache Tika
  3. Chunks text and generates embeddings via Ollama
  4. Stores in ChromaDB vector database
  5. Archives processed files with timestamp to /knowledge_archive
  6. Moves failed files with error report to /knowledge_failed

Folder structure:
  /knowledge_inbox      <- Drop files here
  /knowledge_processing <- File is locked here during processing (auto-managed)
  /knowledge_archive    <- Successfully processed files (with date subfolders)
  /knowledge_failed     <- Failed files + error report (.txt)
"""

import os
import sys
import time
import logging
import requests
import hashlib
import shutil
import json
from pathlib import Path
from datetime import datetime

# ─── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)
log = logging.getLogger("KnowledgeWatcher")

# ─── Configuration ────────────────────────────────────────────────────────────
INBOX_DIR       = Path(os.getenv("INBOX_DIR",       "/knowledge_inbox"))
PROCESSING_DIR  = Path(os.getenv("PROCESSING_DIR",  "/knowledge_processing"))
ARCHIVE_DIR     = Path(os.getenv("ARCHIVE_DIR",     "/knowledge_archive"))
FAILED_DIR      = Path(os.getenv("FAILED_DIR",      "/knowledge_failed"))
TIKA_URL        = os.getenv("TIKA_URL",              "http://tika:9998/tika")
CHROMADB_URL    = os.getenv("CHROMADB_URL",          "http://chromadb:8000")
OLLAMA_URL      = os.getenv("OLLAMA_URL",            "http://host.docker.internal:11434")
EMBED_MODEL     = os.getenv("EMBED_MODEL",           "nomic-embed-text:latest")
COLLECTION_NAME = os.getenv("COLLECTION_NAME",       "saleh_legal_knowledge")
SCAN_INTERVAL   = int(os.getenv("SCAN_INTERVAL",     "10"))
MAX_RETRIES     = int(os.getenv("MAX_RETRIES",       "3"))
CHUNK_SIZE      = int(os.getenv("CHUNK_SIZE",        "400"))
CHUNK_OVERLAP   = int(os.getenv("CHUNK_OVERLAP",     "40"))

# ChromaDB v2 API base path (tenant + database)
CHROMA_TENANT   = os.getenv("CHROMA_TENANT",   "default_tenant")
CHROMA_DATABASE = os.getenv("CHROMA_DATABASE", "default_database")
CHROMA_API_BASE = f"{CHROMADB_URL}/api/v2/tenants/{CHROMA_TENANT}/databases/{CHROMA_DATABASE}"

# Supported file types
SUPPORTED_EXTENSIONS = {
    '.pdf', '.docx', '.doc', '.txt', '.md', '.xlsx', '.xls',
    '.pptx', '.ppt', '.rtf', '.odt', '.csv'
}


# ─── Directory Setup ──────────────────────────────────────────────────────────
def ensure_dirs():
    for d in [INBOX_DIR, PROCESSING_DIR, ARCHIVE_DIR, FAILED_DIR]:
        d.mkdir(parents=True, exist_ok=True)

# ─── File Utilities ───────────────────────────────────────────────────────────
def get_file_hash(file_path: Path) -> str:
    h = hashlib.md5()
    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                h.update(chunk)
    except Exception:
        return "unknown"
    return h.hexdigest()

def get_archive_path(filename: str) -> Path:
    """Returns archive path with date subfolder: /knowledge_archive/2026-03-02/filename"""
    date_folder = datetime.now().strftime("%Y-%m-%d")
    dest_dir = ARCHIVE_DIR / date_folder
    dest_dir.mkdir(parents=True, exist_ok=True)
    return dest_dir / filename

def move_to_archive(src: Path) -> bool:
    """Move successfully processed file to archive with timestamp prefix"""
    timestamp = datetime.now().strftime("%H%M%S")
    dest = get_archive_path(f"{timestamp}_{src.name}")
    try:
        shutil.copy2(str(src), str(dest))
        src.unlink()
        log.info(f"  [ARCHIVED] -> archive/{dest.parent.name}/{dest.name}")
        return True
    except Exception as e:
        log.error(f"  [ARCHIVE ERROR] {e}")
        return False

def move_to_failed(src: Path, error_msg: str) -> bool:
    """Move failed file to failed/ folder with an error report"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest_name = f"{timestamp}_{src.name}"
    dest = FAILED_DIR / dest_name
    report = FAILED_DIR / f"{timestamp}_{src.stem}_error.txt"
    try:
        shutil.copy2(str(src), str(dest))
        src.unlink()
        # Write error report
        with open(report, 'w', encoding='utf-8') as f:
            f.write(f"File     : {src.name}\n")
            f.write(f"Time     : {datetime.now().isoformat()}\n")
            f.write(f"Error    : {error_msg}\n")
        log.warning(f"  [FAILED] -> failed/{dest_name}")
        log.warning(f"  [REPORT] -> failed/{report.name}")
        return True
    except PermissionError:
        log.error(f"  [FAILED] Cannot move {src.name} - permission denied")
        return False
    except Exception as e:
        log.error(f"  [FAILED] Move error: {e}")
        return False

def move_to_processing(src: Path) -> Path:
    """Lock file in processing folder during ingestion"""
    dest = PROCESSING_DIR / src.name
    if dest.exists():
        dest = PROCESSING_DIR / f"{src.stem}_{int(time.time())}{src.suffix}"
    try:
        shutil.copy2(str(src), str(dest))
        src.unlink()
        return dest
    except Exception as e:
        log.error(f"  [LOCK ERROR] Cannot move to processing: {e}")
        return src  # fallback: process in place

# ─── Text Extraction ──────────────────────────────────────────────────────────
def extract_text_tika(file_path: Path) -> str:
    for attempt in range(1, MAX_RETRIES + 1):
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
            log.warning(f"  Tika attempt {attempt}: HTTP {response.status_code}")
        except requests.exceptions.Timeout:
            log.warning(f"  Tika attempt {attempt}: Timeout")
        except Exception as e:
            log.warning(f"  Tika attempt {attempt}: {e}")
        if attempt < MAX_RETRIES:
            time.sleep(3)
    return ""

# ─── Text Chunking ────────────────────────────────────────────────────────────
def chunk_text(text: str) -> list:
    clean = ' '.join(text.split()).strip()
    if len(clean) < 80:
        return []
    words = clean.split(' ')
    chunks = []
    step = CHUNK_SIZE - CHUNK_OVERLAP
    for i in range(0, len(words), step):
        chunk = ' '.join(words[i:i + CHUNK_SIZE])
        if len(chunk) > 80:
            chunks.append(chunk)
    return chunks

# ─── Embedding ────────────────────────────────────────────────────────────────
def get_embedding(text: str) -> list:
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/embeddings",
            json={"model": EMBED_MODEL, "prompt": text},
            timeout=300
        )
        if response.status_code == 200:
            return response.json().get("embedding", [])
        log.warning(f"  Ollama: HTTP {response.status_code}")
        return []
    except requests.exceptions.Timeout:
        log.warning("  Ollama: Timeout (model may be loading)")
        return []
    except Exception as e:
        log.warning(f"  Ollama: {e}")
        return []

# ─── ChromaDB ─────────────────────────────────────────────────────────────────
def chromadb_request(method: str, path: str, **kwargs) -> requests.Response:
    """Make a ChromaDB API request, trying v2 then v1"""
    for version in ["v2", "v1"]:
        url = f"{CHROMADB_URL}/api/{version}{path}"
        try:
            resp = getattr(requests, method)(url, timeout=15, **kwargs)
            if resp.status_code != 405:
                return resp
        except Exception:
            pass
    # Last resort: return last response
    return resp

def ensure_collection() -> bool:
    """Ensure the ChromaDB collection exists, create if not. Uses v2 API with tenant/database."""
    try:
        # Check if collection exists
        r = requests.get(
            f"{CHROMA_API_BASE}/collections/{COLLECTION_NAME}",
            timeout=10
        )
        if r.status_code == 200:
            log.info(f"  ChromaDB collection OK [{CHROMA_TENANT}/{CHROMA_DATABASE}]")
            return True
        if r.status_code == 404:
            # Create collection
            rc = requests.post(
                f"{CHROMA_API_BASE}/collections",
                json={"name": COLLECTION_NAME, "metadata": {"hnsw:space": "cosine"}},
                timeout=10
            )
            if rc.status_code in [200, 201]:
                log.info(f"  ChromaDB collection created [{CHROMA_TENANT}/{CHROMA_DATABASE}]")
                return True
            log.error(f"  ChromaDB create failed: {rc.status_code} {rc.text[:200]}")
            return False
        log.error(f"  ChromaDB check failed: {r.status_code} {r.text[:200]}")
        return False
    except Exception as e:
        log.error(f"  Cannot connect to ChromaDB: {e}")
        return False

def save_chunks_to_chromadb(chunks: list, metadata_base: dict) -> tuple:
    """Save chunks to ChromaDB. Returns (saved_count, total_count)"""
    saved = 0
    errors = []

    url = f"{CHROMA_API_BASE}/collections/{COLLECTION_NAME}/add"
    log.info(f"  ChromaDB endpoint: {CHROMA_TENANT}/{CHROMA_DATABASE}/{COLLECTION_NAME}")

    for i, chunk in enumerate(chunks):
        embedding = get_embedding(chunk)
        doc_id = f"{metadata_base['file_hash']}_{i}"
        metadata = {**metadata_base, "chunk_index": i, "has_embedding": bool(embedding)}

        payload = {
            "ids": [doc_id],
            "documents": [chunk],
            "metadatas": [metadata]
        }
        if embedding:
            payload["embeddings"] = [embedding]
        else:
            log.warning(f"  Chunk {i+1}/{len(chunks)}: no embedding (saved as text-only)")

        try:
            resp = requests.post(url, json=payload, timeout=30)
            if resp.status_code in [200, 201]:
                saved += 1
                log.info(f"  Chunk {i+1}/{len(chunks)}: OK {'[with embedding]' if embedding else '[text-only]'}")
            elif resp.status_code == 409:
                # Already exists - count as success
                saved += 1
                log.info(f"  Chunk {i+1}/{len(chunks)}: already exists (skipped)")
            else:
                err = f"HTTP {resp.status_code}: {resp.text[:120]}"
                errors.append(err)
                log.error(f"  Chunk {i+1}/{len(chunks)}: FAILED - {err}")
        except Exception as e:
            errors.append(str(e))
            log.error(f"  Chunk {i+1}/{len(chunks)}: FAILED - {e}")

    return saved, len(chunks)

# ─── Main Processing Pipeline ─────────────────────────────────────────────────
def process_file(file_path: Path) -> bool:
    """
    Full processing pipeline for a single file.
    Returns True on success, False on failure.
    """
    log.info(f"{'='*55}")
    log.info(f"[START] {file_path.name}")
    log.info(f"  Size: {file_path.stat().st_size:,} bytes")

    # Step 1: Move to processing folder (lock the file)
    processing_path = move_to_processing(file_path)
    log.info(f"  [LOCKED] -> processing/{processing_path.name}")

    try:
        # Step 2: Extract text
        log.info(f"  [STEP 1/4] Extracting text via Tika...")
        text = extract_text_tika(processing_path)

        if not text or len(text.strip()) < 50:
            raise ValueError(f"Text extraction failed or too short ({len(text.strip())} chars)")

        log.info(f"  [STEP 1/4] OK - Extracted {len(text):,} characters")

        # Step 3: Chunk text
        log.info(f"  [STEP 2/4] Chunking text...")
        chunks = chunk_text(text)

        if not chunks:
            raise ValueError("Text chunking produced no chunks")

        log.info(f"  [STEP 2/4] OK - {len(chunks)} chunks (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")

        # Step 4: Ensure ChromaDB collection
        log.info(f"  [STEP 3/4] Checking ChromaDB collection...")
        if not ensure_collection():
            raise ConnectionError("ChromaDB unavailable")

        # Step 5: Save to ChromaDB
        log.info(f"  [STEP 4/4] Saving {len(chunks)} chunks to ChromaDB...")
        metadata_base = {
            "source": file_path.name,
            "file_type": file_path.suffix.lower(),
            "file_hash": get_file_hash(processing_path),
            "file_size": processing_path.stat().st_size,
            "ingested_at": datetime.utcnow().isoformat() + "Z"
        }

        saved, total = save_chunks_to_chromadb(chunks, metadata_base)
        log.info(f"  [STEP 4/4] Saved {saved}/{total} chunks")

        if saved == 0:
            raise RuntimeError(f"All {total} chunks failed to save in ChromaDB")

        # Step 6: Archive the file
        move_to_archive(processing_path)
        log.info(f"[SUCCESS] {file_path.name} - {saved}/{total} chunks ingested")
        log.info(f"{'='*55}")
        return True

    except Exception as e:
        log.error(f"[FAILED] {file_path.name} - {e}")
        move_to_failed(processing_path, str(e))
        log.info(f"{'='*55}")
        return False

# ─── Inbox Scanner ────────────────────────────────────────────────────────────
def scan_inbox() -> list:
    """Return list of processable files in inbox"""
    try:
        files = [
            f for f in INBOX_DIR.iterdir()
            if f.is_file()
            and f.suffix.lower() in SUPPORTED_EXTENSIONS
            and not f.name.startswith('.')
        ]
        return sorted(files, key=lambda f: f.stat().st_mtime)  # oldest first
    except Exception as e:
        log.error(f"Inbox scan error: {e}")
        return []

# ─── Entry Point ──────────────────────────────────────────────────────────────
def main():
    log.info("=" * 55)
    log.info("SaleH SaaS - Knowledge Watcher v3.0")
    log.info("=" * 55)
    log.info(f"Inbox      : {INBOX_DIR}")
    log.info(f"Processing : {PROCESSING_DIR}  (auto-managed)")
    log.info(f"Archive    : {ARCHIVE_DIR}/YYYY-MM-DD/")
    log.info(f"Failed     : {FAILED_DIR}")
    log.info(f"Interval   : {SCAN_INTERVAL}s")
    log.info(f"Model      : {EMBED_MODEL}")
    log.info(f"Collection : {COLLECTION_NAME}")
    log.info(f"Max retries: {MAX_RETRIES}")
    log.info("=" * 55)

    ensure_dirs()

    # Wait for ChromaDB to be ready - use v2 API (v1 is deprecated)
    log.info("Waiting for ChromaDB to be ready...")
    for attempt in range(1, 31):  # up to 5 minutes (30 x 10s)
        try:
            r = requests.get(f"{CHROMADB_URL}/api/v2/heartbeat", timeout=5)
            if r.status_code == 200:
                log.info(f"ChromaDB is ready on v2 API (attempt {attempt})")
                break
        except Exception:
            pass
        if attempt < 30:
            log.info(f"  ChromaDB not ready yet, retrying in 10s... ({attempt}/30)")
            time.sleep(10)
    else:
        log.warning("ChromaDB did not respond after 5 minutes - continuing anyway")

    # Clean up any leftover files in processing folder from previous crash
    # Only re-queue supported file types; skip anything else silently
    try:
        leftover = [f for f in PROCESSING_DIR.iterdir() if f.is_file()]
        processable = [f for f in leftover if f.suffix.lower() in SUPPORTED_EXTENSIONS and not f.name.startswith('.')]
        if processable:
            log.warning(f"Re-queuing {len(processable)} leftover file(s) from previous run")
            for f in processable:
                try:
                    dest = INBOX_DIR / f.name
                    shutil.copy2(str(f), str(dest))
                    try:
                        f.unlink()
                    except Exception:
                        pass  # Can't delete source - that's OK, copy already done
                    log.warning(f"  Re-queued: {f.name}")
                except Exception as e:
                    log.warning(f"  Skipped {f.name}: {e}")
    except Exception as e:
        log.warning(f"Processing folder cleanup skipped: {e}")

    stats = {"processed": 0, "failed": 0, "total_chunks": 0}

    while True:
        try:
            files = scan_inbox()

            if files:
                log.info(f"Found {len(files)} file(s) to process")
                for file_path in files:
                    success = process_file(file_path)
                    if success:
                        stats["processed"] += 1
                    else:
                        stats["failed"] += 1

                log.info(
                    f"Session stats: {stats['processed']} processed, "
                    f"{stats['failed']} failed"
                )

        except KeyboardInterrupt:
            log.info("Watcher stopped by user.")
            break
        except Exception as e:
            log.error(f"Unexpected error in main loop: {e}")

        time.sleep(SCAN_INTERVAL)

if __name__ == "__main__":
    main()
