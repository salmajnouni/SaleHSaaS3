# SaleH Dashboard Service

This is the main user-facing component of the SaleH SaaS ecosystem. It's a FastAPI application that serves a comprehensive SvelteKit single-page application (SPA) for monitoring, search, and chat.

## Features

- **Real-time Monitoring**: Displays the status of all system services (Pipeline, Ollama, ChromaDB, etc.).
- **Statistics**: Shows key metrics like the number of processed files, chunks in ChromaDB, and LoRA queue size.
- **Smart Chat (RAG)**: A chat interface that allows users to ask questions in natural language. The backend queries ChromaDB for relevant context and uses Ollama (Llama 3) to generate answers.
- **Semantic Search**: A dedicated interface to perform direct semantic searches on the ChromaDB knowledge base.
- **File Browser**: Lists files currently in the `incoming`, `processed`, and `failed` directories.

## API Endpoints

The dashboard provides a rich API for the frontend to consume:

- `GET /api/stats`: System-wide statistics.
- `GET /api/services-status`: Health status of all services.
- `GET /api/chromadb/collections`: Lists ChromaDB collections.
- `GET /api/files`: Lists processed, incoming, and failed files.
- `POST /api/chromadb/search`: Semantic search endpoint.
- `POST /api/chat`: RAG chat endpoint.
