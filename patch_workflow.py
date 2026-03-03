#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Patch saudi_laws_chat.json and upload to n8n.
Fixes:
1. Correct workflow selection (Chat workflow, not Sync)
2. Clean API payload (only allowed fields)
3. Handle ChromaDB errors gracefully
"""
import json
import requests
import sys

WORKFLOW_FILE = "n8n/workflows/saudi_laws_chat.json"
N8N_URL = "http://localhost:5678"
API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2MzM4ZjBkYi1kOTIwLTRmMGItOTE3Yi0xZjg3MDAyMDdiNjgiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwianRpIjoiNjkxNDA2MDctZTQ0MC00ZDZiLTk3NjktOWJiNmFhNjkxMTliIiwiaWF0IjoxNzcyNTIwMTYzLCJleHAiOjE3NzUwNzcyMDB9.sET4Cp57eYI5y_w9gfmFiPY260YolvUh9sVIglp7muA"

HEADERS = {
    "X-N8N-API-KEY": API_KEY,
    "Content-Type": "application/json"
}

CONTEXT_CODE = (
    "// تجهيز السياق من نتائج ChromaDB\n"
    "const query = $('📝 استخراج السؤال').first().json.query;\n"
    "const chromaResult = $input.first().json;\n"
    "\n"
    "let context = '';\n"
    "let sources = [];\n"
    "\n"
    "try {\n"
    "  if (chromaResult && !chromaResult.error && chromaResult.documents) {\n"
    "    const documents = chromaResult.documents[0] || [];\n"
    "    const metadatas = chromaResult.metadatas[0] || [];\n"
    "    const distances = chromaResult.distances[0] || [];\n"
    "    if (documents.length > 0) {\n"
    "      documents.forEach(function(doc, i) {\n"
    "        if ((distances[i] || 999) < 1.5) {\n"
    "          const meta = metadatas[i] || {};\n"
    "          const source = meta.source_name || meta.source || 'مصدر قانوني';\n"
    "          sources.push(source);\n"
    "          context += '[' + source + ']:\\n' + doc + '\\n\\n---\\n\\n';\n"
    "        }\n"
    "      });\n"
    "    }\n"
    "  }\n"
    "} catch(e) {\n"
    "  context = '';\n"
    "}\n"
    "\n"
    "const systemPrompt = 'أنت مساعد قانوني متخصص في الأنظمة والتشريعات السعودية.\\n'\n"
    "  + 'أجب على الأسئلة بدقة واحترافية باللغة العربية.\\n'\n"
    "  + 'استند إلى النصوص القانونية المقدمة إذا كانت متاحة.\\n'\n"
    "  + 'إذا لم تجد إجابة في النصوص، وضّح ذلك وقدّم معلومات عامة مفيدة.\\n\\n'\n"
    "  + (context ? ('السياق القانوني المتاح:\\n' + context) : 'لا توجد نصوص قانونية محددة متاحة لهذا السؤال.');\n"
    "\n"
    "return [{\n"
    "  json: {\n"
    "    query: query,\n"
    "    systemPrompt: systemPrompt,\n"
    "    hasContext: context.length > 0,\n"
    "    sources: sources.filter(function(v, i, a) { return a.indexOf(v) === i; })\n"
    "  }\n"
    "}];\n"
)

# ── Step 1: Patch local file ──────────────────────────────────────────────────
print("Loading workflow file...")
with open(WORKFLOW_FILE, 'r', encoding='utf-8') as f:
    data = json.load(f)

nodes = data.get('nodes', [])
print(f"Nodes in file: {len(nodes)}")

for i, node in enumerate(nodes):
    name = node.get('name', '')
    if 'Ollama' in name:
        old = node['parameters'].get('jsonBody', '')
        new = old.replace('llama3.1:8b', 'llama3.1:latest')
        nodes[i]['parameters']['jsonBody'] = new
        print("Ollama model: OK (llama3.1:latest)")
    if 'تجهيز' in name:
        nodes[i]['parameters']['jsCode'] = CONTEXT_CODE
        print(f"Fixed context node: {name}")

data['nodes'] = nodes
with open(WORKFLOW_FILE, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print("Local file saved.\n")

# ── Step 2: Connect to n8n ────────────────────────────────────────────────────
print("Connecting to n8n API...")
try:
    resp = requests.get(f"{N8N_URL}/api/v1/workflows", headers=HEADERS, timeout=10)
except requests.exceptions.ConnectionError:
    print("ERROR: Cannot connect to n8n. Is it running on localhost:5678?")
    print("Please import the file manually via n8n UI.")
    sys.exit(0)

if resp.status_code != 200:
    print(f"n8n API error: {resp.status_code} - {resp.text[:100]}")
    sys.exit(1)

workflows = resp.json().get('data', [])
print(f"Found {len(workflows)} workflows:")
for wf in workflows:
    tags = [t.get('name','') for t in wf.get('tags', [])]
    print(f"  [{wf['id']}] {wf['name']} | tags: {tags}")

# ── Step 3: Find the CHAT workflow (has 'chat' tag, not 'sync') ───────────────
wf_id = None
for wf in workflows:
    tags = [t.get('name','').lower() for t in wf.get('tags', [])]
    name = wf.get('name', '')
    # Must have 'chat' tag OR be the assistant (not the sync workflow)
    if 'chat' in tags and 'n8n-openai-bridge' in tags:
        wf_id = wf['id']
        print(f"\nSelected (by tags): {name} (ID: {wf_id})")
        break

if not wf_id:
    # Fallback: find by name containing 'Assistant' or 'مساعد' but NOT 'Sync'
    for wf in workflows:
        name = wf.get('name', '')
        if ('Assistant' in name or 'مساعد' in name) and 'Sync' not in name and 'سحب' not in name:
            wf_id = wf['id']
            print(f"\nSelected (by name): {name} (ID: {wf_id})")
            break

if not wf_id:
    print("\nERROR: Could not find the Chat workflow.")
    print("Please import the file manually via n8n UI.")
    sys.exit(0)

# ── Step 4: Upload using only allowed fields ──────────────────────────────────
print("\nUploading patched nodes to n8n...")

# n8n PUT /workflows/{id} only accepts: name, nodes, connections, settings, staticData
payload = {
    "name": data.get("name", "🤖 مساعد القوانين السعودية - Saudi Laws Assistant"),
    "nodes": nodes,
    "connections": data.get("connections", {}),
    "settings": data.get("settings", {}),
    "staticData": None
}

resp3 = requests.put(
    f"{N8N_URL}/api/v1/workflows/{wf_id}",
    headers=HEADERS,
    json=payload,
    timeout=30
)

if resp3.status_code in [200, 201]:
    print("Upload successful!")
else:
    print(f"Upload failed: {resp3.status_code}")
    print(resp3.text[:400])
    print("\nPlease import the file manually via n8n UI.")
    sys.exit(0)

# ── Step 5: Activate ──────────────────────────────────────────────────────────
try:
    r = requests.post(
        f"{N8N_URL}/api/v1/workflows/{wf_id}/activate",
        headers=HEADERS, timeout=10
    )
    print("Workflow activated!" if r.status_code in [200,201] else f"Activation: {r.status_code}")
except Exception as e:
    print(f"Activation skipped: {e}")

print("\n✅ Done! Test the chat in Open WebUI now.")
