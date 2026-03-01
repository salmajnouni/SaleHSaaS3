# Data Pipeline Service

This service is the core of the data ingestion process in SaleH SaaS. It's a FastAPI application responsible for receiving files, processing them, generating embeddings, and storing the results.

## Endpoints

- `POST /process-file/`
  - **Description**: Receives a file, chunks it, generates embeddings via Ollama, and stores it in ChromaDB. It also creates a corresponding entry in the LoRA queue.
  - **Request Body**: `multipart/form-data` with a file upload.
  - **Response**: A JSON object confirming the number of chunks stored and the collection name.

- `GET /health`
  - **Description**: A simple health check endpoint.
  - **Response**: `{"status": "ok"}`

## How it Works

1.  **File Reception**: The service receives a file from the `file_watcher` service.
2.  **Content Extraction**: It uses the `unstructured` library to extract text content from various file formats (PDF, DOCX, TXT, MD).
3.  **Text Churning**: The extracted text is split into smaller, overlapping chunks of 1024 tokens.
4.  **Embedding Generation**: For each chunk, it makes a request to the `salehsaas_ollama` service to generate vector embeddings using the `nomic-embed-text` model.
5.  **Vector Storage**: The chunks and their corresponding vectors are saved into the `salehsaas_knowledge` collection in ChromaDB.
6.  **LoRA Queue**: A JSONL file containing the processed text is added to the `/data/lora_queue` directory, preparing for future fine-tuning tasks.
