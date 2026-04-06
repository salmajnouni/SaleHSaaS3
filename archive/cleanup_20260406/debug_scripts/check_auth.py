"""Check what n8n actually resolved for the Authorization header."""
import json
import subprocess

result = subprocess.run(
    ["docker", "exec", "salehsaas_postgres", "psql", "-U", "salehsaas", "-d", "salehsaas",
     "-t", "-A", "-c",
     'SELECT "data"::text FROM execution_data WHERE "executionId" = 160'],
    capture_output=True, text=True, encoding='utf-8'
)

raw = result.stdout.strip()
data = json.loads(raw)

# Find all strings that look relevant
for i, item in enumerate(data):
    if isinstance(item, str):
        if 'Bearer' in item or 'bearer' in item or 'uthorization' in item:
            print(f"  [{i}]: {item[:300]}")
        elif 'WEBUI_API_KEY' in item or 'vars.' in item:
            print(f"  [{i}]: {item[:300]}")
    elif isinstance(item, dict):
        for k, v in item.items():
            if isinstance(v, str) and ('Bearer' in v or 'Authorization' in v or 'WEBUI' in v):
                print(f"  [{i}].{k}: {v[:300]}")
