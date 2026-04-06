"""Dump all string values from execution 152 to find auth mechanism."""
import json
import subprocess

result = subprocess.run(
    ["docker", "exec", "salehsaas_postgres", "psql", "-U", "salehsaas", "-d", "salehsaas",
     "-t", "-A", "-c",
     'SELECT "data"::text FROM execution_data WHERE "executionId" = 152'],
    capture_output=True, text=True, encoding='utf-8'
)
raw = result.stdout.strip()
data = json.loads(raw)

for i, item in enumerate(data):
    if isinstance(item, str) and len(item) < 300:
        print(f"  [{i}]: {item}")
