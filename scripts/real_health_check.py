"""Real system health check - no fake reports"""
import urllib.request
import json
import sys
import os

# Load .env
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
N8N_API_KEY = ""
if os.path.exists(env_path):
    with open(env_path, encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if line.startswith("N8N_API_KEY="):
                N8N_API_KEY = line.split("=", 1)[1].strip().strip('"').strip("'")

def check(url, timeout=10, auth=False):
    try:
        req = urllib.request.Request(url)
        req.add_header("Accept", "application/json")
        if auth and N8N_API_KEY:
            req.add_header("X-N8N-API-KEY", N8N_API_KEY)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, f"HTTP {e.code}: {e.reason}"
    except Exception as e:
        return 0, str(e)

def post(url, body, timeout=15):
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, f"HTTP {e.code}: {e.reason}"
    except Exception as e:
        return 0, str(e)

print("=" * 60)
print("REAL SYSTEM HEALTH CHECK - SaleHSaaS")
print("=" * 60)

# 1. n8n
print("\n=== 1. n8n API ===")
code, data = check("http://localhost:5678/api/v1/workflows", auth=True)
if code == 200:
    j = json.loads(data)
    wfs = j.get("data", [])
    active = [w for w in wfs if w.get("active")]
    inactive = [w for w in wfs if not w.get("active")]
    print(f"Total: {len(wfs)} | Active: {len(active)} | Inactive: {len(inactive)}")
    print("--- Active ---")
    for w in active:
        print(f"  {w['name']} [{w['id']}]")
    print("--- Inactive ---")
    for w in inactive:
        print(f"  {w['name']} [{w['id']}]")
else:
    print(f"FAIL: {data}")

# 2. Error Hunter Webhook
print("\n=== 2. Error Hunter Webhook ===")
code, data = post(
    "http://localhost:5678/webhook/error-hunt-v2",
    {"error": "test connection check"},
)
if code == 200:
    print(f"OK: {code} | {data[:300]}")
else:
    print(f"FAIL: {data}")

# 3. Ollama
print("\n=== 3. Ollama ===")
code, data = check("http://localhost:11434/api/tags")
if code == 200:
    j = json.loads(data)
    models = j.get("models", [])
    print(f"Models: {len(models)}")
    for m in models:
        print(f"  - {m['name']}")
    code2, data2 = check("http://localhost:11434/api/ps")
    if code2 == 200:
        j2 = json.loads(data2)
        running = j2.get("models", [])
        print(f"Running: {len(running)}")
        for m in running:
            print(f"  - {m['name']}")
        if not running:
            print("  (no models loaded)")
else:
    print(f"FAIL: {data}")

# 4. ChromaDB
print("\n=== 4. ChromaDB ===")
code, data = check("http://localhost:8010/api/v1/collections")
if code == 200:
    j = json.loads(data)
    print(f"Collections: {len(j)}")
    for c in j:
        cid = c["id"]
        cname = c["name"]
        # get count
        code3, data3 = check(f"http://localhost:8010/api/v1/collections/{cid}/count")
        count = data3 if code3 == 200 else "?"
        print(f"  {cname} [{cid}] => {count} docs")
else:
    print(f"FAIL: {data}")

# 5. SearXNG
print("\n=== 5. SearXNG ===")
code, data = check("http://localhost:8888/search?q=test&format=json", timeout=15)
if code == 200:
    j = json.loads(data)
    print(f"Results: {len(j.get('results', []))}")
else:
    print(f"FAIL: {data}")

# 6. Tika
print("\n=== 6. Tika ===")
code, data = check("http://localhost:9998/tika")
if code == 200:
    print(f"OK: {data[:100]}")
else:
    print(f"FAIL: {data}")

# 7. Data Pipeline
print("\n=== 7. Data Pipeline ===")
code, data = check("http://localhost:8001/")
if code == 200:
    j = json.loads(data)
    print(f"OK: {j.get('message', '')}")
else:
    print(f"FAIL: {data}")

# 8. Pipelines
print("\n=== 8. Pipelines ===")
code, data = check("http://localhost:9099/")
if code == 200:
    print(f"OK: status {code}")
else:
    print(f"FAIL: {data}")

# 9. n8n recent executions
print("\n=== 9. n8n Recent Failed Executions ===")
code, data = check("http://localhost:5678/api/v1/executions?status=error&limit=5", auth=True)
if code == 200:
    j = json.loads(data)
    execs = j.get("data", [])
    print(f"Recent failures: {len(execs)}")
    for ex in execs:
        wf = ex.get("workflowData", {}).get("name", "?")
        finished = ex.get("stoppedAt", "?")
        print(f"  [{finished}] {wf} - ID: {ex.get('id')}")
else:
    print(f"FAIL: {data}")

print("\n" + "=" * 60)
print("END OF REAL CHECK")
print("=" * 60)
