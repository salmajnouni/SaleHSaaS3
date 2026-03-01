## 🕋 System Services - خدمات النظام

This document provides a detailed overview of all services running within the SaleH SaaS Docker ecosystem.

| Service Name | Container Name | Port (Host:Container) | Description (الوصف) |
| :--- | :--- | :--- | :--- |
| **SaleH Dashboard** | `salehsaas_dashboard` | `8000:8000` | **(لوحة المراقبة)** The main web interface for monitoring, chat (RAG), and search. | 
| **Data Pipeline** | `salehsaas_pipeline` | `8001:8001` | **(خط أنابيب البيانات)** API for processing files, generating embeddings, and storing data in ChromaDB. | 
| **File Watcher** | `salehsaas_watcher` | - | **(مراقب الملفات)** A background service that watches the `incoming` folder and triggers the data pipeline. | 
| **ChromaDB** | `salehsaas_chromadb` | `8010:8000` | **(قاعدة البيانات المتجهية)** The vector database used for storing document chunks and enabling semantic search. | 
| **Ollama** | `salehsaas_ollama` | `11434:11434` | **(محرك الذكاء الاصطناعي)** Runs the local LLMs (Llama 3) and embedding models (nomic-embed-text). | 
| **AnythingLLM** | `salehsaas_anythingllm` | `3002:3001` | **(واجهة بديلة)** An alternative UI for interacting with documents and LLMs (optional). | 

### API Endpoints

#### Data Pipeline (`http://localhost:8001`)

- `POST /process-file/`: Processes a single uploaded file.
- `GET /health`: Checks the health of the pipeline service.

#### SaleH Dashboard (`http://localhost:8000`)

- `GET /api/stats`: Retrieves system-wide statistics.
- `GET /api/services-status`: Checks the health of all dependent services.
- `GET /api/chromadb/collections`: Lists all collections in ChromaDB.
- `GET /api/files`: Lists all files in the `incoming`, `processed`, and `failed` directories.
- `POST /api/chromadb/search`: Performs a semantic search in the `salehsaas_knowledge` collection.
- `POST /api/chat`: The main RAG endpoint for the smart chat interface.
