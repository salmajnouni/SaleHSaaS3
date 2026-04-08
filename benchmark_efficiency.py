#!/usr/bin/env python3
import json
import statistics
import time
from datetime import datetime, UTC

import requests

SAMPLES = 5
TIMEOUT = 15

ENDPOINTS = {
    "open_webui_health": "http://localhost:3000/health",
    "chromadb_heartbeat": "http://localhost:8010/api/v1/heartbeat",
    "data_pipeline_health": "http://localhost:8001/health",
    "n8n_health": "http://localhost:5678/healthz",
}

RAG_QUERY = "ما هي شروط الفسخ في العقود القانونية السعودية؟"


def measure_get(url: str, samples: int = SAMPLES):
    times = []
    statuses = []
    errors = []
    for _ in range(samples):
        t0 = time.perf_counter()
        try:
            r = requests.get(url, timeout=TIMEOUT)
            dt_ms = (time.perf_counter() - t0) * 1000
            times.append(dt_ms)
            statuses.append(r.status_code)
        except Exception as e:
            dt_ms = (time.perf_counter() - t0) * 1000
            times.append(dt_ms)
            statuses.append(None)
            errors.append(str(e))
    ok = any(s and 200 <= s < 500 for s in statuses)
    return {
        "ok": ok,
        "statuses": statuses,
        "avg_ms": round(statistics.mean(times), 2),
        "p95_ms": round(sorted(times)[max(0, int(len(times) * 0.95) - 1)], 2),
        "min_ms": round(min(times), 2),
        "max_ms": round(max(times), 2),
        "errors": errors,
    }


def measure_rag_pipeline():
    # Execute inside pipelines container for direct, realistic path timing.
    import subprocess

    code = r'''
import json, time, sys
sys.path.insert(0, '/app/pipelines')
from saleh_legal_rag import Pipeline
q = "ما هي شروط الفسخ في العقود القانونية السعودية؟"
p = Pipeline()

# retrieval latency
t0 = time.perf_counter()
res = p._search_chromadb(q)
retrieval_ms = (time.perf_counter() - t0) * 1000

# inlet latency
t1 = time.perf_counter()
body = {"messages": [{"role": "user", "content": q}], "model": "qwen2.5:14b"}
aug = p.inlet(body, user={"id": "bench"})
inlet_ms = (time.perf_counter() - t1) * 1000

# first-token latency from pipe (bounded wait to avoid hangs)
t2 = time.perf_counter()
first_chunk = ""
for ch in p.pipe(q, "bench", aug.get("messages", []), aug):
    first_chunk = ch
    break
first_token_ms = (time.perf_counter() - t2) * 1000

print(json.dumps({
    "retrieval_count": len(res),
    "top_similarity": (res[0].get("similarity") if res else None),
    "retrieval_ms": round(retrieval_ms, 2),
    "inlet_ms": round(inlet_ms, 2),
    "first_token_ms": round(first_token_ms, 2),
    "first_chunk_len": len(first_chunk or "")
}, ensure_ascii=False))
'''

    cmd = [
        "docker",
        "exec",
        "salehsaas_pipelines",
        "python3",
        "-c",
        code,
    ]
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True, timeout=45)
        line = out.strip().splitlines()[-1]
        data = json.loads(line)
        return {"ok": True, **data}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def classify(report):
    score = 0
    checks = []

    # endpoint responsiveness checks
    for k in ["open_webui_health", "chromadb_heartbeat", "data_pipeline_health", "n8n_health"]:
        v = report["endpoints"][k]
        ok = v["ok"] and v["avg_ms"] < 1500
        checks.append((k, ok, v["avg_ms"]))
        if ok:
            score += 1

    # rag checks
    rag = report["rag"]
    rag_ok = rag.get("ok") and rag.get("retrieval_count", 0) >= 5 and rag.get("first_token_ms", 999999) < 30000
    checks.append(("rag", rag_ok, rag.get("first_token_ms")))
    if rag_ok:
        score += 1

    if score == 5:
        level = "excellent"
    elif score >= 4:
        level = "good"
    elif score >= 3:
        level = "acceptable"
    else:
        level = "needs_attention"

    return level, checks


def main():
    report = {
        "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "samples": SAMPLES,
        "endpoints": {},
        "rag": {},
    }

    for name, url in ENDPOINTS.items():
        report["endpoints"][name] = measure_get(url)

    report["rag"] = measure_rag_pipeline()

    level, checks = classify(report)
    report["efficiency_level"] = level
    report["checks"] = checks

    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
