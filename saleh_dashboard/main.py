"""
SaleH SaaS - Dashboard API
واجهة مراقبة النظام: ChromaDB، الملفات المعالجة، حالة الخدمات
"""

import os
import json
import glob
import requests
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import chromadb

# ─── إعدادات ─────────────────────────────────────────────────────────────────
CHROMA_HOST     = os.getenv("CHROMA_HOST", "chromadb")
CHROMA_PORT     = int(os.getenv("CHROMA_PORT", 8000))
CHROMA_TOKEN    = os.getenv("CHROMA_TOKEN", "salehsaas-chroma-token")
PIPELINE_URL    = os.getenv("PIPELINE_URL", "http://salehsaas_pipeline:8001")
OLLAMA_URL      = os.getenv("OLLAMA_URL", "http://ollama:11434")
ANYTHINGLLM_URL = os.getenv("ANYTHINGLLM_URL", "http://anythingllm:3001")
PROCESSED_DIR   = Path(os.getenv("PROCESSED_DIR", "/data/processed"))
INCOMING_DIR    = Path(os.getenv("INCOMING_DIR", "/data/incoming"))
FAILED_DIR      = Path(os.getenv("FAILED_DIR", "/data/failed"))
LORA_QUEUE_DIR  = Path(os.getenv("LORA_QUEUE_DIR", "/data/lora_queue"))

# ─── FastAPI App ──────────────────────────────────────────────────────────────
app = FastAPI(title="SaleH SaaS Dashboard", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ─── Static files ─────────────────────────────────────────────────────────────
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


def safe_get(url: str, timeout: int = 3) -> dict:
    """HTTP GET مع معالجة الأخطاء"""
    try:
        r = requests.get(url, timeout=timeout)
        return {"ok": r.status_code == 200, "status": r.status_code, "data": r.json() if r.ok else {}}
    except Exception as e:
        return {"ok": False, "status": 0, "error": str(e)}


def get_chroma_client():
    return chromadb.HttpClient(
        host=CHROMA_HOST,
        port=CHROMA_PORT,
        headers={"Authorization": f"Bearer {CHROMA_TOKEN}"}
    )


# ─── API Endpoints ────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """الصفحة الرئيسية للـ Dashboard"""
    html_path = static_dir / "index.html"
    if html_path.exists():
        return HTMLResponse(html_path.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>Dashboard loading...</h1>")


@app.get("/api/stats")
async def get_stats():
    """إحصاءات شاملة للنظام"""

    # ── ChromaDB Stats ──
    chroma_stats = {"status": "offline", "collections": [], "total_chunks": 0}
    try:
        client = get_chroma_client()
        collections = client.list_collections()
        chroma_collections = []
        total_chunks = 0
        for col in collections:
            collection = client.get_collection(col.name)
            count = collection.count()
            total_chunks += count
            chroma_collections.append({"name": col.name, "chunks": count})
        chroma_stats = {
            "status": "online",
            "collections": chroma_collections,
            "total_chunks": total_chunks,
            "collection_count": len(chroma_collections)
        }
    except Exception as e:
        chroma_stats["error"] = str(e)

    # ── File Stats ──
    def count_files(directory: Path) -> list:
        if not directory.exists():
            return []
        files = []
        for f in sorted(directory.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
            if f.is_file() and not f.name.startswith("."):
                stat = f.stat()
                files.append({
                    "name": f.name,
                    "size": stat.st_size,
                    "size_kb": round(stat.st_size / 1024, 1),
                    "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                })
        return files

    processed_files = count_files(PROCESSED_DIR)
    incoming_files  = count_files(INCOMING_DIR)
    failed_files    = count_files(FAILED_DIR)

    # ── LoRA Queue Stats ──
    lora_stats = {"total_files": 0, "total_examples": 0}
    if LORA_QUEUE_DIR.exists():
        jsonl_files = list(LORA_QUEUE_DIR.glob("*.jsonl"))
        total_examples = 0
        for jf in jsonl_files:
            try:
                with open(jf, "r", encoding="utf-8") as f:
                    total_examples += sum(1 for line in f if line.strip())
            except Exception:
                pass
        lora_stats = {"total_files": len(jsonl_files), "total_examples": total_examples}

    # ── Services Health ──
    services = {
        "pipeline": safe_get(f"{PIPELINE_URL}/health"),
        "ollama":   safe_get(f"{OLLAMA_URL}/api/tags"),
        "anythingllm": safe_get(f"{ANYTHINGLLM_URL}/api/ping"),
    }

    # ── Ollama Models ──
    ollama_models = []
    if services["ollama"]["ok"]:
        try:
            ollama_models = [m["name"] for m in services["ollama"]["data"].get("models", [])]
        except Exception:
            pass

    return JSONResponse({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "chromadb": chroma_stats,
        "files": {
            "processed": {"count": len(processed_files), "items": processed_files[:20]},
            "incoming":  {"count": len(incoming_files),  "items": incoming_files},
            "failed":    {"count": len(failed_files),    "items": failed_files}
        },
        "lora_queue": lora_stats,
        "services": {
            "pipeline":    {"online": services["pipeline"]["ok"]},
            "ollama":      {"online": services["ollama"]["ok"], "models": ollama_models},
            "chromadb":    {"online": chroma_stats["status"] == "online"},
            "anythingllm": {"online": services["anythingllm"]["ok"]},
        }
    })


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "SaleH Dashboard"}


@app.get("/api/chromadb/search")
async def search_chromadb(q: str, collection: str = "salehsaas_knowledge", n: int = 5):
    """بحث في ChromaDB"""
    try:
        client = get_chroma_client()
        col = client.get_collection(collection)
        results = col.query(query_texts=[q], n_results=min(n, col.count()))
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]
        return {
            "query": q,
            "collection": collection,
            "results": [
                {"text": d[:500], "metadata": m, "distance": round(dist, 4)}
                for d, m, dist in zip(docs, metas, distances)
            ]
        }
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
