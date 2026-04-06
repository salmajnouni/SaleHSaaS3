"""Check what header was used in execution 152 (working) vs 160 (failing)."""
import json
import subprocess

for exec_id in [152, 160]:
    result = subprocess.run(
        ["docker", "exec", "salehsaas_postgres", "psql", "-U", "salehsaas", "-d", "salehsaas",
         "-t", "-A", "-c",
         f'SELECT "data"::text FROM execution_data WHERE "executionId" = {exec_id}'],
        capture_output=True, text=True, encoding='utf-8'
    )
    raw = result.stdout.strip()
    data = json.loads(raw)
    
    print(f"\n=== Execution {exec_id} ===")
    for i, item in enumerate(data):
        if isinstance(item, str):
            if 'Bearer' in item or 'bearer' in item:
                print(f"  [{i}]: {item[:200]}")
            elif item == 'Authorization':
                print(f"  [{i}]: {item}")
                # Also show next index
                if i+1 < len(data):
                    print(f"  [{i+1}]: {data[i+1] if isinstance(data[i+1], str) else str(data[i+1])[:200]}")
