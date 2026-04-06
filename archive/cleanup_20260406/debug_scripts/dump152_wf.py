"""Get workflowData from execution 152 to see how auth was configured."""
import json
import subprocess

result = subprocess.run(
    ["docker", "exec", "salehsaas_postgres", "psql", "-U", "salehsaas", "-d", "salehsaas",
     "-t", "-A", "-c",
     'SELECT "workflowData"::text FROM execution_data WHERE "executionId" = 152'],
    capture_output=True, text=True, encoding='utf-8'
)
raw = result.stdout.strip()
wf = json.loads(raw)

if isinstance(wf, list):
    # Compressed format - print all
    for i, item in enumerate(wf):
        if isinstance(item, str) and len(item) < 500:
            if 'auth' in item.lower() or 'header' in item.lower() or 'bearer' in item.lower() or 'cred' in item.lower() or 'api' in item.lower() or 'key' in item.lower():
                print(f"  [{i}]: {item[:300]}")
        elif isinstance(item, dict):
            for k, v in item.items():
                if isinstance(v, str) and ('auth' in k.lower() or 'header' in k.lower() or 'send' in k.lower() or 'specify' in k.lower() or 'cred' in k.lower()):
                    print(f"  [{i}].{k}: {v}")
elif isinstance(wf, dict):
    nodes = wf.get('nodes', [])
    for node in nodes:
        if node.get('id') == 'cw-0005':
            print(json.dumps(node.get('parameters', {}), indent=2, ensure_ascii=False))
            break
