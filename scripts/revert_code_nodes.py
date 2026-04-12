"""
Revert Code nodes back to original fetch-based code (now that we're
using internal runner mode which allows fetch).
Keep the JSON.stringify→object fixes for HTTP Request nodes.
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

# ── Original fetch-based code for each node ──────────────────────────

# Um Al-Qura: فحص الموجود في ChromaDB (original code)
UQN_CHECK_CODE = """// فحص ChromaDB - أي أنظمة أم القرى موجودة بالفعل؟
const CHROMADB = 'http://chromadb:8000/api/v1';
const COLLECTION_NAME = 'saleh_knowledge_qwen3';

// Get collection
const cols = await fetch(`${CHROMADB}/collections`).then(r => r.json());
const col = cols.find(c => c.name === COLLECTION_NAME);
if (!col) throw new Error('Collection saleh_knowledge_qwen3 not found!');

// Get all metadatas
const total = await fetch(`${CHROMADB}/collections/${col.id}/count`).then(r => r.json());
const data = await fetch(`${CHROMADB}/collections/${col.id}/get`, {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({ include: ['metadatas'], limit: total })
}).then(r => r.json());

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

# Um Al-Qura: تقرير نهائي (original code)
UQN_REPORT_CODE = """// تقرير نهائي
const items = $input.all();
const successCount = items.filter(i => !i.json.error).length;
const errorCount = items.filter(i => i.json.error).length;
const timestamp = new Date().toISOString();

let finalCount = 'N/A';
try {
  const resp = await fetch('http://chromadb:8000/api/v1/collections/86fce70f-0753-4989-9e4c-54d1ded405cd/count');
  finalCount = await resp.json();
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

# Auto-Update: فحص الناقص في ChromaDB (original code)
AUTOUPDATE_CHECK_CODE = """// فحص ChromaDB للقوانين الموجودة
const CHROMADB = 'http://chromadb:8000/api/v1';
const COLLECTION_NAME = 'saleh_knowledge_qwen3';

// Get collection ID
const cols = await fetch(`${CHROMADB}/collections`).then(r => r.json());
const col = cols.find(c => c.name === COLLECTION_NAME);
if (!col) throw new Error('Collection not found!');

// Get all metadatas
const total = await fetch(`${CHROMADB}/collections/${col.id}/count`).then(r => r.json());
const data = await fetch(`${CHROMADB}/collections/${col.id}/get`, {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({ include: ['metadatas'], limit: total })
}).then(r => r.json());

// Build set of existing law_ids and law_names
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

# Auto-Update: تقرير نهائي (original code)
AUTOUPDATE_REPORT_CODE = """// تقرير نهائي
const items = $input.all();
const successCount = items.filter(i => !i.json.error).length;
const errorCount = items.filter(i => i.json.error).length;
const timestamp = new Date().toISOString();

let finalCount = 'N/A';
try {
  const resp = await fetch('http://chromadb:8000/api/v1/collections/86fce70f-0753-4989-9e4c-54d1ded405cd/count');
  finalCount = await resp.json();
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


def revert_code_nodes(wid, label, fetch_fixes):
    """Restore fetch-based code and keep JSON.stringify fixes."""
    r = requests.get(f"http://localhost:5678/api/v1/workflows/{wid}", headers=h)
    wf = r.json()
    nodes = wf.get("nodes", [])
    changes = []

    for n in nodes:
        name = n.get("name", "")
        if name in fetch_fixes:
            n["parameters"]["jsCode"] = fetch_fixes[name]
            changes.append(f"  [restored fetch] {name}")

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


revert_code_nodes(
    "UaJRWaaHtVldwoUl",
    "Um Al-Qura",
    {
        "🔍 فحص الموجود في ChromaDB": UQN_CHECK_CODE,
        "📊 تقرير نهائي": UQN_REPORT_CODE,
    },
)

revert_code_nodes(
    "YPVhIxCVGsgPpNDM",
    "Auto-Update",
    {
        "🔍 فحص الناقص في ChromaDB": AUTOUPDATE_CHECK_CODE,
        "📊 تقرير نهائي": AUTOUPDATE_REPORT_CODE,
    },
)

print("\n✅ Code nodes reverted to fetch (ready for internal runner)")
