"""Fix remaining fetch patterns: .then() chains + broken resp.json() calls."""
import requests, json, os

env = {}
with open(os.path.join(os.path.dirname(__file__), '..', '.env')) as f:
    for line in f:
        line = line.strip()
        if '=' in line and not line.startswith('#'):
            k, v = line.split('=', 1)
            env[k] = v

key = env['N8N_API_KEY']
base = 'http://localhost:5678'
h = {'X-N8N-API-KEY': key, 'Content-Type': 'application/json'}

COLLECTION_ID = '86fce70f-0753-4989-9e4c-54d1ded405cd'

# ============================================================
# Fix patterns for each workflow + node
# ============================================================
fixes = [
    # --- Um Al-Qura: فحص الموجود ---
    {
        'workflow_id': 'UaJRWaaHtVldwoUl',
        'node_name': '🔍 فحص الموجود في ChromaDB',
        'replacements': [
            # Pattern: await fetch(`...`).then(r => r.json())
            (
                "const cols = await fetch(`${CHROMADB}/collections`).then(r => r.json());",
                "const cols = await helpers.httpRequest({ method: 'GET', url: `${CHROMADB}/collections`, json: true });"
            ),
            (
                "const total = await fetch(`${CHROMADB}/collections/${col.id}/count`).then(r => r.json());",
                "const total = await helpers.httpRequest({ method: 'GET', url: `${CHROMADB}/collections/${col.id}/count`, json: true });"
            ),
        ]
    },
    # --- Um Al-Qura: تقرير نهائي ---
    {
        'workflow_id': 'UaJRWaaHtVldwoUl',
        'node_name': '📊 تقرير نهائي',
        'replacements': [
            # Fix: helpers.httpRequest returns data directly, not a Response
            (
                "  const resp = await helpers.httpRequest({ method: \"GET\", url: 'http://chromadb:8000/api/v1/collections/86fce70f-0753-4989-9e4c-54d1ded405cd/count' });\n  finalCount = await resp.json();",
                "  finalCount = await helpers.httpRequest({ method: 'GET', url: 'http://chromadb:8000/api/v1/collections/86fce70f-0753-4989-9e4c-54d1ded405cd/count', json: true });"
            ),
        ]
    },
    # --- Auto-Update: فحص الناقص ---
    {
        'workflow_id': 'YPVhIxCVGsgPpNDM',
        'node_name': '🔍 فحص الناقص في ChromaDB',
        'replacements': [
            (
                "const cols = await fetch(`${CHROMADB}/collections`).then(r => r.json());",
                "const cols = await helpers.httpRequest({ method: 'GET', url: `${CHROMADB}/collections`, json: true });"
            ),
            (
                "const total = await fetch(`${CHROMADB}/collections/${col.id}/count`).then(r => r.json());",
                "const total = await helpers.httpRequest({ method: 'GET', url: `${CHROMADB}/collections/${col.id}/count`, json: true });"
            ),
        ]
    },
    # --- Auto-Update: تقرير نهائي ---
    {
        'workflow_id': 'YPVhIxCVGsgPpNDM',
        'node_name': '📊 تقرير نهائي',
        'replacements': [
            (
                "  const resp = await helpers.httpRequest({ method: \"GET\", url: 'http://chromadb:8000/api/v1/collections/86fce70f-0753-4989-9e4c-54d1ded405cd/count' });\n  finalCount = await resp.json();",
                "  finalCount = await helpers.httpRequest({ method: 'GET', url: 'http://chromadb:8000/api/v1/collections/86fce70f-0753-4989-9e4c-54d1ded405cd/count', json: true });"
            ),
        ]
    },
]

# ============================================================
# Apply fixes
# ============================================================
# Group by workflow
from collections import defaultdict
by_wf = defaultdict(list)
for fix in fixes:
    by_wf[fix['workflow_id']].append(fix)

for wf_id, wf_fixes in by_wf.items():
    r = requests.get(f'{base}/api/v1/workflows/{wf_id}', headers=h)
    wf = r.json()
    wf_name = wf.get('name', wf_id)
    print(f'\n{"="*60}')
    print(f'Workflow: {wf_name}')
    
    modified = False
    for fix in wf_fixes:
        node_name = fix['node_name']
        node = next((n for n in wf['nodes'] if n['name'] == node_name), None)
        if not node:
            print(f'  ⚠ Node not found: {node_name}')
            continue
        
        code = node['parameters']['jsCode']
        for old, new in fix['replacements']:
            if old in code:
                code = code.replace(old, new)
                print(f'  ✓ [{node_name}] replaced pattern')
                modified = True
            else:
                print(f'  ⚠ [{node_name}] pattern NOT found:')
                print(f'      Looking for: {repr(old[:80])}...')
        
        node['parameters']['jsCode'] = code
        
        # Final check: no more fetch( in this node
        if 'fetch(' in code:
            print(f'  ⚠ [{node_name}] STILL has fetch() calls!')
        else:
            print(f'  ✓ [{node_name}] clean - no fetch() remaining')
    
    if modified:
        requests.post(f'{base}/api/v1/workflows/{wf_id}/deactivate', headers=h)
        update_data = {
            'nodes': wf['nodes'],
            'connections': wf['connections'],
            'settings': wf.get('settings', {}),
            'name': wf['name']
        }
        r2 = requests.put(f'{base}/api/v1/workflows/{wf_id}', headers=h, json=update_data)
        r3 = requests.post(f'{base}/api/v1/workflows/{wf_id}/activate', headers=h)
        print(f'  Update: {r2.status_code} | Activate: {r3.status_code}')
    else:
        print(f'  No changes needed')

print(f'\n{"="*60}')
print('Done! All fetch() calls replaced with helpers.httpRequest()')
