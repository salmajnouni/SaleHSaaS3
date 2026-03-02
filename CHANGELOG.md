# Changelog

All notable changes to SaleH SaaS are documented in this file.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [4.1.3] - 2026-03-02

### Fixed
- **SearXNG radio_browser (final fix)**: Replaced `disabled: true` approach with `use_default_settings.engines.remove` directive. This is the correct SearXNG API to prevent engines from loading entirely - they are removed before initialization, not just flagged as disabled. Eliminates `socket.herror: No address associated with name` crash permanently.

---

## [4.1.2] - 2026-03-02

### Fixed
- **n8n crash**: Removed `N8N_RUNNERS_MODE=external` which caused fatal error `Missing auth token`. n8n now runs in default internal mode (JS runner only). Python runner warning is informational only and does not affect functionality.
- **SearXNG radio_browser**: Added explicit `engine: radio_browser` field alongside `disabled: true` to ensure SearXNG correctly matches and disables the engine before initialization.

---

## [4.1.1] - 2026-03-02

### Fixed
- **Open WebUI CORS**: Replaced `CORS_ALLOW_ORIGIN` with correct `WEBUI_URL` variable that Open WebUI actually reads for allowed origins. Eliminates `http://localhost:3000 is not an accepted origin` error.
- **SearXNG radio_browser**: Changed strategy from `keep_only` to explicit `disabled: true` per engine. Eliminates `socket.herror: No address associated with name` crash on startup.
- **n8n Python runner**: Added `N8N_RUNNERS_MODE=external` to suppress `Failed to start Python task runner in internal mode` warning.

---

## [4.1.0] - 2026-03-02

### Fixed
- **SearXNG limiter.toml**: Created `config/searxng/limiter.toml` to resolve startup warning. Configured to allow all Docker network IPs (172.20.0.0/16).
- **SearXNG engines**: Updated `settings.yml` to use `keep_only` strategy, disabling failed engines (ahmia, torch, radio_browser) and keeping only stable ones (google, bing, duckduckgo, wikipedia, brave).
- **Open WebUI CORS**: Replaced wildcard `CORS_ALLOW_ORIGIN=*` with explicit `http://localhost:3000,http://127.0.0.1:3000`.
- **Open WebUI USER_AGENT**: Added `USER_AGENT` environment variable to identify requests from langchain.
- **n8n deprecation**: Removed deprecated `N8N_RUNNERS_ENABLED=true` variable (no longer needed in n8n v2.9+).

---

## [4.0.0] - 2026-03-02

### Added
- **Dockerfile.tika**: Custom Tika image with Microsoft TrueType core fonts (Arial, Times New Roman, Helvetica, Courier New). Eliminates all `Using fallback font LiberationSans` PDFBox warnings.
- **n8n_builder MCP Tool** (`tools/mcp/n8n_builder.py`): 10-function MCP tool enabling AI models to create, manage, activate, and execute n8n workflows from natural language chat.
- **n8n Public API**: Enabled `N8N_PUBLIC_API_DISABLED=false` and configured `N8N_API_KEY` for programmatic workflow management.
- **Knowledge Watcher v3.0** (`services/knowledge_watcher/watcher.py`): Professional document ingestion pipeline with automatic monitoring, Tika extraction, Ollama embeddings (300s timeout), ChromaDB v2 storage, and date-based archival.
- **mcpo config** (`config/mcpo/config.json`): Three registered MCP tools: `ollama_model_builder`, `saleh_legal_rag`, `n8n_builder`.

### Fixed
- **ChromaDB v2 API**: Migrated from deprecated v1 to full v2 path `/api/v2/tenants/default_tenant/databases/default_database/`.
- **ChromaDB UUID addressing**: Collection add operations now use UUID-based endpoint.
- **Ollama timeout**: Increased to 300 seconds for large document chunks.
- **PowerShell encoding**: All log messages in English to prevent Unicode issues on Windows.
- **File re-queue**: Crash-proof using copy+delete instead of move.

### Changed
- **docker-compose.yml**: `tika` service builds from `Dockerfile.tika`, image tagged `salehsaas-tika-fonts:latest`.
- **Knowledge Watcher**: Removed `IGNORE_FILENAMES` — inbox processes all files by design.
- **Documentation**: Consolidated knowledge watcher docs into `docs/guides/knowledge_watcher.md`.

---

## [3.0.0] - 2026-03-01

### Added
- **MCP Setup Guide** (`MCP_SETUP_GUIDE.md`): Complete guide for configuring MCP tools in Open WebUI.
- **saleh_legal_rag MCP Tool**: Semantic search over ingested legal documents.
- **ollama_model_builder MCP Tool**: Manage Ollama models from chat.
- **mcpo service**: MCP-to-OpenAPI proxy at port `8020`.
- **n8n workflows folder** (`n8n/workflows/`): Pre-built workflow templates.
- **Pipelines**: `saleh_legal_pipeline.py` and `saleh_legal_rag.py` for RAG-enhanced processing.
- **Legal Glossary**: Saudi legal terminology database in `saleh_brain/glossary/`.

### Changed
- Architecture expanded to 10 services.
- PostgreSQL added as persistent backend for n8n.

---

## [2.0.0] - 2026-03-01

### Added
- **Smart Chat API**: Full RAG pipeline with Llama 3 and ChromaDB.
- **Dashboard v2.0**: New UI with 4 tabs (Overview, Chat, Search, Files).
- **Ollama Embeddings Search**: Uses `nomic-embed-text` via Ollama.

### Changed
- Dashboard port changed from `8088` to `8000`.
- Improved logging in `file_watcher`.

---

## [1.0.0] - 2026-03-01

### Added
- **Initial System**: Data Pipeline, File Watcher, ChromaDB, Ollama, and AnythingLLM.
- **Dashboard v1.0**: Basic monitoring dashboard.
- **File Watcher Service**: Automated file processing from the `incoming` folder.
- **Data Pipeline**: Initial version for processing and storing documents.
