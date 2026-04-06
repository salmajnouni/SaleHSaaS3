"""Extract execution error details from latest execution."""
import json
import subprocess

# Get latest execution ID
result = subprocess.run(
    ["docker", "exec", "salehsaas_postgres", "psql", "-U", "salehsaas", "-d", "salehsaas",
     "-t", "-A", "-c",
     """SELECT id, status FROM execution_entity WHERE "workflowId" = 'CwCounclWbhk001' ORDER BY "createdAt" DESC LIMIT 1"""],
    capture_output=True, text=True, encoding='utf-8'
)
exec_info = result.stdout.strip()
exec_id = exec_info.split('|')[0]
print(f"Latest execution: {exec_info}")

# Get execution data  
result2 = subprocess.run(
    ["docker", "exec", "salehsaas_postgres", "psql", "-U", "salehsaas", "-d", "salehsaas",
     "-t", "-A", "-c",
     f'SELECT "data"::text FROM execution_data WHERE "executionId" = {exec_id}'],
    capture_output=True, text=True, encoding='utf-8'
)

raw = result2.stdout.strip()
data = json.loads(raw)

if isinstance(data, list):
    for i, item in enumerate(data):
        if isinstance(item, str) and ('error' in item.lower() or 'invalid' in item.lower() or 'syntax' in item.lower()):
            print(f"\n  [{i}]: {item[:300]}")
        elif isinstance(item, str) and i < 30:
            print(f"  [{i}]: {item[:200]}")
        elif isinstance(item, dict):
            for k, v in item.items():
                if isinstance(v, str) and len(v) < 200 and ('error' in v.lower() or 'message' in k.lower() or k in ('error', 'cause', 'message', 'stack')):
                    print(f"  [{i}].{k}: {v[:200]}")
