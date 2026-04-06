import subprocess, json

result = subprocess.run(
    ["docker", "exec", "salehsaas_postgres", "psql", "-U", "salehsaas", "-d", "salehsaas",
     "-t", "-A", "-c",
     "SELECT data FROM execution_data WHERE \"executionId\" = '164';"],
    capture_output=True, text=True
)

raw = result.stdout.strip()
data = json.loads(raw)

# Print types and content of first 10 items
for i in range(min(10, len(data))):
    item = data[i]
    t = type(item).__name__
    if isinstance(item, str):
        print(f"[{i}] {t}: {item[:200]}")
    elif isinstance(item, dict):
        print(f"[{i}] {t}: {json.dumps(item, ensure_ascii=False)[:200]}")
    else:
        print(f"[{i}] {t}: {str(item)[:200]}")
