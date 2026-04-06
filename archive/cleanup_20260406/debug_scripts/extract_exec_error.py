import subprocess, json, gzip, sys

# Get execution data for exec 164
result = subprocess.run(
    ["docker", "exec", "salehsaas_postgres", "psql", "-U", "salehsaas", "-d", "salehsaas",
     "-t", "-A", "-c",
     "SELECT encode(data, 'base64') FROM execution_data WHERE \"executionId\" = '164';"],
    capture_output=True, text=True
)

import base64
raw = base64.b64decode(result.stdout.strip())

try:
    data = json.loads(raw)
except:
    data = json.loads(gzip.decompress(raw))

# Find error nodes
rd = data.get("resultData", {})
error = rd.get("error", None)
if error:
    print("=== TOP LEVEL ERROR ===")
    print(json.dumps(error, indent=2, ensure_ascii=False)[:2000])

run_data = rd.get("runData", {})
for node_name, runs in run_data.items():
    for run in runs:
        if run.get("error"):
            print(f"\n=== ERROR IN NODE: {node_name} ===")
            err = run["error"]
            print(f"Message: {err.get('message', 'N/A')}")
            print(f"Description: {err.get('description', 'N/A')}")
            print(f"Stack: {str(err.get('stack', ''))[:500]}")
