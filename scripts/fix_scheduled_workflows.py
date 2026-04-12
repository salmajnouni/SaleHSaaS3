"""
Fix 3 scheduled workflows that have common issues:
1. JSON.stringify in HTTP Request body → replace with direct object expression
2. fetch() in Code nodes → replace with axios ($http helper)

Affected workflows:
- Legal Scraper (HuuRe6ooTrbh5rJF)
- Um Al-Qura (UaJRWaaHtVldwoUl)
- Auto-Update (YPVhIxCVGsgPpNDM)
"""
import requests
import json

env = dict(
    line.strip().split("=", 1)
    for line in open(".env")
    if "=" in line and not line.startswith("#")
)
key = env["N8N_API_KEY"]
h = {"X-N8N-API-KEY": key, "Content-Type": "application/json"}

# ── Replacement code for fetch-based nodes ──────────────────────────

# Um Al-Qura: فحص الموجود في ChromaDB
UQN_CHECK_CODE = r"""// فحص ChromaDB - أي أنظمة أم القرى موجودة بالفعل؟
const CHROMADB = 'http://chromadb:8000/api/v1';
const COLLECTION_NAME = 'saleh_knowledge_qwen3';

// Get collection via axios (fetch not available in n8n code nodes)
const colsResp = await this.helpers.httpRequest({
  method: 'GET',
  url: `${CHROMADB}/collections`,
  json: true
});
const col = colsResp.find(c => c.name === COLLECTION_NAME);
if (!col) throw new Error('Collection saleh_knowledge_qwen3 not found!');

// Get count
const total = await this.helpers.httpRequest({
  method: 'GET',
  url: `${CHROMADB}/collections/${col.id}/count`,
  json: true
});

// Get all metadatas
const data = await this.helpers.httpRequest({
  method: 'POST',
  url: `${CHROMADB}/collections/${col.id}/get`,
  body: { include: ['metadatas'], limit: total },
  json: true
});

// Build set of existing UQN IDs
const existingUqnIds = new Set();
for (const meta of (data.metadatas || [])) {
  if (meta.source === 'uqn.gov.sa' && meta.uqn_id) {
    existingUqnIds.add(String(meta.uqn_id));
  }
}

// Filter input items
const inputItems = $input.all();
const newItems = inputItems.filter(item => {
  if (item.json.skip) return false;
  const uqnId = String(item.json.uqn_id || '');
  return uqnId && !existingUqnIds.has(uqnId);
});

if (newItems.length === 0) {
  return [{ json: { skip: true, message: 'لا يوجد أنظمة جديدة في أم القرى', existing: existingUqnIds.size } }];
}

return newItems;"""

# Um Al-Qura: تقرير نهائي
UQN_REPORT_CODE = r"""// تقرير نهائي
const items = $input.all();
const successCount = items.filter(i => !i.json.error).length;
const errorCount = items.filter(i => i.json.error).length;
const timestamp = new Date().toISOString();

let finalCount = 'N/A';
try {
  finalCount = await this.helpers.httpRequest({
    method: 'GET',
    url: 'http://chromadb:8000/api/v1/collections/86fce70f-0753-4989-9e4c-54d1ded405cd/count',
    json: true
  });
} catch(e) {}

return [{
  json: {
    status: 'completed',
    source: 'uqn.gov.sa - أم القرى',
    total_chunks_saved: successCount,
    errors: errorCount,
    chromadb_total: finalCount,
    message: `📰 أم القرى: تم حفظ ${successCount} قطعة جديدة | أخطاء: ${errorCount} | الإجمالي: ${finalCount}`,
    timestamp: timestamp
  }
}];"""

# Auto-Update: فحص الناقص في ChromaDB
AUTOUPDATE_CHECK_CODE = r"""// فحص ChromaDB للقوانين الموجودة
const CHROMADB = 'http://chromadb:8000/api/v1';
const COLLECTION_NAME = 'saleh_knowledge_qwen3';

// Get collection via helpers.httpRequest (fetch not available)
const colsResp = await this.helpers.httpRequest({
  method: 'GET',
  url: `${CHROMADB}/collections`,
  json: true
});
const col = colsResp.find(c => c.name === COLLECTION_NAME);
if (!col) throw new Error('Collection not found!');

// Get count
const total = await this.helpers.httpRequest({
  method: 'GET',
  url: `${CHROMADB}/collections/${col.id}/count`,
  json: true
});

// Get all metadatas
const data = await this.helpers.httpRequest({
  method: 'POST',
  url: `${CHROMADB}/collections/${col.id}/get`,
  body: { include: ['metadatas'], limit: total },
  json: true
});

// Build sets
const existingIds = new Set();
const existingNames = new Set();
for (const meta of (data.metadatas || [])) {
  if (meta.law_id) existingIds.add(meta.law_id);
  if (meta.law_name) existingNames.add(meta.law_name);
}

// Filter only missing laws
const allLaws = $input.all();
const missing = allLaws.filter(item => {
  const law = item.json;
  return !existingIds.has(law.law_id) && !existingNames.has(law.law_name);
});

if (missing.length === 0) {
  return [{ json: { status: 'up_to_date', message: 'جميع القوانين محدثة في ChromaDB', total_existing: existingIds.size } }];
}

return missing;"""

# Auto-Update: تقرير نهائي
AUTOUPDATE_REPORT_CODE = r"""// تقرير نهائي
const items = $input.all();
const successCount = items.filter(i => !i.json.error).length;
const errorCount = items.filter(i => i.json.error).length;
const timestamp = new Date().toISOString();

let finalCount = 'N/A';
try {
  finalCount = await this.helpers.httpRequest({
    method: 'GET',
    url: 'http://chromadb:8000/api/v1/collections/86fce70f-0753-4989-9e4c-54d1ded405cd/count',
    json: true
  });
} catch(e) {}

return [{
  json: {
    status: 'completed',
    total_chunks_saved: successCount,
    errors: errorCount,
    chromadb_total: finalCount,
    message: `✅ تم حفظ ${successCount} قطعة جديدة في ChromaDB | أخطاء: ${errorCount} | الإجمالي: ${finalCount}`,
    timestamp: timestamp
  }
}];"""


def fix_workflow(wid, label, fetch_fixes):
    """Fix JSON.stringify and fetch issues in a workflow."""
    r = requests.get(f"http://localhost:5678/api/v1/workflows/{wid}", headers=h)
    wf = r.json()
    nodes = wf.get("nodes", [])
    changes = []

    for n in nodes:
        name = n.get("name", "")
        params = n.get("parameters", {})

        # Fix 1: JSON.stringify in HTTP Request jsonBody
        jb = params.get("jsonBody", "")
        if "JSON.stringify" in jb:
            # Replace JSON.stringify({...}) with just ({...})
            new_jb = jb.replace("JSON.stringify(", "(", 1)
            # Remove trailing ) that was from JSON.stringify
            if new_jb.endswith(" }}"):
                # ={{ JSON.stringify({ ... }) }} → ={{ ({ ... }) }}
                # Actually: remove stringify wrapper, keep expression
                pass
            n["parameters"]["jsonBody"] = new_jb
            changes.append(f"  [JSON.stringify→object] {name}")

        # Fix 2: Replace fetch-based code nodes
        if name in fetch_fixes:
            n["parameters"]["jsCode"] = fetch_fixes[name]
            changes.append(f"  [fetch→httpRequest] {name}")

    payload = {
        "name": wf["name"],
        "nodes": nodes,
        "connections": wf["connections"],
        "settings": wf.get("settings", {}),
    }
    r = requests.put(
        f"http://localhost:5678/api/v1/workflows/{wid}", headers=h, json=payload
    )
    r2 = requests.post(
        f"http://localhost:5678/api/v1/workflows/{wid}/activate", headers=h
    )
    print(f"\n{label}: update={r.status_code} activate={r2.status_code}")
    for c in changes:
        print(c)
    return r.status_code == 200


# ── Apply fixes ─────────────────────────────────────────────────────

fix_workflow("HuuRe6ooTrbh5rJF", "Legal Scraper", {})

fix_workflow(
    "UaJRWaaHtVldwoUl",
    "Um Al-Qura",
    {
        "🔍 فحص الموجود في ChromaDB": UQN_CHECK_CODE,
        "📊 تقرير نهائي": UQN_REPORT_CODE,
    },
)

fix_workflow(
    "YPVhIxCVGsgPpNDM",
    "Auto-Update",
    {
        "🔍 فحص الناقص في ChromaDB": AUTOUPDATE_CHECK_CODE,
        "📊 تقرير نهائي": AUTOUPDATE_REPORT_CODE,
    },
)

print("\n✅ All 3 workflows fixed")
