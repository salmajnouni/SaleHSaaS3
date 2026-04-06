import subprocess, json, gzip, base64

result = subprocess.run(
    ["docker", "exec", "salehsaas_postgres", "psql", "-U", "salehsaas", "-d", "salehsaas",
     "-t", "-A", "-c",
     "SELECT data FROM execution_data WHERE \"executionId\" = '164';"],
    capture_output=True, text=True
)

raw = result.stdout.strip()
if not raw:
    print("No data returned")
    exit(1)

# data column is text, might be JSON directly or base64-encoded
try:
    data = json.loads(raw)
    print("Parsed as direct JSON")
except:
    try:
        decoded = base64.b64decode(raw)
        data = json.loads(decoded)
        print("Parsed as base64 JSON")
    except:
        try:
            decoded = base64.b64decode(raw)
            data = json.loads(gzip.decompress(decoded))
            print("Parsed as base64+gzip JSON")
        except Exception as e:
            print(f"Failed all: {e}")
            print(f"First 200 chars: {raw[:200]}")
            exit(1)

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
