#!/usr/bin/env python3
"""
🧠 SaleH SaaS - Knowledge Watcher Service
يراقب مجلد knowledge_inbox ويرسل الملفات الجديدة لـ n8n عبر Webhook
"""

import os
import time
import logging
import requests
import hashlib
import json
from pathlib import Path

# إعداد اللوج
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
log = logging.getLogger("KnowledgeWatcher")

# الإعدادات
INBOX_DIR = Path(os.getenv("INBOX_DIR", "/knowledge_inbox"))
PROCESSED_DIR = Path(os.getenv("PROCESSED_DIR", "/knowledge_processed"))
FAILED_DIR = Path(os.getenv("FAILED_DIR", "/knowledge_failed"))
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "http://n8n:5678/webhook/knowledge-ingest")
TIKA_URL = os.getenv("TIKA_URL", "http://tika:9998/tika")
CHROMADB_URL = os.getenv("CHROMADB_URL", "http://chromadb:8000")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text:latest")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "saleh_legal_knowledge")
SCAN_INTERVAL = int(os.getenv("SCAN_INTERVAL", "10"))  # ثوانٍ

# أنواع الملفات المدعومة
SUPPORTED_EXTENSIONS = {
    '.pdf', '.docx', '.doc', '.txt', '.xlsx', '.xls',
    '.pptx', '.ppt', '.md', '.rtf', '.odt', '.csv'
}

def ensure_dirs():
    """إنشاء المجلدات إذا لم تكن موجودة"""
    for d in [INBOX_DIR, PROCESSED_DIR, FAILED_DIR]:
        d.mkdir(parents=True, exist_ok=True)

def get_file_hash(file_path: Path) -> str:
    """حساب hash للملف لتجنب المعالجة المكررة"""
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
    """توليد embedding عبر Ollama"""
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/embeddings",
            json={"model": EMBED_MODEL, "prompt": text},
            timeout=60
        )
        if response.status_code == 200:
            return response.json().get("embedding", [])
        return []
    except Exception as e:
        log.error(f"Ollama embedding error: {e}")
        return []

def ensure_collection():
    """التأكد من وجود collection في ChromaDB"""
    try:
        # التحقق من وجود الـ collection
        r = requests.get(f"{CHROMADB_URL}/api/v1/collections/{COLLECTION_NAME}", timeout=10)
        if r.status_code == 404:
            # إنشاء collection جديد
            requests.post(
                f"{CHROMADB_URL}/api/v1/collections",
                json={
                    "name": COLLECTION_NAME,
                    "metadata": {"description": "SaleH Legal Knowledge Base"}
                },
                timeout=10
            )
            log.info(f"✅ تم إنشاء collection: {COLLECTION_NAME}")
    except Exception as e:
        log.warning(f"ChromaDB collection check: {e}")

def save_to_chromadb(chunks: list, metadata_base: dict) -> int:
    """حفظ الـ chunks في ChromaDB"""
    saved = 0
    
    for i, chunk in enumerate(chunks):
        embedding = get_embedding(chunk)
        if not embedding:
            log.warning(f"  ⚠️ فشل embedding للـ chunk {i}")
            continue
        
        doc_id = f"{metadata_base['source']}_{i}_{int(time.time())}"
        metadata = {**metadata_base, "chunk_index": i}
        
        try:
            response = requests.post(
                f"{CHROMADB_URL}/api/v1/collections/{COLLECTION_NAME}/add",
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
                log.error(f"  ❌ ChromaDB error: {response.status_code} - {response.text[:100]}")
        except Exception as e:
            log.error(f"  ❌ ChromaDB save error: {e}")
    
    return saved

def process_file(file_path: Path):
    """معالجة ملف واحد"""
    log.info(f"📄 معالجة: {file_path.name}")
    
    # استخراج النص
    log.info(f"  🔍 استخراج النص عبر Tika...")
    text = extract_text_tika(file_path)
    
    if not text or len(text.strip()) < 50:
        log.warning(f"  ⚠️ النص قصير جداً أو فارغ - تخطي")
        # نقل للفاشلة
        dest = FAILED_DIR / file_path.name
        file_path.rename(dest)
        return False
    
    log.info(f"  ✅ تم استخراج {len(text)} حرف")
    
    # تقسيم إلى chunks
    chunks = chunk_text(text)
    log.info(f"  ✂️ {len(chunks)} chunk")
    
    if not chunks:
        log.warning(f"  ⚠️ لا chunks - تخطي")
        dest = FAILED_DIR / file_path.name
        file_path.rename(dest)
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
    dest = PROCESSED_DIR / file_path.name
    if dest.exists():
        dest = PROCESSED_DIR / f"{file_path.stem}_{int(time.time())}{file_path.suffix}"
    file_path.rename(dest)
    
    log.info(f"  📦 نُقل إلى: {dest.name}")
    return True

def scan_inbox():
    """مسح مجلد الـ inbox"""
    files = [
        f for f in INBOX_DIR.iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
    ]
    return files

def main():
    log.info("🚀 SaleH SaaS Knowledge Watcher - بدء التشغيل")
    log.info(f"📂 مجلد المراقبة: {INBOX_DIR}")
    log.info(f"✅ مجلد المعالجة: {PROCESSED_DIR}")
    log.info(f"🔄 فترة المسح: {SCAN_INTERVAL} ثانية")
    
    ensure_dirs()
    
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
                        # نقل للفاشلة
                        try:
                            dest = FAILED_DIR / file_path.name
                            file_path.rename(dest)
                        except:
                            pass
            
        except Exception as e:
            log.error(f"❌ خطأ في المسح: {e}")
        
        time.sleep(SCAN_INTERVAL)

if __name__ == "__main__":
    main()
