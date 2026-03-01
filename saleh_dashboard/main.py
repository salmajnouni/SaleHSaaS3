"""
SaleH SaaS - Dashboard API
واجهة مراقبة النظام + Chat API مع RAG (ChromaDB + Ollama)
"""

import os
import json
import requests
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import chromadb

# ─── إعدادات ─────────────────────────────────────────────────────────────────
CHROMA_HOST     = os.getenv("CHROMA_HOST", "chromadb")
CHROMA_PORT     = int(os.getenv("CHROMA_PORT", 8000))
CHROMA_TOKEN    = os.getenv("CHROMA_TOKEN", "salehsaas-chroma-token")
PIPELINE_URL    = os.getenv("PIPELINE_URL", "http://salehsaas_pipeline:8001")
OLLAMA_URL      = os.getenv("OLLAMA_URL", "http://ollama:11434")
ANYTHINGLLM_URL = os.getenv("ANYTHINGLLM_URL", "http://anythingllm:3001")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text:latest")
CHAT_MODEL      = os.getenv("CHAT_MODEL", "llama3:latest")
PROCESSED_DIR   = Path(os.getenv("PROCESSED_DIR", "/data/processed"))
INCOMING_DIR    = Path(os.getenv("INCOMING_DIR", "/data/incoming"))
FAILED_DIR      = Path(os.getenv("FAILED_DIR", "/data/failed"))
LORA_QUEUE_DIR  = Path(os.getenv("LORA_QUEUE_DIR", "/data/lora_queue"))

# ─── FastAPI App ──────────────────────────────────────────────────────────────
app = FastAPI(title="SaleH SaaS Dashboard", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


# ─── Helpers ──────────────────────────────────────────────────────────────────

def get_chroma_client():
    return chromadb.HttpClient(
        host=CHROMA_HOST,
        port=CHROMA_PORT,
        headers={"Authorization": f"Bearer {CHROMA_TOKEN}"}
    )


def get_ollama_embedding(text: str) -> list:
    """الحصول على embedding من Ollama"""
    response = requests.post(
        f"{OLLAMA_URL}/api/embeddings",
        json={"model": EMBEDDING_MODEL, "prompt": text},
        timeout=60
    )
    response.raise_for_status()
    return response.json()["embedding"]


def safe_get(url: str, timeout: int = 3) -> dict:
    try:
        r = requests.get(url, timeout=timeout)
        return {"ok": r.status_code == 200, "data": r.json() if r.ok else {}}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def count_files(directory: Path) -> list:
    if not directory.exists():
        return []
    files = []
    for f in sorted(directory.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
        if f.is_file() and not f.name.startswith("."):
            stat = f.stat()
            files.append({
                "name": f.name,
                "size_kb": round(stat.st_size / 1024, 1),
                "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            })
    return files


# ─── API Endpoints ────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    html_path = static_dir / "index.html"
    if html_path.exists():
        return HTMLResponse(html_path.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>Dashboard loading...</h1>")


@app.get("/api/stats")
async def get_stats():
    # ChromaDB
    chroma_stats = {"status": "offline", "collections": [], "total_chunks": 0, "collection_count": 0}
    try:
        client = get_chroma_client()
        collections = client.list_collections()
        total_chunks = 0
        col_list = []
        for col in collections:
            c = client.get_collection(col.name)
            count = c.count()
            total_chunks += count
            col_list.append({"name": col.name, "chunks": count})
        chroma_stats = {"status": "online", "collections": col_list,
                        "total_chunks": total_chunks, "collection_count": len(col_list)}
    except Exception as e:
        chroma_stats["error"] = str(e)

    # Files
    processed = count_files(PROCESSED_DIR)
    incoming  = count_files(INCOMING_DIR)
    failed    = count_files(FAILED_DIR)

    # LoRA
    lora_stats = {"total_files": 0, "total_examples": 0}
    if LORA_QUEUE_DIR.exists():
        jsonl_files = list(LORA_QUEUE_DIR.glob("*.jsonl"))
        total_ex = 0
        for jf in jsonl_files:
            try:
                with open(jf, "r", encoding="utf-8") as f:
                    total_ex += sum(1 for line in f if line.strip())
            except Exception:
                pass
        lora_stats = {"total_files": len(jsonl_files), "total_examples": total_ex}

    # Services
    pipeline_ok    = safe_get(f"{PIPELINE_URL}/health")
    ollama_ok      = safe_get(f"{OLLAMA_URL}/api/tags")
    anythingllm_ok = safe_get(f"{ANYTHINGLLM_URL}/api/ping")

    ollama_models = []
    if ollama_ok["ok"]:
        try:
            ollama_models = [m["name"] for m in ollama_ok["data"].get("models", [])]
        except Exception:
            pass

    return JSONResponse({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "chromadb": chroma_stats,
        "files": {
            "processed": {"count": len(processed), "items": processed[:20]},
            "incoming":  {"count": len(incoming),  "items": incoming},
            "failed":    {"count": len(failed),    "items": failed}
        },
        "lora_queue": lora_stats,
        "services": {
            "pipeline":    {"online": pipeline_ok["ok"]},
            "ollama":      {"online": ollama_ok["ok"], "models": ollama_models},
            "chromadb":    {"online": chroma_stats["status"] == "online"},
            "anythingllm": {"online": anythingllm_ok["ok"]},
        }
    })


@app.get("/api/chromadb/search")
async def search_chromadb(q: str, collection: str = "salehsaas_knowledge", n: int = 5):
    """بحث دلالي في ChromaDB باستخدام Ollama embeddings"""
    try:
        # الحصول على embedding من Ollama
        embedding = get_ollama_embedding(q)

        client = get_chroma_client()
        col = client.get_collection(collection)
        count = col.count()
        if count == 0:
            return {"query": q, "results": [], "message": "المجموعة فارغة"}

        results = col.query(
            query_embeddings=[embedding],
            n_results=min(n, count)
        )
        docs      = results.get("documents", [[]])[0]
        metas     = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        return {
            "query": q,
            "collection": collection,
            "results": [
                {
                    "text": d[:600],
                    "metadata": m,
                    "similarity": round((1 - dist) * 100, 1)
                }
                for d, m, dist in zip(docs, metas, distances)
            ]
        }
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


class ChatRequest(BaseModel):
    message: str
    collection: str = "salehsaas_knowledge"
    n_context: int = 3


@app.post("/api/chat")
async def chat(req: ChatRequest):
    """
    Chat API مع RAG:
    1. يبحث في ChromaDB عن الأجزاء الأقرب للسؤال
    2. يُرسلها مع السؤال إلى llama3
    3. يُعيد الإجابة
    """
    try:
        # 1. البحث في ChromaDB
        embedding = get_ollama_embedding(req.message)
        client = get_chroma_client()

        context_text = ""
        try:
            col = client.get_collection(req.collection)
            count = col.count()
            if count > 0:
                results = col.query(
                    query_embeddings=[embedding],
                    n_results=min(req.n_context, count)
                )
                docs = results.get("documents", [[]])[0]
                context_text = "\n\n---\n\n".join(docs)
        except Exception:
            context_text = ""

        # 2. بناء الـ prompt
        if context_text:
            prompt = f"""أنت مساعد ذكي متخصص في تحليل المحتوى وتقييمه.

فيما يلي مقتطفات من قاعدة المعرفة المتعلقة بسؤالك:

{context_text}

---

بناءً على المحتوى أعلاه، أجب على السؤال التالي بشكل مفصل ومنظم:

السؤال: {req.message}

الإجابة:"""
        else:
            prompt = f"""أنت مساعد ذكي. أجب على السؤال التالي:

{req.message}"""

        # 3. إرسال إلى llama3
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": CHAT_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_predict": 1024
                }
            },
            timeout=120
        )
        response.raise_for_status()
        result = response.json()

        return {
            "question": req.message,
            "answer": result.get("response", ""),
            "context_used": len(context_text) > 0,
            "context_chunks": req.n_context if context_text else 0,
            "model": CHAT_MODEL
        }

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "SaleH Dashboard v2.0"}
