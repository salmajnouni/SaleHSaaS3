"""Extract execution error details from n8n postgres DB."""
import json
import subprocess

result = subprocess.run(
    ["docker", "exec", "salehsaas_postgres", "psql", "-U", "salehsaas", "-d", "salehsaas",
     "-t", "-A", "-c", 'SELECT "data"::text FROM execution_data WHERE "executionId" = 158'],
    capture_output=True, text=True, encoding='utf-8'
)

raw = result.stdout.strip()
print(f"Data length: {len(raw)}")
print(f"First 100: {raw[:100]}")

try:
    data = json.loads(raw)
    print(f"\nType: {type(data)}, Length: {len(data)}")
    
    # n8n uses a flattened array format where objects reference indices
    # The first element is the main structure, others are referenced values
    if isinstance(data, list):
        # Print all short string values (these are the referenced values)
        for i, item in enumerate(data):
            if isinstance(item, str) and len(item) < 500:
                print(f"  [{i}]: {item[:200]}")
            elif isinstance(item, dict):
                for k, v in item.items():
                    if isinstance(v, str) and len(v) < 200:
                        print(f"  [{i}].{k}: {v[:200]}")
except json.JSONDecodeError as e:
    print(f"JSON parse error: {e}")
    # Try to find error text directly
    import re
    for m in re.finditer(r'(error|invalid|syntax|مت ال)[^"]{0,100}', raw, re.IGNORECASE):
        print(f"Found: {m.group()}")
