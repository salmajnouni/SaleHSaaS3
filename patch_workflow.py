#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Upload the new Webhook-based Saudi Laws Chat workflow to n8n.
Replaces the old Chat Trigger workflow.
"""
import json
import os
import requests
import sys
N8N_URL = "http://localhost:5678"
API_KEY = os.environ.get("N8N_API_KEY", "")
if not API_KEY:
    print("ERROR: N8N_API_KEY environment variable not set."); sys.exit(1)

HEADERS = {
    "X-N8N-API-KEY": API_KEY,
    "Content-Type": "application/json"
}

# ── Load workflow file ────────────────────────────────────────────────────────
print("Loading workflow file...")
with open(WORKFLOW_FILE, 'r', encoding='utf-8') as f:
    new_workflow = json.load(f)

nodes = new_workflow.get('nodes', [])
print(f"Nodes: {len(nodes)}")
for n in nodes:
    print(f"  - {n.get('name','')} | {n.get('type','')}")

# ── Connect to n8n ────────────────────────────────────────────────────────────
print("\nConnecting to n8n API...")
try:
    resp = requests.get(f"{N8N_URL}/api/v1/workflows", headers=HEADERS, timeout=10)
except requests.exceptions.ConnectionError:
    print("ERROR: Cannot connect to n8n. Is it running on localhost:5678?")
    print("Please import the file manually via n8n UI.")
    sys.exit(0)

if resp.status_code != 200:
    print(f"n8n API error: {resp.status_code}")
    sys.exit(1)

workflows = resp.json().get('data', [])
print(f"Found {len(workflows)} workflows:")
for wf in workflows:
    print(f"  [{wf['id']}] {wf['name']}")

# ── Find the old Chat workflow ────────────────────────────────────────────────
old_wf_id = None
for wf in workflows:
    tags = [t.get('name','').lower() for t in wf.get('tags', [])]
    name = wf.get('name', '')
    if 'chat' in tags and 'n8n-openai-bridge' in tags and 'Sync' not in name and 'سحب' not in name:
        old_wf_id = wf['id']
        print(f"\nFound old workflow: {name} (ID: {old_wf_id})")
        break

if not old_wf_id:
    for wf in workflows:
        name = wf.get('name', '')
        if ('Assistant' in name or 'مساعد' in name) and 'Sync' not in name and 'سحب' not in name:
            old_wf_id = wf['id']
            print(f"\nFound old workflow by name: {name} (ID: {old_wf_id})")
            break

# ── Update existing or create new ────────────────────────────────────────────
payload = {
    "name": new_workflow.get("name"),
    "nodes": nodes,
    "connections": new_workflow.get("connections", {}),
    "settings": new_workflow.get("settings", {}),
    "staticData": None
}

if old_wf_id:
    print(f"\nUpdating existing workflow (ID: {old_wf_id})...")
    resp2 = requests.put(
        f"{N8N_URL}/api/v1/workflows/{old_wf_id}",
        headers=HEADERS,
        json=payload,
        timeout=30
    )
    if resp2.status_code in [200, 201]:
        print("Updated successfully!")
        wf_id = old_wf_id
    else:
        print(f"Update failed: {resp2.status_code} - {resp2.text[:300]}")
        print("Trying to create new workflow instead...")
        old_wf_id = None

if not old_wf_id:
    print("\nCreating new workflow...")
    # Add tags for auto-discovery
    payload["tags"] = [
        {"name": "n8n-openai-bridge"},
        {"name": "chat"},
        {"name": "saudi-laws"},
        {"name": "legal"}
    ]
    resp3 = requests.post(
        f"{N8N_URL}/api/v1/workflows",
        headers=HEADERS,
        json=payload,
        timeout=30
    )
    if resp3.status_code in [200, 201]:
        wf_id = resp3.json().get('id')
        print(f"Created! ID: {wf_id}")
    else:
        print(f"Create failed: {resp3.status_code} - {resp3.text[:300]}")
        print("Please import the file manually via n8n UI.")
        sys.exit(0)

# ── Activate ──────────────────────────────────────────────────────────────────
print("\nActivating workflow...")
try:
    r = requests.post(
        f"{N8N_URL}/api/v1/workflows/{wf_id}/activate",
        headers=HEADERS, timeout=10
    )
    if r.status_code in [200, 201]:
        print("Activated!")
    else:
        print(f"Activation response: {r.status_code} - {r.text[:100]}")
except Exception as e:
    print(f"Activation error: {e}")

# ── Show webhook URL ──────────────────────────────────────────────────────────
print("\n" + "="*60)
print("SUCCESS!")
print("="*60)
print("Webhook URL (for n8n_bridge models.json):")
print("  http://n8n:5678/webhook/saleh-legal-chat-001")
print("\nTest in Open WebUI now.")
print("="*60)
