#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Patch saudi_laws_chat.json:
1. Fix Ollama model: llama3.1:8b -> llama3.1:latest
2. Fix context node to handle ChromaDB errors gracefully
3. Upload to n8n API
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

# Step 1: Load
print("Loading workflow file...")
with open(WORKFLOW_FILE, 'r', encoding='utf-8') as f:
    data = json.load(f)

nodes = data.get('nodes', [])
print(f"Nodes: {len(nodes)}")

# Step 2: Patch
for i, node in enumerate(nodes):
    name = node.get('name', '')

    if 'Ollama' in name:
        old = node['parameters'].get('jsonBody', '')
        new = old.replace('llama3.1:8b', 'llama3.1:latest')
        nodes[i]['parameters']['jsonBody'] = new
        if old != new:
            print("Fixed Ollama model: llama3.1:8b -> llama3.1:latest")
        else:
            print("Ollama model OK (already llama3.1:latest)")

    if 'تجهيز' in name:
        nodes[i]['parameters']['jsCode'] = CONTEXT_CODE
        print(f"Fixed context node: {name}")

data['nodes'] = nodes

# Step 3: Save
with open(WORKFLOW_FILE, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print("Saved patched file.")

# Step 4: Upload to n8n
print("\nConnecting to n8n API...")
try:
    resp = requests.get(f"{N8N_URL}/api/v1/workflows", headers=HEADERS, timeout=10)
    if resp.status_code != 200:
        print(f"n8n API error: {resp.status_code}")
        print("Please re-import the workflow file manually in n8n UI.")
        sys.exit(0)

    workflows = resp.json().get('data', [])
    wf_id = None
    for wf in workflows:
        wf_name = wf.get('name', '')
        if 'Saudi' in wf_name or 'مساعد' in wf_name:
            wf_id = wf['id']
            print(f"Found: {wf_name} (ID: {wf_id})")
            break

    if not wf_id:
        print("Workflow not found. Please import the file manually.")
        sys.exit(0)

    # Get full workflow from API
    resp2 = requests.get(f"{N8N_URL}/api/v1/workflows/{wf_id}", headers=HEADERS, timeout=10)
    wf_full = resp2.json()

    # Replace nodes
    wf_full['nodes'] = nodes

    # Upload
    resp3 = requests.put(
        f"{N8N_URL}/api/v1/workflows/{wf_id}",
        headers=HEADERS,
        json=wf_full,
        timeout=30
    )
    if resp3.status_code in [200, 201]:
        print("Uploaded to n8n successfully!")
    else:
        print(f"Upload failed: {resp3.status_code}")
        print(resp3.text[:300])
        print("Please re-import the workflow file manually.")

    # Activate
    try:
        requests.post(
            f"{N8N_URL}/api/v1/workflows/{wf_id}/activate",
            headers=HEADERS, timeout=10
        )
        print("Workflow activated!")
    except Exception:
        pass

except requests.exceptions.ConnectionError:
    print("Cannot connect to n8n (connection refused).")
    print("Workflow file patched. Please re-import manually:")
    print(f"  File: {WORKFLOW_FILE}")

print("\nDone!")
