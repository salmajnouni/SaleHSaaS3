#!/usr/bin/env python3
"""
auto_update_laws.py - نظام التحديث الذاتي للقوانين السعودية
=============================================================
يكتشف القوانين من هيئة الخبراء، يقارن بالموجود في ChromaDB،
ويسحب الناقص تلقائياً.

الاستخدام:
  python auto_update_laws.py                  # سحب الناقص فقط
  python auto_update_laws.py --discover       # اكتشاف قوانين جديدة من الموقع
  python auto_update_laws.py --force          # إعادة سحب الكل
  python auto_update_laws.py --dry-run        # عرض الناقص بدون سحب
  python auto_update_laws.py --report         # تقرير عن الحالة الحالية
"""
import requests
import re
import json
import time
import sys
import os
import logging
from pathlib import Path
from datetime import datetime
from collections import Counter
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def _configure_stdio_utf8():
    """Keep Arabic output readable when redirected/piped on Windows."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass


_configure_stdio_utf8()

# === Configuration ===
CHROMADB_URL = os.environ.get("CHROMADB_URL", "http://localhost:8010")
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
COLLECTION_NAME = os.environ.get("CHROMA_COLLECTION", "saleh_knowledge")
BOE_BASE = "https://laws.boe.gov.sa"
BOE_LAW_URL = BOE_BASE + "/BoeLaws/Laws/LawDetails/{law_id}/1"
BOE_SEARCH_URL = BOE_BASE + "/BoeLaws/Laws/Search"
CHUNK_SIZE = 800
OVERLAP = 100
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "nomic-embed-text:latest")
REQUEST_DELAY = 2  # seconds between requests to be respectful

# Logging
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "auto_update_laws.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
log = logging.getLogger("auto_update_laws")

# ====================================================================
# القائمة الشاملة للأنظمة السعودية (مع BOE IDs)
# ====================================================================
SAUDI_LAWS_REGISTRY = [
    # === الأنظمة الأساسية (verified) ===
    {"law_id": "16b97fcb-4833-4f66-8531-a9a700f161b6", "law_name": "النظام الأساسي للحكم", "category": "constitutional"},
    {"law_id": "b5cf540a-e6ac-426a-b348-a9a700f163de", "law_name": "نظام مجلس الشورى", "category": "constitutional"},
    {"law_id": "93e87aa7-f344-4711-b97c-a9a700f1662b", "law_name": "نظام مجلس الوزراء", "category": "constitutional"},
    {"law_id": "93f81644-fbbc-49ca-b33c-a9a700f16701", "law_name": "نظام المناطق", "category": "regions"},

    # === القضاء والمرافعات (corrected IDs) ===
    {"law_id": "ea1765a3-dec3-41a0-a32f-a9a700f26d58", "law_name": "نظام القضاء", "category": "judiciary"},
    {"law_id": "f0eaae46-9f84-40ee-815e-a9a700f268b3", "law_name": "نظام المرافعات الشرعية", "category": "litigation"},
    {"law_id": "9a0249b7-f835-48fa-8d1e-a9a700f1981a", "law_name": "نظام الإجراءات الجزائية", "category": "criminal_procedure"},
    {"law_id": "d7e8efd3-4021-4413-8255-ae7c00f190de", "law_name": "نظام التنفيذ", "category": "execution_law"},
    {"law_id": "2716057c-c097-4bad-8e1e-ae1400c678d5", "law_name": "نظام الإثبات", "category": "evidence_law"},
    {"law_id": "12752a60-2a4a-4cab-a05d-a9a700f274a5", "law_name": "نظام التحكيم", "category": "arbitration"},
    {"law_id": "4d72d829-947b-45d5-b9b5-ae5800d6bac2", "law_name": "نظام الأحوال الشخصية", "category": "personal_status"},

    # === العمل والتوظيف (corrected IDs) ===
    {"law_id": "08381293-6388-48e2-8ad2-a9a700f2aa94", "law_name": "نظام العمل", "category": "labor_law"},
    {"law_id": "eaee8a20-3a54-4aaf-b0d9-b1ad00998962", "law_name": "نظام التأمينات الاجتماعية", "category": "social_insurance"},
    {"law_id": "32f651e6-2976-439c-b418-a9a700f23fb2", "law_name": "نظام الخدمة المدنية", "category": "civil_service"},

    # === التجارة والشركات (corrected IDs) ===
    {"law_id": "a8376aea-1bc3-49d4-9027-aed900b555af", "law_name": "نظام الشركات", "category": "companies_law"},
    {"law_id": "98ee4b51-d398-4323-ae69-b2b8009f3156", "law_name": "نظام السجل التجاري", "category": "commercial_registry"},
    {"law_id": "4763eb94-047b-46f1-9697-a9a700f1b7ed", "law_name": "نظام الأوراق التجارية", "category": "commercial_law"},
    {"law_id": "c58ba10c-4e89-4c06-98d7-a9a700f1c706", "law_name": "نظام المحكمة التجارية", "category": "commercial_law"},
    {"law_id": "a748e485-620c-45c4-8ca8-a9f40166406d", "law_name": "نظام الإفلاس", "category": "bankruptcy"},
    {"law_id": "e3605c0d-ef87-4cff-b5da-aa3f0102bbb4", "law_name": "نظام المنافسة", "category": "competition"},

    # === المالية والضرائب (corrected IDs) ===
    {"law_id": "23576008-1ce4-4685-ac3e-a9a700f2cb02", "law_name": "نظام ضريبة الدخل", "category": "tax"},
    {"law_id": "c2c05ee1-201a-48de-91e7-a9a700f2d14f", "law_name": "نظام المنافسات والمشتريات الحكومية", "category": "procurement"},
    {"law_id": "b93d0275-775f-482a-9d52-a9a700f2ca15", "law_name": "نظام الجمارك الموحد", "category": "customs"},

    # === تقنية المعلومات والاتصالات (corrected IDs) ===
    {"law_id": "ae610645-e094-48ef-814e-aeb4009d244f", "law_name": "نظام الاتصالات وتقنية المعلومات", "category": "telecom"},
    {"law_id": "25df73d6-0f49-4dc5-b010-a9a700f2ec1d", "law_name": "نظام مكافحة جرائم المعلوماتية", "category": "cyber_crimes"},
    {"law_id": "6f509360-2c39-4358-ae2a-a9a700f2ed16", "law_name": "نظام التعاملات الإلكترونية", "category": "ecommerce"},
    {"law_id": "b7cfae89-828e-4994-b167-adaa00e37188", "law_name": "نظام حماية البيانات الشخصية", "category": "data_protection"},
    {"law_id": "360de590-0286-4fa5-a243-aa9100c31979", "law_name": "نظام التجارة الإلكترونية", "category": "ecommerce_law"},

    # === العقارات والأراضي (corrected IDs) ===
    {"law_id": "06272e6b-1fb9-4226-90b7-a9a700f21dc0", "law_name": "نظام نزع ملكية العقارات للمنفعة العامة", "category": "real_estate"},
    {"law_id": "a1bdadb5-c518-48bb-a1d0-b33000e66fd1", "law_name": "نظام تملك غير السعوديين للعقار", "category": "real_estate"},
    {"law_id": "c9756bfb-ff81-4226-a820-ae8200dc074c", "law_name": "نظام التسجيل العيني للعقار", "category": "real_estate"},

    # === الجزاءات والعقوبات (corrected IDs) ===
    {"law_id": "75e963c8-9ff3-4d10-88a4-a9a700f17f21", "law_name": "نظام مكافحة الرشوة", "category": "criminal_law"},
    {"law_id": "4a8842df-9cd1-4ee7-bf97-a9a700f180d4", "law_name": "نظام مكافحة غسل الأموال", "category": "aml_law"},

    # === المرور والنقل ===
    {"law_id": "85364e57-c01e-41ba-8def-a9a700f183e9", "law_name": "نظام المرور", "category": "traffic"},

    # === الاستثمار والاقتصاد (corrected IDs) ===
    {"law_id": "eda86cc3-3a00-4b90-900d-b1d000c8a863", "law_name": "نظام الاستثمار", "category": "investment"},
    {"law_id": "e7bd6fcc-c29c-4696-8032-aae9009b113a", "law_name": "نظام الرهن التجاري", "category": "commercial_law"},

    # === البيئة والصحة (corrected IDs) ===
    {"law_id": "63831ff6-63d9-4212-8b54-abf800e146bd", "law_name": "نظام البيئة", "category": "environment"},
    {"law_id": "64e307c5-ac8c-49d8-9174-a9a700f285a0", "law_name": "نظام المؤسسات الصحية الخاصة", "category": "health"},
    {"law_id": "f1de206c-eef4-4a76-904a-a9a700f2899a", "law_name": "نظام مزاولة المهن الصحية", "category": "health"},

    # === التعليم والملكية الفكرية (corrected IDs) ===
    {"law_id": "a6843359-3237-4553-8271-a9a700f1fcda", "law_name": "نظام مجلس التعليم العالي والجامعات", "category": "education"},
    {"law_id": "67d159e6-ee98-4efc-a2ee-a9a700f17083", "law_name": "نظام حماية حقوق المؤلف", "category": "intellectual_property"},
    {"law_id": "b2d0decd-a691-45b9-9af0-a9a700f1e86f", "law_name": "نظام العلامات التجارية", "category": "intellectual_property"},
    {"law_id": "6cfde53b-e803-49be-b2c6-a9a700f1c434", "law_name": "نظام براءات الاختراع", "category": "intellectual_property"},

    # === الإعلام والصحافة (corrected ID) ===
    {"law_id": "ecaaec43-8ff9-46b8-b269-a9a700f16e66", "law_name": "نظام المطبوعات والنشر", "category": "media"},

    # === الأمن والدفاع (corrected ID) ===
    {"law_id": "a445af93-671f-496b-818a-a9a700f19150", "law_name": "نظام الأسلحة والذخائر", "category": "security"},

    # === الأنظمة الحديثة (verified) ===
    {"law_id": "48da5c0f-b5a6-4e93-b76c-b33200be0330", "law_name": "نظام المواد البترولية والبتروكيماوية", "category": "petroleum"},
    {"law_id": "b4edc050-18f3-4b23-aabc-b35b00ddaab7", "law_name": "نظام الإحصاء", "category": "statistics"},
    {"law_id": "366a4221-3214-4338-b3f2-b35c009f36cd", "law_name": "نظام الحرف والصناعات اليدوية", "category": "crafts"},
]

# ====================================================================
# Discovered laws registry file (for auto-discovered laws from website)
# ====================================================================
REGISTRY_FILE = Path(__file__).parent / "data" / "laws_registry.json"


def load_registry():
    """Load the combined registry (hardcoded + discovered)"""
    laws = {l["law_id"]: l for l in SAUDI_LAWS_REGISTRY}
    if REGISTRY_FILE.exists():
        try:
            with open(REGISTRY_FILE, "r", encoding="utf-8") as f:
                discovered = json.load(f)
            for d in discovered:
                if d["law_id"] not in laws:
                    laws[d["law_id"]] = d
        except Exception as e:
            log.warning(f"Could not load registry: {e}")
    return list(laws.values())


def save_discovered(new_laws):
    """Save newly discovered laws to registry file"""
    existing = []
    if REGISTRY_FILE.exists():
        try:
            with open(REGISTRY_FILE, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            pass

    existing_ids = {l["law_id"] for l in existing}
    for law in new_laws:
        if law["law_id"] not in existing_ids:
            existing.append(law)

    REGISTRY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(REGISTRY_FILE, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)
    log.info(f"Registry saved: {len(existing)} discovered laws")


# ====================================================================
# ChromaDB helper functions
# ====================================================================
def get_collection_id():
    """Get or create the saleh_knowledge collection ID"""
    cols = requests.get(f"{CHROMADB_URL}/api/v1/collections", timeout=10).json()
    for c in cols:
        if c["name"] == COLLECTION_NAME:
            return c["id"]
    raise Exception(f"Collection '{COLLECTION_NAME}' not found in ChromaDB")


def get_existing_laws():
    """Get all unique law_names currently in ChromaDB"""
    cid = get_collection_id()
    total = requests.get(f"{CHROMADB_URL}/api/v1/collections/{cid}/count", timeout=10).json()

    r = requests.post(f"{CHROMADB_URL}/api/v1/collections/{cid}/get", json={
        "include": ["metadatas"],
        "limit": total
    }, timeout=30).json()

    law_counts = Counter()
    law_ids = set()
    for meta in r.get("metadatas", []):
        law_name = meta.get("law_name", "")
        law_id = meta.get("law_id", "")
        if law_name:
            law_counts[law_name] += 1
        if law_id:
            law_ids.add(law_id)

    return {"counts": law_counts, "law_ids": law_ids, "total": total}


# ====================================================================
# BOE Website scraping functions
# ====================================================================
def discover_laws_from_boe(max_pages=15):
    """Discover law IDs by crawling the BOE search pages"""
    log.info("🔍 Discovering laws from laws.boe.gov.sa...")
    discovered = []
    seen_ids = set()

    for page in range(1, max_pages + 1):
        try:
            log.info(f"  Page {page}/{max_pages}...")
            resp = requests.get(
                f"{BOE_SEARCH_URL}",
                params={"PageNumber": page},
                timeout=30,
            )
            resp.raise_for_status()
            html = resp.text

            # Extract law IDs from URLs in the page
            pattern = r'/BoeLaws/Laws/LawDetails/([0-9a-f\-]{36})/1'
            matches = re.findall(pattern, html)

            # Extract law names (they appear in link text)
            name_pattern = r'<a[^>]*href="[^"]*LawDetails/([0-9a-f\-]{36})/1"[^>]*>([^<]+)</a>'
            name_matches = re.findall(name_pattern, html)

            for law_id, law_name in name_matches:
                law_name = law_name.strip()
                if law_id not in seen_ids and len(law_name) > 3:
                    seen_ids.add(law_id)
                    category = guess_category(law_name)
                    discovered.append({
                        "law_id": law_id,
                        "law_name": law_name,
                        "category": category,
                        "discovered_at": datetime.now().isoformat()
                    })

            # Also try plain ID matches without names
            for law_id in matches:
                if law_id not in seen_ids:
                    seen_ids.add(law_id)

            if not matches:
                log.info(f"  No more results at page {page}")
                break

            time.sleep(REQUEST_DELAY)

        except Exception as e:
            log.warning(f"  Error on page {page}: {e}")
            continue

    log.info(f"✅ Discovered {len(discovered)} laws from BOE website")
    return discovered


def guess_category(name):
    """Guess a category from the law name"""
    mapping = {
        "عمل": "labor_law", "عمال": "labor_law",
        "شركات": "companies_law", "تجاري": "commercial_law",
        "جزائي": "criminal_procedure", "جنائي": "criminal_law",
        "مرافعات": "litigation", "قضا": "judiciary",
        "تنفيذ": "execution_law", "إثبات": "evidence_law",
        "تحكيم": "arbitration", "إفلاس": "bankruptcy",
        "ضريب": "tax", "زكا": "tax", "جمارك": "customs",
        "مرور": "traffic", "نقل": "transport",
        "اتصالات": "telecom", "تقني": "telecom",
        "معلوماتية": "cyber_crimes", "إلكتروني": "ecommerce",
        "بيانات": "data_protection", "خصوصي": "data_protection",
        "استثمار": "investment", "منافس": "competition",
        "بيئ": "environment", "صح": "health",
        "تعليم": "education", "جامع": "education",
        "إعلام": "media", "مطبوعات": "media",
        "عقار": "real_estate", "ملكية": "real_estate",
        "تأمين": "social_insurance", "خدمة مدنية": "civil_service",
        "مكافح": "criminal_law", "رشوة": "criminal_law",
        "غسل": "aml_law", "إرهاب": "terrorism",
        "أحوال شخصية": "personal_status", "أسرة": "personal_status",
        "شورى": "constitutional", "وزراء": "constitutional",
        "حكم": "constitutional", "أساسي": "constitutional",
        "مناطق": "regions", "بلدي": "municipal",
        "تجارة": "commercial_law", "سجل تجار": "commercial_registry",
        "منافسات": "procurement", "مشتريات": "procurement",
        "بترول": "petroleum", "طاقة": "energy",
        "طيران": "aviation", "بحري": "maritime",
        "سلاح": "security", "أمن": "security",
        "علامات": "intellectual_property", "براءات": "intellectual_property",
        "مؤلف": "intellectual_property", "حقوق": "intellectual_property",
        "هيئة": "regulatory", "تنظيم": "regulatory", "مؤسسة": "regulatory",
    }
    for keyword, cat in mapping.items():
        if keyword in name:
            return cat
    return "general"


# ====================================================================
# Law fetching and processing
# ====================================================================
def fetch_law_html(law_id):
    """Fetch law page HTML from BOE"""
    url = BOE_LAW_URL.format(law_id=law_id)
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    return resp.text


def extract_law_text(html):
    """Extract clean text from law HTML page"""
    text = re.sub(r'<script[^>]*>[\s\S]*?</script>', '', html, flags=re.I)
    text = re.sub(r'<style[^>]*>[\s\S]*?</style>', '', text, flags=re.I)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = (text.replace('&nbsp;', ' ').replace('&amp;', '&')
            .replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"'))
    text = re.sub(r'\s+', ' ', text).strip()

    for marker in ['نـــص النظـــام', 'نص النظام', 'المادة الأولى']:
        idx = text.find(marker)
        if idx > -1:
            text = text[idx:]
            break

    for footer in ['جميع الحقوق محفوظة', 'go to top', 'Additional Links']:
        idx = text.find(footer)
        if idx > -1:
            text = text[:idx]

    return text.strip()


def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=OVERLAP):
    """Split text into overlapping chunks"""
    chunks = []
    start = 0
    idx = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end].strip()
        if len(chunk) > 50:
            chunks.append({"index": idx, "text": chunk})
            idx += 1
        if end >= len(text):
            break
        start += chunk_size - overlap
    return chunks


def get_embedding(text):
    """Get embedding from Ollama"""
    resp = requests.post(
        f"{OLLAMA_URL}/api/embeddings",
        json={"model": EMBEDDING_MODEL, "prompt": text},
        timeout=120
    )
    resp.raise_for_status()
    return resp.json()["embedding"]


def upsert_chunks(collection_id, law, chunks):
    """Embed and upsert all chunks for a law"""
    success = 0
    for i, chunk in enumerate(chunks):
        chunk_id = f"boe_{law['category']}_{law['law_id'][:8]}_c{chunk['index']}"
        try:
            embedding = get_embedding(chunk["text"])
            requests.post(
                f"{CHROMADB_URL}/api/v1/collections/{collection_id}/upsert",
                json={
                    "ids": [chunk_id],
                    "embeddings": [embedding],
                    "documents": [chunk["text"]],
                    "metadatas": [{
                        "law_name": law["law_name"],
                        "law_id": law["law_id"],
                        "source": "laws.boe.gov.sa",
                        "category": law["category"],
                        "chunk_index": chunk["index"],
                        "ingested_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "auto_updated": "true"
                    }]
                },
                timeout=30
            ).raise_for_status()
            success += 1
            if (i + 1) % 10 == 0:
                log.info(f"    [{i+1}/{len(chunks)}] chunks embedded...")
        except Exception as e:
            log.error(f"    Chunk {chunk_id}: {e}")

    return success


# ====================================================================
# Main orchestration
# ====================================================================
def find_missing_laws():
    """Compare registry with ChromaDB and return missing laws"""
    registry = load_registry()
    existing = get_existing_laws()

    missing = []
    for law in registry:
        # Check both by law_id and by name (in case IDs differ)
        if law["law_id"] not in existing["law_ids"] and law["law_name"] not in existing["counts"]:
            missing.append(law)

    return missing, registry, existing


def process_law(law, collection_id):
    """Fetch, extract, chunk, embed, and store a single law"""
    log.info(f"  📥 Fetching: {law['law_name']}...")
    html = fetch_law_html(law["law_id"])
    log.info(f"     HTML: {len(html):,} bytes")

    text = extract_law_text(html)
    log.info(f"     Text: {len(text):,} chars")

    if len(text) < 100:
        log.warning(f"     ⚠️ Text too short, skipping")
        return 0

    chunks = chunk_text(text)
    log.info(f"     Chunks: {len(chunks)}")

    saved = upsert_chunks(collection_id, law, chunks)
    log.info(f"     ✅ Saved: {saved}/{len(chunks)} chunks")
    return saved


def generate_report():
    """Generate a detailed status report"""
    log.info("=" * 60)
    log.info("  📊 تقرير حالة القوانين السعودية")
    log.info("=" * 60)

    registry = load_registry()
    existing = get_existing_laws()

    log.info(f"\n  📚 إجمالي في السجل: {len(registry)} نظام")
    log.info(f"  💾 إجمالي في ChromaDB: {existing['total']} قطعة")
    log.info(f"  📋 أنظمة فريدة في ChromaDB: {len(existing['counts'])} نظام")

    # Show what's present
    log.info(f"\n  ✅ الأنظمة الموجودة:")
    for name, count in existing["counts"].most_common():
        log.info(f"     [{count:3d} chunks] {name}")

    # Show what's missing
    missing = []
    for law in registry:
        if law["law_id"] not in existing["law_ids"] and law["law_name"] not in existing["counts"]:
            missing.append(law)

    log.info(f"\n  ❌ الأنظمة الناقصة ({len(missing)}):")
    for law in missing:
        log.info(f"     - {law['law_name']} ({law['category']})")

    log.info("=" * 60)
    return {"present": len(existing["counts"]), "missing": len(missing), "total_chunks": existing["total"]}


def run_update(force=False, dry_run=False, discover=False):
    """Main update orchestration"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log.info("=" * 60)
    log.info(f"  🔄 التحديث الذاتي للقوانين السعودية")
    log.info(f"  {timestamp}")
    log.info("=" * 60)

    # Step 1: Discover new laws if requested
    if discover:
        log.info("\n📡 Phase 1: Discovering laws from BOE website...")
        new_laws = discover_laws_from_boe()
        if new_laws:
            save_discovered(new_laws)
            log.info(f"   Found {len(new_laws)} laws on website")

    # Step 2: Find what's missing
    log.info("\n📊 Phase 2: Comparing registry with ChromaDB...")
    if force:
        registry = load_registry()
        missing = registry
        existing = get_existing_laws()
        log.info(f"   FORCE mode: will re-process all {len(missing)} laws")
    else:
        missing, registry, existing = find_missing_laws()
        log.info(f"   Registry: {len(registry)} laws")
        log.info(f"   In ChromaDB: {len(existing['counts'])} laws ({existing['total']} chunks)")
        log.info(f"   Missing: {len(missing)} laws")

    if not missing:
        log.info("\n✅ All laws are up to date! Nothing to do.")
        return {"status": "up_to_date", "processed": 0}

    log.info(f"\n📋 Laws to process:")
    for law in missing:
        log.info(f"   - {law['law_name']} ({law['category']})")

    if dry_run:
        log.info("\n🔍 DRY RUN - No changes will be made")
        return {"status": "dry_run", "missing": len(missing)}

    # Step 3: Process missing laws
    log.info(f"\n⚡ Phase 3: Processing {len(missing)} laws...")
    collection_id = get_collection_id()
    total_saved = 0
    errors = 0

    for i, law in enumerate(missing, 1):
        log.info(f"\n[{i}/{len(missing)}] {law['law_name']}")
        try:
            saved = process_law(law, collection_id)
            total_saved += saved
            time.sleep(REQUEST_DELAY)
        except Exception as e:
            log.error(f"  ❌ Error: {e}")
            errors += 1

    # Step 4: Report
    final_count = requests.get(
        f"{CHROMADB_URL}/api/v1/collections/{collection_id}/count", timeout=10
    ).json()

    log.info("\n" + "=" * 60)
    log.info("  📊 التقرير النهائي")
    log.info("=" * 60)
    log.info(f"  أنظمة معالجة: {len(missing)}")
    log.info(f"  قطع محفوظة: {total_saved}")
    log.info(f"  أخطاء: {errors}")
    log.info(f"  ChromaDB الآن: {final_count} قطعة")
    log.info("=" * 60)

    return {
        "status": "completed",
        "processed": len(missing),
        "chunks_saved": total_saved,
        "errors": errors,
        "total_in_db": final_count,
        "timestamp": timestamp
    }


# ====================================================================
# CLI Entry Point
# ====================================================================
if __name__ == "__main__":
    args = sys.argv[1:]

    if "--report" in args:
        generate_report()
    elif "--discover" in args:
        run_update(discover=True, dry_run="--dry-run" in args)
    elif "--force" in args:
        run_update(force=True)
    elif "--dry-run" in args:
        run_update(dry_run=True)
    else:
        run_update()
