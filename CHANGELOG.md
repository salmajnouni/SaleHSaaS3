# Changelog

All notable changes to this project will be documented in this file.

## [2.0.0] - 2026-03-01

### Added
- **Smart Chat API**: Full RAG pipeline with Llama 3 and ChromaDB.
- **Dashboard v2.0**: New UI with 4 tabs (Overview, Chat, Search, Files).
- **Ollama Embeddings Search**: Search now uses `nomic-embed-text` via Ollama, removing the ONNX dependency.

### Changed
- Dashboard port changed from `8088` to `8000` for simplicity.
- Improved logging in `file_watcher` to show chunk count and collection name.

## [1.0.0] - 2026-03-01

### Added
- **Initial System**: Data Pipeline, File Watcher, ChromaDB, Ollama, and AnythingLLM.
- **Dashboard v1.0**: Basic monitoring dashboard.
- **File Watcher Service**: Automated file processing from the `incoming` folder.
- **Data Pipeline**: Initial version for processing and storing documents.
