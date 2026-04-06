import subprocess, json, gzip, base64

result = subprocess.run(
    ["docker", "exec", "salehsaas_postgres", "psql", "-U", "salehsaas", "-d", "salehsaas",
     "-t", "-A", "-c",
     "SELECT encode(data, 'base64') FROM execution_data WHERE \"executionId\" = '164';"],
    capture_output=True, text=True
)

raw_b64 = result.stdout.strip().replace("\n", "")
raw = base64.b64decode(raw_b64)

# Try different decompression strategies
for attempt_name, attempt_fn in [
    ("plain JSON", lambda d: json.loads(d)),
    ("gzip", lambda d: json.loads(gzip.decompress(d))),
    ("skip 1 byte gzip", lambda d: json.loads(gzip.decompress(d[1:]))),
]:
    try:
        data = attempt_fn(raw)
        print(f"Success with: {attempt_name}")
        break
    except Exception as e:
        print(f"{attempt_name}: {e}")
        continue
else:
    print(f"Raw bytes (first 50): {raw[:50]}")
    print(f"Raw len: {len(raw)}")
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
