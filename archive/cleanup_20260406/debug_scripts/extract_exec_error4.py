import subprocess, json

result = subprocess.run(
    ["docker", "exec", "salehsaas_postgres", "psql", "-U", "salehsaas", "-d", "salehsaas",
     "-t", "-A", "-c",
     "SELECT data FROM execution_data WHERE \"executionId\" = '164';"],
    capture_output=True, text=True
)

raw = result.stdout.strip()
data = json.loads(raw)
print(f"Type: {type(data)}")
if isinstance(data, list):
    print(f"Length: {len(data)}")
    # n8n 2.x stores execution data as array of [key, value] pairs
    d = dict(data) if all(isinstance(x, list) and len(x) == 2 for x in data[:5]) else None
    if d:
        print(f"Keys: {list(d.keys())[:20]}")
        rd = d.get("resultData", {})
        if isinstance(rd, str):
            rd = json.loads(rd)
    else:
        # Maybe it's a different structure
        print(f"First item type: {type(data[0])}")
        print(f"First item: {json.dumps(data[0], ensure_ascii=False)[:500]}")
        rd = {}
elif isinstance(data, dict):
    rd = data.get("resultData", {})
else:
    print(f"Unexpected type: {type(data)}")
    exit(1)

error = rd.get("error", None) if isinstance(rd, dict) else None
if error:
    print("=== TOP LEVEL ERROR ===")
    print(json.dumps(error, indent=2, ensure_ascii=False)[:2000])

if isinstance(rd, dict):
    run_data = rd.get("runData", {})
    for node_name, runs in run_data.items():
        if isinstance(runs, list):
            for run in runs:
                if isinstance(run, dict) and run.get("error"):
                    print(f"\n=== ERROR IN NODE: {node_name} ===")
                    err = run["error"]
                    print(f"Message: {err.get('message', 'N/A')}")
                    print(f"Description: {err.get('description', 'N/A')}")
                    print(f"Stack: {str(err.get('stack', ''))[:500]}")
