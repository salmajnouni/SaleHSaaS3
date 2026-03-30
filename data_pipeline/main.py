import os
import json
import uuid
import tempfile
import requests as http_requests
from fastapi import FastAPI, UploadFile, File, HTTPException
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
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text:latest")
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


@app.post("/process-file/", summary="Process an uploaded file, chunk it, store in ChromaDB and LoRA queue")
async def process_file(file: UploadFile = File(...), collection_name: str = "saleh_knowledge"):
    """
    Accepts any file (PDF, Word, Excel, TXT, etc.),
    extracts text via Apache Tika, splits into chunks,
    stores them in ChromaDB for RAG, and appends to LoRA queue.
    """
    try:
        # Save the uploaded file temporarily
        file_path = os.path.join(INCOMING_DIR, file.filename)
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
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health", summary="Health check")
def health_check():
    return {"status": "ok", "message": "SaleHSaaS Data Pipeline API is running."}


@app.get("/", summary="Root")
def read_root():
    return {"message": "SaleHSaaS Data Pipeline API v1.0 — Use /docs for API documentation."}
