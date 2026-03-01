#!/usr/bin/env python3
"""
🧠 SaleH SaaS - Knowledge Watcher Service
يراقب مجلد knowledge_inbox ويحفظ الملفات الجديدة في ChromaDB تلقائياً
"""

import os
import time
import logging
import requests
import hashlib
import shutil
from pathlib import Path

# إعداد اللوج
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
log = logging.getLogger("KnowledgeWatcher")

# الإعدادات
INBOX_DIR      = Path(os.getenv("INBOX_DIR",      "/knowledge_inbox"))
PROCESSED_DIR  = Path(os.getenv("PROCESSED_DIR",  "/knowledge_processed"))
FAILED_DIR     = Path(os.getenv("FAILED_DIR",     "/knowledge_failed"))
TIKA_URL       = os.getenv("TIKA_URL",            "http://tika:9998/tika")
CHROMADB_URL   = os.getenv("CHROMADB_URL",        "http://chromadb:8000")
OLLAMA_URL     = os.getenv("OLLAMA_URL",          "http://host.docker.internal:11434")
EMBED_MODEL    = os.getenv("EMBED_MODEL",         "nomic-embed-text:latest")
COLLECTION_NAME = os.getenv("COLLECTION_NAME",   "saleh_legal_knowledge")
SCAN_INTERVAL  = int(os.getenv("SCAN_INTERVAL",   "10"))

# أنواع الملفات المدعومة (بدون .md لتجنب معالجة README)
SUPPORTED_EXTENSIONS = {
    '.pdf', '.docx', '.doc', '.txt', '.xlsx', '.xls',
    '.pptx', '.ppt', '.rtf', '.odt', '.csv'
}

# ─────────────────────────────────────────────────────────────────────────────

def ensure_dirs():
    """إنشاء المجلدات إذا لم تكن موجودة"""
    for d in [INBOX_DIR, PROCESSED_DIR, FAILED_DIR]:
        d.mkdir(parents=True, exist_ok=True)

def get_file_hash(file_path: Path) -> str:
    """حساب hash للملف"""
    h = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()

def extract_text_tika(file_path: Path) -> str:
    """استخراج النص من الملف عبر Tika"""
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
    """تقسيم النص إلى chunks"""
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
    """توليد embedding عبر Ollama - مع مهلة 5 دقائق"""
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/embeddings",
            json={"model": EMBED_MODEL, "prompt": text},
            timeout=300
        )
        if response.status_code == 200:
            return response.json().get("embedding", [])
        log.warning(f"  Ollama returned {response.status_code}")
        return []
    except Exception as e:
        log.error(f"Ollama embedding error: {e}")
        return []

def detect_chromadb_api_version() -> str:
    """اكتشاف إصدار ChromaDB API تلقائياً"""
    for version in ["v2", "v1"]:
        try:
            r = requests.get(f"{CHROMADB_URL}/api/{version}/collections", timeout=5)
            if r.status_code in [200, 401, 403]:
                log.info(f"  ✅ ChromaDB API version: {version}")
                return version
        except Exception:
            pass
    return "v1"

# نكتشف الإصدار مرة واحدة عند البدء
CHROMA_API_VERSION = None

def get_chroma_api():
    global CHROMA_API_VERSION
    if CHROMA_API_VERSION is None:
        CHROMA_API_VERSION = detect_chromadb_api_version()
    return CHROMA_API_VERSION

def ensure_collection():
    """التأكد من وجود collection في ChromaDB"""
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
                log.info(f"✅ تم إنشاء collection: {COLLECTION_NAME}")
            else:
                log.warning(f"Collection create: {resp.status_code} - {resp.text[:100]}")
        elif r.status_code == 200:
            log.info(f"✅ Collection موجود: {COLLECTION_NAME}")
    except Exception as e:
        log.warning(f"ChromaDB collection check error: {e}")

def save_to_chromadb(chunks: list, metadata_base: dict) -> int:
    """حفظ الـ chunks في ChromaDB"""
    api = get_chroma_api()
    saved = 0

    for i, chunk in enumerate(chunks):
        embedding = get_embedding(chunk)
        if not embedding:
            log.warning(f"  ⚠️ فشل embedding للـ chunk {i} - سيُحفظ بدون embedding")
            # حفظ بدون embedding كـ fallback
            doc_id = f"{metadata_base['source']}_{i}_{int(time.time())}"
            metadata = {**metadata_base, "chunk_index": i, "has_embedding": False}
            try:
                response = requests.post(
                    f"{CHROMADB_URL}/api/{api}/collections/{COLLECTION_NAME}/add",
                    json={
                        "ids": [doc_id],
                        "documents": [chunk],
                        "metadatas": [metadata]
                    },
                    timeout=30
                )
                if response.status_code in [200, 201]:
                    saved += 1
                    log.info(f"  💾 chunk {i} حُفظ بدون embedding")
                else:
                    log.error(f"  ❌ ChromaDB error: {response.status_code} - {response.text[:150]}")
            except Exception as e:
                log.error(f"  ❌ ChromaDB save error: {e}")
            continue

        doc_id = f"{metadata_base['source']}_{i}_{int(time.time())}"
        metadata = {**metadata_base, "chunk_index": i, "has_embedding": True}

        try:
            response = requests.post(
                f"{CHROMADB_URL}/api/{api}/collections/{COLLECTION_NAME}/add",
                json={
                    "ids": [doc_id],
                    "embeddings": [embedding],
                    "documents": [chunk],
                    "metadatas": [metadata]
                },
                timeout=30
            )
            if response.status_code in [200, 201]:
                saved += 1
            else:
                log.error(f"  ❌ ChromaDB error: {response.status_code} - {response.text[:150]}")
        except Exception as e:
            log.error(f"  ❌ ChromaDB save error: {e}")

    return saved

def move_file_safe(src: Path, dest_dir: Path):
    """نقل الملف بأمان مع معالجة التعارضات"""
    dest = dest_dir / src.name
    if dest.exists():
        dest = dest_dir / f"{src.stem}_{int(time.time())}{src.suffix}"
    try:
        shutil.copy2(str(src), str(dest))
        src.unlink()
        log.info(f"  📦 نُقل إلى: {dest_dir.name}/{dest.name}")
    except PermissionError:
        log.warning(f"  ⚠️ لا يمكن نقل {src.name} (ملف محمي) - سيُتجاهل")
    except Exception as e:
        log.error(f"  ❌ خطأ في النقل: {e}")

def process_file(file_path: Path):
    """معالجة ملف واحد"""
    log.info(f"📄 معالجة: {file_path.name}")

    # استخراج النص
    log.info(f"  🔍 استخراج النص عبر Tika...")
    text = extract_text_tika(file_path)

    if not text or len(text.strip()) < 50:
        log.warning(f"  ⚠️ النص قصير جداً أو فارغ - نقل للفاشلة")
        move_file_safe(file_path, FAILED_DIR)
        return False

    log.info(f"  ✅ تم استخراج {len(text)} حرف")

    # تقسيم إلى chunks
    chunks = chunk_text(text)
    log.info(f"  ✂️ {len(chunks)} chunk")

    if not chunks:
        log.warning(f"  ⚠️ لا chunks - نقل للفاشلة")
        move_file_safe(file_path, FAILED_DIR)
        return False

    # التأكد من وجود الـ collection
    ensure_collection()

    # حفظ في ChromaDB
    metadata = {
        "source": file_path.name,
        "file_type": file_path.suffix.lower(),
        "file_hash": get_file_hash(file_path),
        "ingested_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }

    log.info(f"  💾 حفظ في ChromaDB...")
    saved = save_to_chromadb(chunks, metadata)
    log.info(f"  ✅ تم حفظ {saved}/{len(chunks)} chunk")

    # نقل للمعالجة
    move_file_safe(file_path, PROCESSED_DIR)
    return True

def scan_inbox():
    """مسح مجلد الـ inbox - يتجاهل README وملفات النظام"""
    files = [
        f for f in INBOX_DIR.iterdir()
        if f.is_file()
        and f.suffix.lower() in SUPPORTED_EXTENSIONS
        and not f.name.startswith('.')
        and f.name.upper() not in ('README.MD', 'README.TXT', 'README')
    ]
    return files

def main():
    log.info("🚀 SaleH SaaS Knowledge Watcher - بدء التشغيل")
    log.info(f"📂 مجلد المراقبة: {INBOX_DIR}")
    log.info(f"✅ مجلد المعالجة: {PROCESSED_DIR}")
    log.info(f"❌ مجلد الفاشلة: {FAILED_DIR}")
    log.info(f"🔄 فترة المسح: {SCAN_INTERVAL} ثانية")
    log.info(f"🤖 نموذج الـ Embedding: {EMBED_MODEL}")

    ensure_dirs()

    # اكتشاف إصدار ChromaDB
    api = get_chroma_api()
    log.info(f"🗄️ ChromaDB API: /api/{api}/")

    while True:
        try:
            files = scan_inbox()

            if files:
                log.info(f"📥 وجدت {len(files)} ملف جديد")
                for file_path in files:
                    try:
                        process_file(file_path)
                    except Exception as e:
                        log.error(f"❌ خطأ في معالجة {file_path.name}: {e}")
                        try:
                            move_file_safe(file_path, FAILED_DIR)
                        except Exception:
                            pass

        except Exception as e:
            log.error(f"❌ خطأ في المسح: {e}")

        time.sleep(SCAN_INTERVAL)

if __name__ == "__main__":
    main()
