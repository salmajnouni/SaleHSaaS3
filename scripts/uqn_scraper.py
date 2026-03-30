#!/usr/bin/env python3
"""
أم القرى - سكريبت سحب وأرشفة الأنظمة واللوائح السعودية
Umm Al-Qura Gazette Scraper & Archiver

يسحب الأنظمة واللوائح والقرارات من جريدة أم القرى الرسمية
ويدخلها تلقائياً في ChromaDB عبر pipeline الموجود

المصادر:
  - لوائح وأنظمة: https://www.uqn.gov.sa/decisions/rules-and-regulations
  - قرارات مجلس الوزراء: https://www.uqn.gov.sa/decisions/council-of-ministers-decisions
  - مراسيم ملكية: https://www.uqn.gov.sa/decisions/royal-decrees
  - أوامر ملكية: https://www.uqn.gov.sa/decisions/royal-orders
  - قرارات وزارية: https://www.uqn.gov.sa/decisions/ministerial-decisions

الاستخدام:
  python scripts/uqn_scraper.py                    # سحب الجديد فقط
  python scripts/uqn_scraper.py --full             # سحب كل شيء (أول مرة)
  python scripts/uqn_scraper.py --pages 5          # سحب أول 5 صفحات فقط
  python scripts/uqn_scraper.py --category rules   # لوائح وأنظمة فقط
  python scripts/uqn_scraper.py --report           # تقرير بدون سحب
  python scripts/uqn_scraper.py --dry-run          # معاينة بدون إدخال
"""

import requests
import re
import json
import time
import hashlib
import logging
import argparse
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from html import unescape


def _configure_stdio_utf8():
    """Keep Arabic output readable when redirected/piped on Windows."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass


_configure_stdio_utf8()

# === Configuration ===
UQN_BASE = "https://www.uqn.gov.sa"
CHROMADB_URL = os.getenv("CHROMADB_URL", "http://localhost:8010")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
COLLECTION_NAME = os.getenv("CHROMA_COLLECTION", "saleh_knowledge")
EMBED_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text:latest")
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150
REQUEST_DELAY = 2  # seconds between requests (be polite)

# Archive directory
PROJECT_DIR = Path(__file__).resolve().parent.parent
ARCHIVE_DIR = PROJECT_DIR / "knowledge_archive" / "uqn"
STATE_FILE = PROJECT_DIR / "data" / "uqn_scraper_state.json"

# Categories to scrape
CATEGORIES = {
    "rules": {
        "name": "لوائح وأنظمة",
        "path": "/decisions/rules-and-regulations",
        "detail_path": "/decisions-and-regulations/rules-and-regulations",
        "type": "regulation"
    },
    "cabinet": {
        "name": "قرارات مجلس الوزراء",
        "path": "/decisions/council-of-ministers-decisions",
        "detail_path": "/decisions-and-regulations/council-of-ministers-decisions",
        "type": "cabinet_decision"
    },
    "royal_decrees": {
        "name": "مراسيم ملكية",
        "path": "/decisions/royal-decrees",
        "detail_path": "/decisions-and-regulations/royal-decrees",
        "type": "royal_decree"
    },
    "royal_orders": {
        "name": "أوامر ملكية",
        "path": "/decisions/royal-orders",
        "detail_path": "/decisions-and-regulations/royal-orders",
        "type": "royal_order"
    },
    "ministerial": {
        "name": "قرارات وزارية",
        "path": "/decisions/ministerial-decisions",
        "detail_path": "/decisions-and-regulations/ministerial-decisions",
        "type": "ministerial_decision"
    },
}

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout,
)
log = logging.getLogger("uqn_scraper")


# =====================================================================
# State Management - tracks what we already scraped
# =====================================================================
class ScraperState:
    def __init__(self):
        self.state_file = STATE_FILE
        self.state = self._load()

    def _load(self):
        if self.state_file.exists():
            with open(self.state_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {
            "last_run": None,
            "scraped_ids": {},  # {uqn_id: {title, date, category, hash}}
            "stats": {"total_scraped": 0, "total_ingested": 0},
        }

    def save(self):
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(self.state, f, ensure_ascii=False, indent=2)

    def is_scraped(self, uqn_id, content_hash=None):
        entry = self.state["scraped_ids"].get(str(uqn_id))
        if not entry:
            return False
        if content_hash and entry.get("hash") != content_hash:
            return False  # Content changed, re-scrape
        return True

    def mark_scraped(self, uqn_id, title, date_str, category, content_hash):
        self.state["scraped_ids"][str(uqn_id)] = {
            "title": title,
            "date": date_str,
            "category": category,
            "hash": content_hash,
            "scraped_at": datetime.now().isoformat(),
        }
        self.state["stats"]["total_scraped"] += 1
        self.state["last_run"] = datetime.now().isoformat()


# =====================================================================
# HTML Parsing (lightweight, no BS4 dependency needed)
# =====================================================================
def strip_html(html_text):
    """Remove HTML tags and clean text."""
    text = re.sub(r"<script[^>]*>.*?</script>", "", html_text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</p>", "\n\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</div>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    text = unescape(text)
    # Clean whitespace
    lines = [line.strip() for line in text.splitlines()]
    text = "\n".join(line for line in lines if line)
    # Remove excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_listing_items(html, category_key):
    """Extract regulation items from a listing page."""
    items = []
    seen = set()

    # UQN uses two link formats:
    # 1. Full: href="https://www.uqn.gov.sa/decisions-and-regulations/rules-and-regulations/4000592"
    # 2. Short: href="https://www.uqn.gov.sa/decisions-and-regulations/4000576"
    # Both have title="النظام..." attribute

    # Pattern: <a href="...decisions-and-regulations.../DIGITS" title="TITLE">
    # Capture the full path to preserve category subpath
    pattern = re.compile(
        r'<a[^>]*href="(?:https?://www\.uqn\.gov\.sa)?(/decisions-and-regulations/(?:[^/"]+/)?(\d+))"'
        r'[^>]*title="([^"]+)"',
        re.IGNORECASE,
    )

    for m in pattern.finditer(html):
        full_path = m.group(1)
        uqn_id = m.group(2)
        title = unescape(m.group(3)).strip()
        if uqn_id not in seen and title and len(title) > 3:
            seen.add(uqn_id)
            items.append({
                "uqn_id": uqn_id,
                "title": title,
                "url": f"{UQN_BASE}{full_path}",
                "category": category_key,
            })

    # Fallback: links without title attribute but with text content
    if not items:
        pattern2 = re.compile(
            r'<a[^>]*href="(?:https?://www\.uqn\.gov\.sa)?(/decisions-and-regulations/(?:[^/"]+/)?(\d+))"[^>]*>'
            r'([\s\S]*?)</a>',
            re.IGNORECASE,
        )
        for m in pattern2.finditer(html):
            full_path = m.group(1)
            uqn_id = m.group(2)
            title_text = strip_html(m.group(3)).strip()
            if uqn_id not in seen and title_text and len(title_text) > 5 and "no image" not in title_text:
                seen.add(uqn_id)
                items.append({
                    "uqn_id": uqn_id,
                    "title": title_text,
                    "url": f"{UQN_BASE}{full_path}",
                    "category": category_key,
                })

    return items


def extract_regulation_content(html, title):
    """Extract the main law/regulation text from a detail page."""
    # Try to find the main content area
    # UQN pages have the law text in the main content div
    
    # Strategy 1: Find content between article markers
    # المادة الأولى ... end
    article_match = re.search(
        r"(المادة\s+الأولى[\s\S]*?)(?:<footer|<div[^>]*class=\"[^\"]*footer|<!-- footer|$)",
        html,
        re.IGNORECASE,
    )
    
    if article_match:
        raw = article_match.group(1)
        text = strip_html(raw)
        if len(text) > 200:
            return text

    # Strategy 2: Look for the content container
    content_match = re.search(
        r'<div[^>]*class="[^"]*(?:content-body|article-content|law-content|details-content)[^"]*"[^>]*>([\s\S]*?)</div>',
        html,
        re.IGNORECASE,
    )
    if content_match:
        text = strip_html(content_match.group(1))
        if len(text) > 200:
            return text

    # Strategy 3: Take the largest text block after the title
    title_pos = html.find(title[:30]) if title else 0
    if title_pos > 0:
        remainder = html[title_pos:]
        text = strip_html(remainder)
        # Remove navigation/footer content
        for marker in ["الأكثر قراءة", "جميع الحقوق محفوظة", "تابعنا على", "اتصل بنا"]:
            idx = text.find(marker)
            if idx > 200:
                text = text[:idx]
                break
        if len(text) > 200:
            return text.strip()

    # Strategy 4: Full page strip
    text = strip_html(html)
    for marker in ["الأكثر قراءة", "جميع الحقوق محفوظة", "تابعنا على"]:
        idx = text.find(marker)
        if idx > 200:
            text = text[:idx]
            break
    return text.strip()


def extract_date(html):
    """Extract publication date from the page."""
    # Pattern: 1447-9-24 الموافق 13-03-2026
    m = re.search(r"(\d{4}-\d{1,2}-\d{1,2})\s*الموافق\s*(\d{2}-\d{2}-\d{4})", html)
    if m:
        return m.group(2)  # Gregorian date
    
    m = re.search(r"الموافق\s*(\d{2}-\d{2}-\d{4})", html)
    if m:
        return m.group(1)
    
    return None


# =====================================================================
# Text Chunking (Arabic-aware)
# =====================================================================
def chunk_text(text, title="", chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """Split text into chunks, respecting Arabic article boundaries."""
    if not text or len(text) < 100:
        return []

    chunks = []
    # Try to split at article boundaries first
    article_pattern = re.compile(r"(?=المادة\s+(?:الأولى|الثانية|الثالثة|الرابعة|الخامسة|السادسة|السابعة|الثامنة|التاسعة|العاشرة|الحادية|الثانية|[\u0660-\u0669\d]+)\s*[:\-–]?)")
    article_splits = article_pattern.split(text)
    
    if len(article_splits) > 3:
        # Good article structure, chunk by articles
        current_chunk = ""
        for part in article_splits:
            part = part.strip()
            if not part:
                continue
            if len(current_chunk) + len(part) < chunk_size:
                current_chunk += "\n\n" + part if current_chunk else part
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = part
        if current_chunk:
            chunks.append(current_chunk.strip())
    else:
        # Fall back to paragraph-based chunking
        paragraphs = text.split("\n\n")
        current_chunk = ""
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            if len(current_chunk) + len(para) + 2 <= chunk_size:
                current_chunk += "\n\n" + para if current_chunk else para
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                # Handle paragraphs longer than chunk_size
                if len(para) > chunk_size:
                    for i in range(0, len(para), chunk_size - overlap):
                        chunks.append(para[i : i + chunk_size].strip())
                    current_chunk = ""
                else:
                    current_chunk = para
        if current_chunk:
            chunks.append(current_chunk.strip())

    # Add title prefix to first chunk
    if chunks and title:
        chunks[0] = f"{title}\n\n{chunks[0]}"

    return [c for c in chunks if len(c) > 50]


# =====================================================================
# ChromaDB Integration
# =====================================================================
def get_collection_id():
    """Get the saleh_knowledge collection ID."""
    try:
        r = requests.get(f"{CHROMADB_URL}/api/v1/collections", timeout=10)
        r.raise_for_status()
        for col in r.json():
            if col["name"] == COLLECTION_NAME:
                return col["id"]
    except Exception as e:
        log.error(f"Cannot reach ChromaDB: {e}")
    return None


def get_existing_uqn_ids(collection_id):
    """Check which UQN IDs are already in ChromaDB."""
    try:
        total = requests.get(
            f"{CHROMADB_URL}/api/v1/collections/{collection_id}/count", timeout=10
        ).json()
        if total == 0:
            return set()

        r = requests.post(
            f"{CHROMADB_URL}/api/v1/collections/{collection_id}/get",
            json={"include": ["metadatas"], "limit": total},
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()
        
        existing = set()
        for meta in data.get("metadatas", []):
            if meta.get("source") == "uqn.gov.sa":
                uqn_id = meta.get("uqn_id", "")
                if uqn_id:
                    existing.add(str(uqn_id))
        return existing
    except Exception as e:
        log.error(f"Error querying ChromaDB: {e}")
        return set()


def generate_embedding(text):
    """Generate embedding via Ollama."""
    try:
        r = requests.post(
            f"{OLLAMA_URL}/api/embeddings",
            json={"model": EMBED_MODEL, "prompt": text[:8000]},
            timeout=30,
        )
        r.raise_for_status()
        return r.json().get("embedding")
    except Exception as e:
        log.error(f"Embedding error: {e}")
        return None


def upsert_to_chromadb(collection_id, chunks, metadata_base):
    """Insert chunks into ChromaDB."""
    ids = []
    embeddings = []
    documents = []
    metadatas = []

    for i, chunk in enumerate(chunks):
        chunk_id = f"uqn_{metadata_base['uqn_id']}_{i}"
        emb = generate_embedding(chunk)
        if not emb:
            continue
        
        ids.append(chunk_id)
        embeddings.append(emb)
        documents.append(chunk)
        metadatas.append({
            **metadata_base,
            "chunk_index": i,
            "total_chunks": len(chunks),
        })

    if not ids:
        return 0

    try:
        r = requests.post(
            f"{CHROMADB_URL}/api/v1/collections/{collection_id}/upsert",
            json={
                "ids": ids,
                "embeddings": embeddings,
                "documents": documents,
                "metadatas": metadatas,
            },
            timeout=60,
        )
        r.raise_for_status()
        return len(ids)
    except Exception as e:
        log.error(f"ChromaDB upsert error: {e}")
        return 0


# =====================================================================
# Archive (local file backup)
# =====================================================================
def archive_document(uqn_id, title, content, category, date_str):
    """Save document locally for backup."""
    cat_dir = ARCHIVE_DIR / category
    cat_dir.mkdir(parents=True, exist_ok=True)
    
    safe_title = re.sub(r'[\\/:*?"<>|]', '_', title)[:80]
    filename = f"{uqn_id}_{safe_title}.txt"
    filepath = cat_dir / filename

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"العنوان: {title}\n")
        f.write(f"المعرّف: {uqn_id}\n")
        f.write(f"التصنيف: {CATEGORIES.get(category, {}).get('name', category)}\n")
        f.write(f"تاريخ النشر: {date_str or 'غير محدد'}\n")
        f.write(f"المصدر: جريدة أم القرى - uqn.gov.sa\n")
        f.write(f"تاريخ السحب: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write("=" * 60 + "\n\n")
        f.write(content)

    return filepath


# =====================================================================
# Main Scraping Logic
# =====================================================================
def fetch_page(url):
    """Fetch a page with rate limiting and retries."""
    headers = {
        "User-Agent": "SaleHSaaS-LegalBot/1.0 (Internal Knowledge System)",
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "ar,en;q=0.5",
    }
    for attempt in range(3):
        try:
            r = requests.get(url, headers=headers, timeout=30)
            r.raise_for_status()
            r.encoding = "utf-8"
            time.sleep(REQUEST_DELAY)
            return r.text
        except requests.RequestException as e:
            log.warning(f"  Attempt {attempt+1}/3 failed for {url}: {e}")
            time.sleep(5 * (attempt + 1))
    return None


def scrape_category(category_key, max_pages=None, state=None, dry_run=False, 
                    collection_id=None, existing_ids=None):
    """Scrape all items from a category."""
    cat = CATEGORIES[category_key]
    log.info(f"\n{'='*60}")
    log.info(f"📂 {cat['name']} ({category_key})")
    log.info(f"{'='*60}")

    page = 1
    total_found = 0
    total_new = 0
    total_ingested = 0

    while True:
        if max_pages and page > max_pages:
            break

        url = f"{UQN_BASE}{cat['path']}?pgno={page}"
        log.info(f"  📄 صفحة {page}: {url}")
        
        html = fetch_page(url)
        if not html:
            log.error(f"  ❌ فشل تحميل الصفحة {page}")
            break

        items = extract_listing_items(html, category_key)
        if not items:
            log.info(f"  ✅ انتهت الصفحات (لا توجد عناصر في صفحة {page})")
            break

        total_found += len(items)
        log.info(f"  📋 وجدنا {len(items)} عنصر")

        for item in items:
            uqn_id = item["uqn_id"]
            
            # Skip if already scraped (check state + ChromaDB)
            if state and state.is_scraped(uqn_id):
                continue
            if existing_ids and uqn_id in existing_ids:
                continue

            total_new += 1
            log.info(f"    🆕 [{uqn_id}] {item['title'][:60]}...")

            if dry_run:
                continue

            # Fetch detail page
            detail_html = fetch_page(item["url"])
            if not detail_html:
                log.warning(f"    ❌ فشل تحميل التفاصيل")
                continue

            # Extract content
            content = extract_regulation_content(detail_html, item["title"])
            pub_date = extract_date(detail_html)
            
            if len(content) < 100:
                log.warning(f"    ⚠️ محتوى قصير جداً ({len(content)} حرف) - تخطي")
                continue

            content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
            log.info(f"    📝 {len(content)} حرف | تاريخ: {pub_date or '?'}")

            # Archive locally
            archive_document(uqn_id, item["title"], content, category_key, pub_date)

            # Chunk and ingest into ChromaDB
            if collection_id:
                chunks = chunk_text(content, title=item["title"])
                if chunks:
                    metadata = {
                        "law_name": item["title"],
                        "uqn_id": uqn_id,
                        "category": cat["type"],
                        "source": "uqn.gov.sa",
                        "source_url": item["url"],
                        "publication_date": pub_date or "",
                        "content_hash": content_hash,
                    }
                    inserted = upsert_to_chromadb(collection_id, chunks, metadata)
                    total_ingested += inserted
                    log.info(f"    ✅ أُدخل {inserted} chunk في ChromaDB")

            # Update state
            if state:
                state.mark_scraped(uqn_id, item["title"], pub_date or "", category_key, content_hash)
                state.save()

        page += 1

    return {
        "category": category_key,
        "found": total_found,
        "new": total_new,
        "ingested": total_ingested,
    }


# =====================================================================
# Report
# =====================================================================
def generate_report(state):
    """Generate a status report."""
    print("\n" + "=" * 60)
    print("  📊 تقرير أم القرى - UQN Scraper Report")
    print("=" * 60)
    
    last_run = state.state.get("last_run", "لم يعمل بعد")
    print(f"  آخر تشغيل: {last_run}")
    print(f"  إجمالي المسحوبات: {state.state['stats']['total_scraped']}")
    
    # Group by category
    by_cat = {}
    for uid, info in state.state["scraped_ids"].items():
        cat = info.get("category", "unknown")
        by_cat.setdefault(cat, []).append(info)
    
    print(f"\n  --- حسب التصنيف ---")
    for cat_key, items in sorted(by_cat.items(), key=lambda x: -len(x[1])):
        cat_name = CATEGORIES.get(cat_key, {}).get("name", cat_key)
        print(f"  [{len(items):4d}] {cat_name}")
    
    # Check ChromaDB
    col_id = get_collection_id()
    if col_id:
        total = requests.get(f"{CHROMADB_URL}/api/v1/collections/{col_id}/count", timeout=10).json()
        uqn_ids = get_existing_uqn_ids(col_id)
        print(f"\n  --- ChromaDB ---")
        print(f"  إجمالي chunks في القاعدة: {total}")
        print(f"  منها من أم القرى: ~{len(uqn_ids)} وثيقة")
    
    print("=" * 60)


# =====================================================================
# Entry Point
# =====================================================================
def main():
    parser = argparse.ArgumentParser(description="أم القرى - سحب وأرشفة الأنظمة السعودية")
    parser.add_argument("--full", action="store_true", help="سحب كامل (كل الصفحات)")
    parser.add_argument("--pages", type=int, default=3, help="عدد الصفحات لكل تصنيف (افتراضي: 3)")
    parser.add_argument("--category", choices=list(CATEGORIES.keys()), help="تصنيف محدد فقط")
    parser.add_argument("--report", action="store_true", help="عرض تقرير فقط")
    parser.add_argument("--dry-run", action="store_true", help="معاينة بدون إدخال")
    parser.add_argument("--no-chromadb", action="store_true", help="أرشفة محلية فقط بدون ChromaDB")
    args = parser.parse_args()

    state = ScraperState()

    if args.report:
        generate_report(state)
        return

    max_pages = None if args.full else args.pages
    categories = [args.category] if args.category else list(CATEGORIES.keys())

    log.info("🏛️  أم القرى - بدء السحب والأرشفة")
    log.info(f"   التصنيفات: {', '.join(categories)}")
    log.info(f"   الصفحات: {'الكل' if args.full else max_pages}")
    log.info(f"   الوضع: {'معاينة' if args.dry_run else 'تشغيل كامل'}")

    # Connect to ChromaDB
    collection_id = None
    existing_ids = set()
    if not args.no_chromadb and not args.dry_run:
        collection_id = get_collection_id()
        if collection_id:
            existing_ids = get_existing_uqn_ids(collection_id)
            log.info(f"   ChromaDB: متصل ✅ ({len(existing_ids)} وثيقة أم القرى موجودة)")
        else:
            log.warning("   ChromaDB: غير متاح ⚠️ - أرشفة محلية فقط")

    # Scrape
    results = []
    for cat_key in categories:
        result = scrape_category(
            cat_key,
            max_pages=max_pages,
            state=state,
            dry_run=args.dry_run,
            collection_id=collection_id,
            existing_ids=existing_ids,
        )
        results.append(result)

    # Summary
    log.info("\n" + "=" * 60)
    log.info("📊 ملخص التشغيل")
    log.info("=" * 60)
    total_new = 0
    total_ingested = 0
    for r in results:
        cat_name = CATEGORIES[r["category"]]["name"]
        log.info(f"  {cat_name}: وُجد {r['found']} | جديد {r['new']} | أُدخل {r['ingested']}")
        total_new += r["new"]
        total_ingested += r["ingested"]
    
    log.info(f"\n  الإجمالي: {total_new} جديد | {total_ingested} chunk أُدخل")
    if args.dry_run:
        log.info("  ⚠️ وضع المعاينة - لم يتم إدخال أي شيء فعلياً")
    log.info("=" * 60)

    state.save()


if __name__ == "__main__":
    main()
