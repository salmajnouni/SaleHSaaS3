import os
import json
import uuid
import logging
import tempfile
import requests as http_requests
from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
import chromadb
from dotenv import load_dotenv

load_dotenv()

# --- Environment Variables ---
CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", 8000))
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "qwen3-embedding:0.6b")
TIKA_URL = os.getenv("TIKA_URL", "http://tika:9998/tika")
LORA_QUEUE_DIR = os.getenv("LORA_QUEUE_DIR", "./lora_queue")
INCOMING_DIR = os.getenv("INCOMING_DIR", "./incoming")

# --- Ensure directories exist ---
os.makedirs(LORA_QUEUE_DIR, exist_ok=True)
os.makedirs(INCOMING_DIR, exist_ok=True)

# --- FastAPI App ---
app = FastAPI(title="SaleHSaaS Data Pipeline API", version="1.0.0")

# --- ChromaDB Client ---
chroma_client = chromadb.HttpClient(
    host=CHROMA_HOST,
    port=CHROMA_PORT,
    settings=chromadb.config.Settings(anonymized_telemetry=False)
)

# --- Ollama Embeddings ---
embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL, base_url=OLLAMA_URL)

# --- Text Splitter (1024 tokens with 200 overlap) ---
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1024,
    chunk_overlap=200,
    length_function=len
)


import re as _re

_VALID_COLLECTION = _re.compile(r"^[a-zA-Z0-9_-]{1,64}$")

@app.post("/process-file/", summary="Process an uploaded file, chunk it, store in ChromaDB and LoRA queue")
async def process_file(file: UploadFile = File(...), collection_name: str = os.getenv("COLLECTION_NAME", "saleh_knowledge_qwen3")):
    """
    Accepts any file (PDF, Word, Excel, TXT, etc.),
    extracts text via Apache Tika, splits into chunks,
    stores them in ChromaDB for RAG, and appends to LoRA queue.
    """
    if not _VALID_COLLECTION.match(collection_name):
        raise HTTPException(status_code=400, detail="Invalid collection name.")
    try:
        # Save the uploaded file temporarily (sanitize filename to prevent path traversal)
        safe_name = os.path.basename(file.filename)
        if not safe_name:
            raise HTTPException(status_code=400, detail="Invalid filename.")
        file_path = os.path.join(INCOMING_DIR, safe_name)
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        # Extract text using Apache Tika
        with open(file_path, "rb") as f:
            tika_response = http_requests.put(
                TIKA_URL,
                data=f,
                headers={"Accept": "text/plain"},
                timeout=120
            )

        if tika_response.status_code != 200 or not tika_response.text.strip():
            os.remove(file_path)
            raise HTTPException(status_code=400, detail="Could not extract any text from the document.")

        extracted_text = tika_response.text.strip()
        documents = [Document(page_content=extracted_text, metadata={"source": file.filename})]

        # Split the document into chunks
        chunks = text_splitter.split_documents(documents)

        if not chunks:
            os.remove(file_path)
            raise HTTPException(status_code=400, detail="Document produced no chunks after splitting.")

        # --- Store in ChromaDB (RAG) ---
        Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            client=chroma_client,
            collection_name=collection_name,
        )

        # --- Add to LoRA Queue (Fine-tuning) ---
        lora_filename = f"{uuid.uuid4()}.jsonl"
        lora_file_path = os.path.join(LORA_QUEUE_DIR, lora_filename)
        with open(lora_file_path, "a", encoding="utf-8") as f:
            for chunk in chunks:
                lora_record = {
                    "text": chunk.page_content,
                    "metadata": chunk.metadata
                }
                f.write(json.dumps(lora_record, ensure_ascii=False) + "\n")

        # Clean up the temporary file
        os.remove(file_path)

        return {
            "status": "success",
            "message": f"Processed {len(chunks)} chunks from '{file.filename}'",
            "collection_name": collection_name,
            "chunks_count": len(chunks),
            "lora_queue_file": lora_filename
        }

    except HTTPException:
        raise
    except Exception as e:
        logging.getLogger(__name__).error(f"process-file error: {e}")
        raise HTTPException(status_code=500, detail="Internal processing error.")


@app.get("/health", summary="Health check")
def health_check():
    return {"status": "ok", "message": "SaleHSaaS Data Pipeline API is running."}


@app.get("/", summary="Root")
def read_root():
    return {"message": "SaleHSaaS Data Pipeline API v1.0 — Use /docs for API documentation."}


# ── Service Logs API ────────────────────────────────────

def _get_pg_conn():
    """Get PostgreSQL connection for log queries."""
    import psycopg2
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "postgres"),
        port=int(os.getenv("POSTGRES_PORT", 5432)),
        dbname=os.getenv("POSTGRES_DB", "salehsaas"),
        user=os.getenv("POSTGRES_USER", "salehsaas"),
        password=os.getenv("POSTGRES_PASSWORD", ""),
    )


@app.get("/logs/recent", summary="Get recent error/warning logs from all containers")
def get_recent_logs(
    minutes: int = Query(default=60, ge=1, le=1440, description="How many minutes back"),
    level: str = Query(default="ERROR", description="Minimum level: ERROR or WARNING"),
    container: str = Query(default="", description="Filter by container name (empty=all)"),
    limit: int = Query(default=50, ge=1, le=500),
):
    """Query recent service logs from PostgreSQL."""
    try:
        conn = _get_pg_conn()
        cur = conn.cursor()

        levels = ["ERROR"] if level.upper() == "ERROR" else ["ERROR", "WARNING"]

        query = """
            SELECT id, container, level, message, log_timestamp, collected_at
            FROM service_logs
            WHERE collected_at > NOW() - INTERVAL '%s minutes'
            AND level = ANY(%s)
        """
        params = [minutes, levels]

        if container:
            query += " AND container = %s"
            params.append(container)

        query += " ORDER BY collected_at DESC LIMIT %s"
        params.append(limit)

        cur.execute(query, params)
        rows = cur.fetchall()

        logs = []
        for row in rows:
            logs.append({
                "id": row[0],
                "container": row[1],
                "level": row[2],
                "message": row[3],
                "log_timestamp": row[4].isoformat() if row[4] else None,
                "collected_at": row[5].isoformat() if row[5] else None,
            })

        # Summary by container
        cur.execute("""
            SELECT container, level, COUNT(*)
            FROM service_logs
            WHERE collected_at > NOW() - INTERVAL '%s minutes'
            AND level = ANY(%s)
            GROUP BY container, level
            ORDER BY COUNT(*) DESC
        """, [minutes, levels])
        summary = {}
        for row in cur.fetchall():
            c = row[0]
            if c not in summary:
                summary[c] = {"errors": 0, "warnings": 0}
            if row[1] == "ERROR":
                summary[c]["errors"] = row[2]
            else:
                summary[c]["warnings"] = row[2]

        cur.close()
        conn.close()

        return {
            "total": len(logs),
            "minutes": minutes,
            "level_filter": level,
            "summary": summary,
            "logs": logs,
        }
    except ImportError:
        raise HTTPException(status_code=500, detail="psycopg2 not installed in this container")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB error: {str(e)[:300]}")


@app.get("/logs/stats", summary="Get log statistics summary")
def get_log_stats():
    """Quick stats: how many errors/warnings per container in last hour."""
    try:
        conn = _get_pg_conn()
        cur = conn.cursor()

        cur.execute("""
            SELECT
                container,
                SUM(CASE WHEN level = 'ERROR' THEN 1 ELSE 0 END) as errors,
                SUM(CASE WHEN level = 'WARNING' THEN 1 ELSE 0 END) as warnings,
                MAX(collected_at) as last_seen
            FROM service_logs
            WHERE collected_at > NOW() - INTERVAL '1 hour'
            GROUP BY container
            ORDER BY errors DESC, warnings DESC
        """)
        rows = cur.fetchall()

        cur.execute("SELECT COUNT(*) FROM service_logs")
        total_all = cur.fetchone()[0]

        stats = []
        for row in rows:
            stats.append({
                "container": row[0],
                "errors_1h": row[1],
                "warnings_1h": row[2],
                "last_seen": row[3].isoformat() if row[3] else None,
            })

        cur.close()
        conn.close()

        return {
            "total_logs_in_db": total_all,
            "containers_with_issues": len(stats),
            "stats": stats,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB error: {str(e)[:300]}")
