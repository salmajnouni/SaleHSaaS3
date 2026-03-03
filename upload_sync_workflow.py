#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Upload the Saudi Laws Sync workflow to n8n.
Fixes: collection name = saleh_legal_knowledge, JSON body for embedding/upsert.
"""
import json
import requests
import sys

WORKFLOW_FILE = "n8n/workflows/saudi_laws_sync.json"
N8N_URL = "http://localhost:5678"
API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2MzM4ZjBkYi1kOTIwLTRmMGItOTE3Yi0xZjg3MDAyMDdiNjgiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwianRpIjoiNjkxNDA2MDctZTQ0MC00ZDZiLTk3NjktOWJiNmFhNjkxMTliIiwiaWF0IjoxNzcyNTIwMTYzLCJleHAiOjE3NzUwNzcyMDB9.sET4Cp57eYI5y_w9gfmFiPY260YolvUh9sVIglp7muA"

HEADERS = {
    "X-N8N-API-KEY": API_KEY,
    "Content-Type": "application/json"
}

print("Loading Sync workflow file...")
with open(WORKFLOW_FILE, 'r', encoding='utf-8') as f:
    wf_data = json.load(f)

nodes = wf_data.get('nodes', [])
print(f"Nodes: {len(nodes)}")

print("\nConnecting to n8n API...")
try:
    resp = requests.get(f"{N8N_URL}/api/v1/workflows", headers=HEADERS, timeout=10)
except requests.exceptions.ConnectionError:
    print("ERROR: Cannot connect to n8n at localhost:5678")
    print("Please import manually via n8n UI -> Import -> select n8n/workflows/saudi_laws_sync.json")
    sys.exit(0)

if resp.status_code != 200:
    print(f"n8n API error: {resp.status_code}")
    sys.exit(1)

workflows = resp.json().get('data', [])
print(f"Found {len(workflows)} workflows:")
for wf in workflows:
    print(f"  [{wf['id']}] {wf['name']}")

# Find the Sync workflow
sync_id = None
for wf in workflows:
    name = wf.get('name', '')
    if 'Sync' in name or 'سحب' in name or 'مزامنة' in name:
        sync_id = wf['id']
        print(f"\nFound Sync workflow: {name} (ID: {sync_id})")
        break

payload = {
    "name": wf_data.get("name"),
    "nodes": nodes,
    "connections": wf_data.get("connections", {}),
    "settings": wf_data.get("settings", {}),
    "staticData": None
}

if sync_id:
    print(f"Updating workflow (ID: {sync_id})...")
    r = requests.put(
        f"{N8N_URL}/api/v1/workflows/{sync_id}",
        headers=HEADERS,
        json=payload,
        timeout=30
    )
    if r.status_code in [200, 201]:
        print("Updated successfully!")
    else:
        print(f"Update failed: {r.status_code} - {r.text[:300]}")
        print("Please import manually via n8n UI.")
        sys.exit(0)
else:
    print("Sync workflow not found, creating new...")
    r = requests.post(
        f"{N8N_URL}/api/v1/workflows",
        headers=HEADERS,
        json=payload,
        timeout=30
    )
    if r.status_code in [200, 201]:
        sync_id = r.json().get('id')
        print(f"Created! ID: {sync_id}")
    else:
        print(f"Create failed: {r.status_code} - {r.text[:300]}")
        sys.exit(0)

print("\n" + "="*60)
print("SUCCESS! Sync workflow updated.")
print("="*60)
print("\nNow run the workflow in n8n:")
print("  1. Open http://localhost:5678")
print("  2. Open 'Saudi Laws Sync' workflow")
print("  3. Click 'Execute workflow' button")
print("  4. Wait ~5-10 minutes for data to sync")
print("  5. Then test the chat in Open WebUI")
print("="*60)
