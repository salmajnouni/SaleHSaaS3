#!/usr/bin/env python3
"""
ChromaDB Data Cleanup & Fix Script
===================================
1. Delete garbage chunks (error pages + test data)
2. Normalize duplicate law names (extra spaces, versions)
3. Reclassify "general" category with better categories
4. Re-scrape 6 failed BOE laws
"""
import requests, json, re, time, logging
import os
from collections import Counter, defaultdict
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings()

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
log = logging.getLogger(__name__)

BASE = 'http://localhost:8010/api/v1'
CID = '86fce70f-0753-4989-9e4c-54d1ded405cd'
OLLAMA = 'http://localhost:11434'
EMBED_MODEL = os.getenv('EMBEDDING_MODEL', 'nomic-embed-text:latest')
BOE_BASE = 'https://laws.boe.gov.sa'

if os.getenv('ALLOW_LEGACY_CHROMA_CLEANUP') != 'true':
    log.warning('Skipped: cleanup_chromadb is disabled by default (destructive operations).')
    log.warning('Set ALLOW_LEGACY_CHROMA_CLEANUP=true to run intentionally.')
    raise SystemExit(0)

def embed(text):
    r = requests.post(f'{OLLAMA}/api/embeddings', json={'model': EMBED_MODEL, 'prompt': text})
    return r.json()['embedding']

def chroma_get(params):
    r = requests.post(f'{BASE}/collections/{CID}/get', json=params)
    return r.json()

def chroma_delete(ids):
    r = requests.post(f'{BASE}/collections/{CID}/delete', json={'ids': ids})
    return r.json()

def chroma_update(ids, metadatas=None, documents=None, embeddings=None):
    payload = {'ids': ids}
    if metadatas:
        payload['metadatas'] = metadatas
    if documents:
        payload['documents'] = documents
    if embeddings:
        payload['embeddings'] = embeddings
    r = requests.post(f'{BASE}/collections/{CID}/update', json=payload)
    return r.json()

def chroma_upsert(ids, documents, metadatas, embeddings):
    r = requests.post(f'{BASE}/collections/{CID}/upsert', json={
        'ids': ids, 'documents': documents, 'metadatas': metadatas, 'embeddings': embeddings
    })
    return r.json()

def get_count():
    return requests.get(f'{BASE}/collections/{CID}/count').json()

# ============================================================
# Load ALL data
# ============================================================
log.info("Loading all data from ChromaDB...")
count = get_count()
all_ids = []
all_meta = []
all_docs = []
for offset in range(0, count, 5000):
    data = chroma_get({'include': ['metadatas', 'documents'], 'limit': 5000, 'offset': offset})
    all_ids.extend(data['ids'])
    all_meta.extend(data['metadatas'])
    all_docs.extend(data['documents'])
log.info(f"Loaded {len(all_ids)} chunks")

# ============================================================
# STEP 1: Delete garbage chunks
# ============================================================
log.info("\n" + "="*60)
log.info("STEP 1: Deleting garbage chunks")
log.info("="*60)

garbage_ids = []
garbage_details = []

for i, (did, meta, doc) in enumerate(zip(all_ids, all_meta, all_docs)):
    # Error pages from BOE
    if doc and 'عذراً' in doc and 'حدث خطأ' in doc and len(doc) < 300:
        garbage_ids.append(did)
        garbage_details.append(('error_page', meta.get('law_name', '?')))
    
    # Test judiciary files (no category, small, from knowledge_processed)
    if not meta.get('category') and meta.get('source', '') in [
        'نظام_القضاء_معالج.txt', 'judiciary_v4.txt', 'نظام_القضاء_تجريبي.txt',
        'judicial_system_1.txt', 'independence_of_judiciary.txt', 'judicial_system_2.txt'
    ]:
        garbage_ids.append(did)
        garbage_details.append(('test_data', meta.get('source', '?')))

if garbage_ids:
    log.info(f"Found {len(garbage_ids)} garbage chunks:")
    for gtype, gname in garbage_details:
        log.info(f"  [{gtype}] {gname}")
    
    chroma_delete(garbage_ids)
    log.info(f"✅ Deleted {len(garbage_ids)} garbage chunks")
else:
    log.info("No garbage found")

# Reload after deletion
count = get_count()
log.info(f"ChromaDB count after cleanup: {count}")

# Reload
all_ids = []
all_meta = []
all_docs = []
for offset in range(0, count, 5000):
    data = chroma_get({'include': ['metadatas', 'documents'], 'limit': 5000, 'offset': offset})
    all_ids.extend(data['ids'])
    all_meta.extend(data['metadatas'])
    all_docs.extend(data['documents'])

# ============================================================
# STEP 2: Normalize duplicate law names
# ============================================================
log.info("\n" + "="*60)
log.info("STEP 2: Normalizing duplicate law names")
log.info("="*60)

# Map of old_name -> normalized_name
name_fixes = {
    'نظام مكافحة غسل  الأموال': 'نظام مكافحة غسل الأموال',
    'نظام صندوق الاستثمارات  العامة': 'نظام صندوق الاستثمارات العامة',
    'نظام  المنافسات و المشتريات الحكومية': 'نظام المنافسات والمشتريات الحكومية',
}

# Also find any names with double spaces automatically
for i, meta in enumerate(all_meta):
    law_name = meta.get('law_name', '')
    if '  ' in law_name:  # double space
        normalized = re.sub(r'\s+', ' ', law_name).strip()
        if normalized != law_name and law_name not in name_fixes:
            name_fixes[law_name] = normalized

# Merge "الموافقة على..." duplicates with their base documents
approval_merges = {}
law_names = set(m.get('law_name', '') for m in all_meta if m.get('law_name'))
for name in law_names:
    if name.startswith('الموافقة على ') or name.startswith('اعتماد '):
        base = name.replace('الموافقة على ', '').replace('اعتماد ', '').replace('مشروع ', '')
        # Check if base law exists
        for other in law_names:
            if other != name and base in other and len(other) < len(name):
                approval_merges[name] = other
                break

log.info(f"Name normalizations (spaces): {len(name_fixes)}")
for old, new in name_fixes.items():
    log.info(f"  '{old}' → '{new}'")

log.info(f"Approval prefix merges: {len(approval_merges)}")
for old, new in approval_merges.items():
    log.info(f"  '{old}' → '{new}'")

# Apply name fixes
fix_count = 0
batch_ids = []
batch_metas = []

for i, (did, meta) in enumerate(zip(all_ids, all_meta)):
    law_name = meta.get('law_name', '')
    new_name = name_fixes.get(law_name) or approval_merges.get(law_name)
    if new_name:
        new_meta = dict(meta)
        new_meta['law_name'] = new_name
        batch_ids.append(did)
        batch_metas.append(new_meta)
        fix_count += 1

if batch_ids:
    # Update in batches of 500
    for start in range(0, len(batch_ids), 500):
        end = start + 500
        chroma_update(batch_ids[start:end], metadatas=batch_metas[start:end])
    log.info(f"✅ Fixed {fix_count} chunks with normalized names")
else:
    log.info("No name fixes needed")

# ============================================================
# STEP 3: Reclassify "general" category
# ============================================================
log.info("\n" + "="*60)
log.info("STEP 3: Reclassifying 'general' category")
log.info("="*60)

# Better category mapping based on law name keywords
CATEGORY_RULES = [
    # Constitutional & governance
    (r'النظام الأساسي للحكم|مجلس الوزراء|مجلس الشورى|هيئة البيعة|نظام المناطق', 'constitutional'),
    (r'نظام الحكم|الحكم المحلي', 'constitutional'),
    
    # Financial & banking
    (r'البنك المركزي|مؤسسة النقد|المصرف|مصرفي|التمويل|الائتمان|السوق المالية|الأوراق المالية|البورصة', 'finance'),
    (r'صندوق الاستثمارات|صندوق التنمية|الاستثمار|التمويل العقاري', 'finance'),
    
    # Military & security
    (r'خدمة الضباط|خدمة الأفراد|العسكري|الجيش|الحرس|الاستخبارات|أمن الدولة|الدفاع', 'military'),
    (r'التقاعد العسكري|مجلس الخدمة العسكرية', 'military'),
    
    # Civil service & government
    (r'الخدمة المدنية|التقاعد المدني|الموظف|الوظائف|المعاشات', 'civil_service'),
    (r'المنافسات.*المشتريات|التخصيص', 'procurement'),
    
    # Real estate & urban
    (r'العقار|عقاري|التسجيل العيني|الملكية|نزع ملكية|الإيجار|السكن|وحدات.*عقارية|مساهمات عقارية', 'real_estate'),
    (r'الطرق والمباني|مباني|عمارة', 'real_estate'),
    
    # Agriculture & water
    (r'الزراع|المياه|الري|حيوان|بيطري|الثروة.*الحيوانية|الصيد|المراعي|الأعلاف', 'agriculture'),
    
    # Mining & energy
    (r'التعدين|معادن|بترول|كهرباء|طاقة|غاز|نفط', 'energy'),
    
    # Transport
    (r'الطيران|بحري|موانئ|حديدية|نقل|سكك|مرور|مركبات', 'transport'),
    
    # Health
    (r'صح|طب|صيدل|مستشفى|دواء|مخدرات|تبغ|مكافحة.*ضار|تبرع.*أعضاء|نقل.*دم', 'health'),
    
    # Education & culture
    (r'جامع|تعليم|مدرسة|معهد|ثقاف|مكتبة|آثار|متاح|تراث|فنون', 'education'),
    (r'رياضة|كشافة|شباب', 'education'),
    
    # Commerce
    (r'تجار|شركات|إفلاس|سجل تجاري|غرف.*تجارية|علامات|وكالات|أسماء تجارية|منافسة|احتكار', 'commercial_law'),
    (r'المحكمة التجارية|المحاكم التجارية', 'commercial_law'),
    
    # Labor
    (r'عمل|عمال|عامل|التأمين.*تعطل|خدمة منزلية|تطوع', 'labor_law'),
    
    # Judiciary
    (r'قضا|محكم|ديوان المظالم|نياب|تحقيق|مرافعات|تنفيذ.*أحكام', 'judiciary'),
    
    # Environment
    (r'بيئة|نفايات|تلوث|محميات|حياة فطرية', 'environment'),
    
    # Telecom & IT
    (r'اتصالات|معلوماتية|إلكترون|رقمي|سيبران|بريد', 'telecom'),
    
    # Social
    (r'ضمان اجتماعي|جمعيات|مؤسسات أهلية|تعاونية|إعاقة|رعاية|رفق|حماية.*طفل', 'social'),
    
    # Civil law
    (r'معاملات مدنية|أحوال مدنية|جنسية|وثائق سفر|إقامة|سعوديين', 'civil_law'),
    
    # Media
    (r'مطبوعات|نشر|إعلام|صحف', 'media'),
    
    # Statistics & planning
    (r'إحصاء|تخطيط|استراتيج', 'statistics'),
    
    # Standards & quality
    (r'مواصفات|جودة|تقييس|اعتماد|مقيمين', 'standards'),
    
    # Insurance
    (r'تأمين(?!.*تعطل)|تعاوني', 'insurance'),
    
    # Intellectual property
    (r'حقوق المؤلف|براءات|ملكية فكرية', 'intellectual_property'),
    
    # International
    (r'اتفاقية|مجلس التعاون|خليج|دولي', 'international'),
    
    # Civil defense
    (r'دفاع مدني|حريق|طوارئ|كوارث', 'civil_defense'),
]

reclassify_count = 0
reclass_ids = []
reclass_metas = []
reclass_stats = Counter()

for i, (did, meta, doc) in enumerate(zip(all_ids, all_meta, all_docs)):
    if meta.get('category') != 'general':
        continue
    
    law_name = meta.get('law_name', '')
    # Try to match law name against rules
    new_cat = None
    for pattern, category in CATEGORY_RULES:
        if re.search(pattern, law_name):
            new_cat = category
            break
    
    # If still no match, try matching against document content (first 500 chars)
    if not new_cat and doc:
        snippet = doc[:500]
        for pattern, category in CATEGORY_RULES:
            if re.search(pattern, snippet):
                new_cat = category
                break
    
    if new_cat:
        new_meta = dict(meta)
        new_meta['category'] = new_cat
        reclass_ids.append(did)
        reclass_metas.append(new_meta)
        reclassify_count += 1
        reclass_stats[new_cat] += 1

log.info(f"Reclassifying {reclassify_count} chunks from 'general':")
for cat, cnt in reclass_stats.most_common():
    log.info(f"  general → {cat}: {cnt} chunks")

if reclass_ids:
    for start in range(0, len(reclass_ids), 500):
        end = start + 500
        chroma_update(reclass_ids[start:end], metadatas=reclass_metas[start:end])
    log.info(f"✅ Reclassified {reclassify_count} chunks")

# Check remaining general
remaining_general = sum(1 for m in all_meta if m.get('category') == 'general') - reclassify_count
log.info(f"Remaining 'general': ~{remaining_general} chunks")

# ============================================================
# STEP 4: Re-scrape 6 failed BOE laws
# ============================================================
log.info("\n" + "="*60)
log.info("STEP 4: Re-scraping 6 failed laws from BOE")
log.info("="*60)

failed_laws = [
    'نظام الغرف التجارية والصناعية',
    'لائحة عمال الخدمة المنزلية ومن في حكمهم',
    'نظام نزع ملكية العقارات للمنفعة العامة ووضع اليد المؤقت على العقار',
    'تنظيم المركز الوطني للدراسات الاستراتيجية التنموية',
    'تنظيم مجلس التنمية السياحي',
    'نظام الاتصالات',
]

# Load laws registry to get IDs
registry_path = 'data/laws_registry.json'
try:
    with open(registry_path, 'r', encoding='utf-8') as f:
        registry = json.load(f)
except:
    registry = {}

def fetch_boe_law(law_id, law_name):
    """Fetch a law from BOE and return text content"""
    url = f'{BOE_BASE}/BoeLaws/Laws/LawDetails/{law_id}/1'
    try:
        r = requests.get(url, verify=False, timeout=30)
        r.encoding = 'utf-8'
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # Remove scripts, styles
        for tag in soup(['script', 'style', 'nav', 'header', 'footer']):
            tag.decompose()
        
        content = soup.find('div', class_='law-content') or soup.find('div', id='lawContent')
        if not content:
            content = soup.find('main') or soup.find('body')
        
        text = content.get_text(separator='\n', strip=True) if content else soup.get_text(separator='\n', strip=True)
        
        # Clean
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        text = '\n'.join(lines)
        
        # Remove common header/footer noise
        noise = ['البحث في الوثائق النظامية', 'تسجيل الدخول', 'عذراً', 'جميع الحقوق محفوظة']
        for n in noise:
            if n in text[:200]:
                # Likely still an error page
                return None
        
        return text if len(text) > 200 else None
    except Exception as e:
        log.error(f"  Failed to fetch {law_name}: {e}")
        return None

def chunk_text(text, chunk_size=800, overlap=100):
    """Split text into overlapping chunks"""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk.strip())
        start = end - overlap
    return chunks

def guess_category(law_name, text=''):
    """Guess category from law name"""
    combined = law_name + ' ' + text[:500]
    for pattern, category in CATEGORY_RULES:
        if re.search(pattern, combined):
            return category
    return 'general'

# Find the law IDs for failed laws
law_id_map = {}
for law_name in failed_laws:
    if isinstance(registry, list):
        for entry in registry:
            lname = entry.get('law_name', '')
            lid = entry.get('law_id', '')
            if lname == law_name or law_name in lname:
                law_id_map[law_name] = lid
                break
    elif isinstance(registry, dict):
        for lid, lname in registry.items():
            if lname == law_name or law_name in str(lname):
                law_id_map[law_name] = lid
                break

# Also try to find via search on BOE
for law_name in failed_laws:
    if law_name not in law_id_map:
        log.info(f"  Searching BOE for: {law_name}")
        try:
            search_url = f'{BOE_BASE}/BoeLaws/Laws/Search'
            r = requests.get(search_url, params={'SearchText': law_name}, verify=False, timeout=15)
            soup = BeautifulSoup(r.text, 'html.parser')
            links = soup.find_all('a', href=re.compile(r'/BoeLaws/Laws/LawDetails/'))
            for link in links:
                href = link.get('href', '')
                match = re.search(r'/LawDetails/([a-f0-9-]+)', href)
                if match:
                    law_id_map[law_name] = match.group(1)
                    break
        except:
            pass

log.info(f"Found IDs for {len(law_id_map)}/{len(failed_laws)} failed laws")

rescrape_count = 0
for law_name in failed_laws:
    law_id = law_id_map.get(law_name)
    if not law_id:
        log.warning(f"  ⚠️ No ID found for: {law_name}")
        continue
    
    log.info(f"  📥 Re-scraping: {law_name}")
    
    # First delete old error chunk
    old = chroma_get({
        'where': {'law_name': law_name},
        'include': ['metadatas'],
        'limit': 10
    })
    if old['ids']:
        chroma_delete(old['ids'])
        log.info(f"    Deleted {len(old['ids'])} old error chunks")
    
    # Fetch fresh content
    text = fetch_boe_law(law_id, law_name)
    if not text:
        log.warning(f"    ❌ Still can't fetch {law_name} - BOE may be blocking")
        continue
    
    # Chunk and embed
    chunks = chunk_text(text)
    if not chunks:
        log.warning(f"    ❌ No chunks generated for {law_name}")
        continue
    
    category = guess_category(law_name, text)
    
    ids = []
    documents = []
    metadatas = []
    embeddings = []
    
    for j, chunk in enumerate(chunks):
        chunk_id = f"boe_{law_id}_{j}"
        vec = embed(chunk)
        ids.append(chunk_id)
        documents.append(chunk)
        metadatas.append({
            'source': 'laws.boe.gov.sa',
            'law_name': law_name,
            'category': category,
            'chunk_index': j,
            'total_chunks': len(chunks),
            'boe_law_id': law_id
        })
        embeddings.append(vec)
    
    # Upsert in batches
    for start in range(0, len(ids), 100):
        end = start + 100
        chroma_upsert(ids[start:end], documents[start:end], metadatas[start:end], embeddings[start:end])
    
    log.info(f"    ✅ Saved {len(chunks)} chunks for {law_name} [{category}]")
    rescrape_count += 1
    time.sleep(2)

log.info(f"✅ Re-scraped {rescrape_count}/{len(failed_laws)} laws")

# ============================================================
# FINAL SUMMARY
# ============================================================
final_count = get_count()
log.info("\n" + "="*60)
log.info("📋 CLEANUP SUMMARY")
log.info("="*60)
log.info(f"Garbage deleted: {len(garbage_ids)} chunks")
log.info(f"Names normalized: {fix_count} chunks")
log.info(f"Reclassified from general: {reclassify_count} chunks")
log.info(f"Laws re-scraped: {rescrape_count}/{len(failed_laws)}")
log.info(f"Final ChromaDB count: {final_count}")

# Show new category distribution
new_cats = Counter()
for offset in range(0, final_count, 5000):
    data = chroma_get({'include': ['metadatas'], 'limit': 5000, 'offset': offset})
    for m in data['metadatas']:
        new_cats[m.get('category', 'none')] += 1

log.info("\n📊 New category distribution:")
for cat, cnt in new_cats.most_common():
    pct = cnt * 100 // final_count
    bar = '█' * (pct // 2)
    log.info(f"  [{cnt:5d}] ({pct:2d}%) {cat} {bar}")
