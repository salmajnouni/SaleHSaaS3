"""Smoke test: verify all live system paths are operational."""
import requests
import time
import json
import sys
import os
from pathlib import Path

# Load .env for credentials (never hardcode secrets)
_env_file = Path(__file__).resolve().parents[1] / ".env"
if _env_file.exists():
    with open(_env_file) as _f:
        for _line in _f:
            _line = _line.strip()
            if "=" in _line and not _line.startswith("#"):
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip().strip('"').strip("'"))

PASS = 0
FAIL = 0
RESULTS = []

def check(name, func):
    global PASS, FAIL
    try:
        ok, detail = func()
        status = "PASS" if ok else "FAIL"
        if ok:
            PASS += 1
        else:
            FAIL += 1
        RESULTS.append((status, name, detail))
        print(f"  {'✓' if ok else '✗'} {name}: {detail}")
    except Exception as e:
        FAIL += 1
        RESULTS.append(("FAIL", name, str(e)[:120]))
        print(f"  ✗ {name}: {e}")

# --- Docker containers ---
print("\n[1] Docker containers")

def check_container(name, url, expect_status=200):
    def _check():
        r = requests.get(url, timeout=10)
        return r.status_code == expect_status, f"HTTP {r.status_code}"
    return _check

check("Open WebUI", check_container("webui", "http://localhost:3000"))
check("ChromaDB", check_container("chromadb", "http://localhost:8010/api/v1/heartbeat"))
check("n8n", check_container("n8n", "http://localhost:5678/healthz"))
check("Data Pipeline", check_container("data_pipeline", "http://localhost:8001/health"))

def check_pipelines():
    api_key = os.environ.get("WEBUI_API_KEY", "")
    r = requests.get("http://localhost:9099/v1/models",
                     headers={"Authorization": f"Bearer {api_key}"},
                     timeout=10)
    return r.status_code == 200, f"HTTP {r.status_code}"

check("Pipelines (API key)", check_pipelines)

# SearXNG and Tika are internal-only (no host port mapping)
def check_internal(container, url):
    def _check():
        import subprocess
        r = subprocess.run(["docker", "exec", container, "wget", "-q", "-O-", url],
                          capture_output=True, text=True, timeout=10)
        return r.returncode == 0, f"exit={r.returncode} len={len(r.stdout)}"
    return _check

check("SearXNG (internal)", check_internal("salehsaas_searxng", "http://localhost:8080/healthz"))

def check_tika():
    import subprocess
    # Tika image has no curl/wget; check from data_pipeline which connects to it
    r = subprocess.run(["docker", "exec", "salehsaas_data_pipeline",
                        "python", "-c", "import urllib.request; print(urllib.request.urlopen('http://tika:9998/version').read()[:80])"],
                       capture_output=True, text=True, timeout=10)
    return r.returncode == 0 and b"Apache" not in b"" and len(r.stdout) > 5, f"exit={r.returncode} out={r.stdout.strip()[:60]}"

check("Tika (internal)", check_tika)

# --- Ollama ---
print("\n[2] Ollama")

def check_ollama_models():
    r = requests.get("http://localhost:11434/api/tags", timeout=10)
    models = [m["name"] for m in r.json().get("models", [])]
    required = ["qwen3:32b", "qwen2.5:7b", "qwen3-embedding:0.6b"]
    missing = [m for m in required if m not in models]
    if missing:
        return False, f"missing: {missing}"
    return True, f"{len(models)} models available"

def check_ollama_loaded():
    r = requests.get("http://localhost:11434/api/ps", timeout=10)
    loaded = [m["name"] for m in r.json().get("models", [])]
    required = ["qwen3:32b", "qwen2.5:7b", "qwen3-embedding:0.6b"]
    missing = [m for m in required if m not in loaded]
    if missing:
        return False, f"not loaded: {missing}"
    return True, f"{len(loaded)} models in VRAM (Forever)"

check("Ollama available", check_ollama_models)
check("Models in VRAM", check_ollama_loaded)

# --- Embedding ---
print("\n[3] Embedding")

def check_embed():
    r = requests.post("http://localhost:11434/api/embed", json={
        "model": "qwen3-embedding:0.6b",
        "input": "اختبار التضمين"
    }, timeout=30)
    data = r.json()
    dims = len(data.get("embeddings", [[]])[0])
    return dims == 1024, f"dims={dims}"

check("Embedding (qwen3-embedding)", check_embed)

# --- ChromaDB collection ---
print("\n[4] ChromaDB collection")

def check_chroma_collection():
    r = requests.get("http://localhost:8010/api/v1/collections", timeout=10)
    cols = r.json()
    qwen3 = [c for c in cols if c["name"] == "saleh_knowledge_qwen3"]
    if not qwen3:
        return False, "saleh_knowledge_qwen3 not found"
    return True, f"id={qwen3[0]['id']}"

def check_chroma_query():
    # Get embedding first
    er = requests.post("http://localhost:11434/api/embed", json={
        "model": "qwen3-embedding:0.6b",
        "input": "شروط الفسخ في العقود"
    }, timeout=30)
    emb = er.json()["embeddings"]
    # Query ChromaDB
    r = requests.post(
        "http://localhost:8010/api/v1/collections/86fce70f-0753-4989-9e4c-54d1ded405cd/query",
        json={"query_embeddings": emb, "n_results": 5},
        timeout=15
    )
    docs = r.json().get("documents", [[]])[0]
    return len(docs) > 0, f"{len(docs)} results"

check("Collection exists", check_chroma_collection)
check("RAG query (embed+search)", check_chroma_query)

# --- n8n API ---
print("\n[5] n8n API")

def check_n8n_api():
    n8n_jwt = os.environ.get("N8N_API_KEY", "")
    r = requests.get("http://localhost:5678/api/v1/workflows",
                     headers={"X-N8N-API-KEY": n8n_jwt}, timeout=10)
    if r.status_code != 200:
        return False, f"HTTP {r.status_code}"
    wfs = r.json().get("data", [])
    active = sum(1 for w in wfs if w["active"])
    return True, f"{active}/{len(wfs)} active workflows"

def check_n8n_login():
    email = os.environ.get("N8N_LOGIN_EMAIL", os.environ.get("N8N_USER", ""))
    password = os.environ.get("N8N_PASSWORD", "")
    r = requests.post("http://localhost:5678/rest/login", json={
        "emailOrLdapLoginId": email,
        "password": password
    }, timeout=10)
    return r.status_code == 200, f"HTTP {r.status_code}"

check("n8n API (JWT key)", check_n8n_api)
check("n8n login (.env password)", check_n8n_login)

# --- Council webhook (Innovation, lightest) ---
print("\n[6] Council smoke (Innovation)")

def check_council_webhook():
    start = time.time()
    r = requests.post("http://localhost:5678/webhook/council-innovation",
                      json={"question": "ما هي أفضل طريقة لتحسين أداء النظام؟"},
                      timeout=360)
    elapsed = time.time() - start
    if r.status_code != 200:
        return False, f"HTTP {r.status_code} in {elapsed:.0f}s"
    data = r.json()
    decision_len = len(data.get("decision", ""))
    rag = data.get("sources", {}).get("rag", 0)
    web = data.get("sources", {}).get("web", 0)
    return decision_len > 100, f"decision={decision_len}ch rag={rag} web={web} time={elapsed:.0f}s"

check("Innovation Council (full)", check_council_webhook)

# --- Summary ---
print(f"\n{'='*50}")
print(f"SMOKE TEST COMPLETE: {PASS} passed, {FAIL} failed")
if FAIL > 0:
    print("\nFailed tests:")
    for status, name, detail in RESULTS:
        if status == "FAIL":
            print(f"  ✗ {name}: {detail}")
sys.exit(0 if FAIL == 0 else 1)
