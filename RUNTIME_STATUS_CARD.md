# Runtime Status Card

Updated: 2026-03-30
Scope: current operational truth for this repository.

## Active Runtime (docker-compose.yml)

- `open_webui` (`salehsaas_webui`) -> `http://localhost:3000`
- `postgres` (`salehsaas_postgres`)
- `chromadb` (`salehsaas_chromadb`) -> `http://localhost:8010`
- `pipelines` (`salehsaas_pipelines`) -> `http://localhost:9099`
- `data_pipeline` (`salehsaas_data_pipeline`) -> `http://localhost:8001`
- `knowledge_watcher` (`salehsaas_watcher`)
- `n8n` (`salehsaas_n8n`) -> `http://localhost:5678`
- `tika` (`salehsaas_tika`)
- `searxng` (`salehsaas_searxng`)
- `browserless` (`salehsaas_browser`) -> `http://localhost:3001`
- `open-terminal` (`salehsaas_open-terminal`) -> `http://localhost:8000`

## Cancelled / Not Active

- `mcpo`: cancelled in this project. Do not assume any active MCP endpoint via `mcpo`.
- `Code Server`: not active in current runtime.
- `AnythingLLM`: not active in current runtime.
- `AnythingLLM` evaluation reference: `docs/guides/anythingllm_optional_return_assessment.md`.
- `saleh_dashboard`: legacy/reference path, not an active runtime service.

## Operational Defaults

- Chroma collection: `saleh_knowledge`
- Embedding model: `nomic-embed-text:latest`
- Chroma API mode in active paths: `v1`

## Resolution Order (when docs conflict)

1. `docker-compose.yml`
2. `ARCHITECTURE.md`
3. `الحقائق التشغيلية الحاكمة - v0.1.md`
4. This file (`RUNTIME_STATUS_CARD.md`) as a quick card

## Hard Rule

If a service/path is not in `docker-compose.yml`, do not treat it as active runtime.
