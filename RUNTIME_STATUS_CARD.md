# Runtime Status Card

Updated: 2026-04-06
Scope: current operational truth for this repository.

## Active Runtime (docker-compose.yml)

- `open_webui` (`salehsaas_webui`) -> `http://localhost:3000`
- `postgres` (`salehsaas_postgres`)
- `chromadb` (`salehsaas_chromadb`) -> `http://localhost:8010`
- `pipelines` (`salehsaas_pipelines`) -> `http://localhost:9099`
- `data_pipeline` (`salehsaas_data_pipeline`) -> `http://localhost:8001`
- `knowledge_watcher` (`salehsaas_watcher`)
- `n8n` (`salehsaas_n8n`) -> `http://localhost:5678`
- `task_runners` (`salehsaas_task_runners`) -> internal (n8n external runners)
- `tika` (`salehsaas_tika`)
- `searxng` (`salehsaas_searxng`)

## Optional (profiles — not started by default)

- `open-terminal` (profile: `open-terminal`) -> `http://localhost:8000`
- `browserless` (profile: `browserless`) -> `http://localhost:3001` — disabled 2026-04-06, zero active usage
- `crawl4ai` (profile: `crawl4ai`) -> `http://localhost:11235` — disabled 2026-04-06, zero active usage
- `python_agent` (profile: `python-agent`) — disabled 2026-04-06, docker.sock removed

## Cancelled / Not Active

- `mcpo`: cancelled in this project. Do not assume any active MCP endpoint via `mcpo`.
- `Code Server`: not active in current runtime.
- `AnythingLLM`: not active in current runtime.
- `AnythingLLM` evaluation reference: `docs/guides/anythingllm_optional_return_assessment.md`.
- `saleh_dashboard`: legacy/reference path, not an active runtime service.
- `python_agent`: DISABLED as of 2026-04-06. Placed under `profiles: python-agent`. Do NOT activate unless a real defined purpose exists. docker.sock access removed — was a security risk with no operational value.

## Security Rules (Hard)

- Any container with `docker.sock` must have a documented and active purpose. No exceptions.
- Tokens and secrets must never be hardcoded in Python/PS1 scripts — use `.env` only.
- AI-generated scripts that claim autonomous capabilities (scraping, injection, monitoring) must be reviewed before any execution.
- Archive path for dangerous AI-generated artifacts: `archive/cleanup_20260406/president_scripts/`

## Operational Defaults

- Chroma collection: `saleh_knowledge_qwen3`
- Embedding model: `qwen3-embedding:0.6b` (1024 dims)
- Chroma API mode in active paths: `v1`
- Open WebUI behavior settings (main model, RAG model, web search, locale, signup) are managed from the Open WebUI Admin interface and persisted in `saleh_core_data`.
- `docker-compose.yml` now keeps only infrastructure bindings for Open WebUI (Ollama URL, Pipelines URL/API key, secret key, Tika URL).

## RAG Verification (2026-04-06)

- End-to-end RAG was verified on the live path (`pipelines/saleh_legal_rag.py`)
- Query: `ما هي شروط الفسخ في العقود القانونية السعودية؟`
- Retrieval: `15` chunks (top similarity `0.606`) from `saleh_knowledge_qwen3`
- Context injection: `11253` chars via `inlet()`
- LLM response streamed successfully via `pipe()`
- Journal record: `logs/ops_journal.jsonl` action `rag_e2e_verified`

## Backup Status (Verified 2026-04-06)

- Backup script: `backup.ps1` (creates zip in `backups/`)
- Backup script now appends structured records to: `logs/ops_journal.jsonl`
- Last verified backup files: `backups/20260330_005300.zip`, `backups/auto_backups/` (last: 2026-04-03)
- **WARNING**: n8n workflow "Daily Backup" was NOT calling `backup.ps1` before 2026-04-06. It only performed a ChromaDB HTTP health check. Fixed in `n8n_workflows/daily_health_check.json` — requires manual re-import into n8n.
- n8n "execution success" ≠ actual backup file created. Verification requires parsing `[OK]`/`[FAIL]` from `backup.ps1` stdout.

## Continuous Improvement Log

- Canonical log file: `logs/ops_journal.jsonl` (JSONL, one event per line)
- Manual logging tool: `ops_log.ps1`
- Deviation detector: `ops_detect_deviations.ps1`
- Example manual entry:
	- `./ops_log.ps1 -Category rag -Action webui_test -Status ok -Summary "RAG verified from UI" -Metric "top_score=0.508"`
- Use this log for: incident follow-up, root-cause notes, experiment outcomes, and next-step tracking.

### Deviation Scan (from logs)

- Run: `./ops_detect_deviations.ps1 -SinceHours 168`
- Output report: `logs/deviation_report_latest.json`
- Optional journal append: `./ops_detect_deviations.ps1 -SinceHours 168 -AppendScanEvent`

### Runtime Smoke (real execution check)

- Run: `./ops_runtime_smoke.ps1`
- Report output: `logs/runtime_smoke_latest.json`
- Journal event: `runtime/runtime_smoke` (unless `-SkipJournal` is used)

## Visibility Rule

- No hidden runtime paths are accepted in this project.
- Any live execution path must be visible through the operational truth chain, not only by reading source code manually.
- If a service, workflow, pipeline, tool, or scheduled task affects production behavior and is absent from the visibility layer below, treat that as an operational defect.

### Minimum Visibility Layer

- Active services and current state.
- Optional/disabled services and the explicit reason they are disabled.
- Active execution paths: `pipelines`, loaded Open WebUI tools, and active `n8n` workflows.
- Canonical Chroma collection and embedding model.
- Latest RAG verification, latest benchmark result, and latest deviation scan result.
- Latest impactful entries from `logs/ops_journal.jsonl`.

### Current Source of Truth for Visibility

- Runtime topology: `docker-compose.yml`
- Quick operational card: `RUNTIME_STATUS_CARD.md`
- Governing rules: `الحقائق التشغيلية الحاكمة - v0.1.md`
- Measured event trail: `logs/ops_journal.jsonl`

Any future dashboard or operational UI must surface these same items directly. A polished interface that hides runtime reality is not an acceptable operating surface.

## AI Agent Limitations (Hard Limits)

- The LLM (President) cannot modify system files (`.py`, `.ps1`, `.json`) from chat.
- The LLM cannot add or edit n8n workflow nodes directly — user must import JSON manually via `http://localhost:5678`.
- `executeCommand` node type is NOT in the allowed auto-creation list — cannot automate shell commands via `n8n-workflow` blocks from chat.
- n8n "execution started/success" reflects workflow node completion only — does NOT confirm external operations (file creation, script success).

## Resolution Order (when docs conflict)

1. `docker-compose.yml`
2. `ARCHITECTURE.md`
3. `الحقائق التشغيلية الحاكمة - v0.1.md`
4. This file (`RUNTIME_STATUS_CARD.md`) as a quick card

## Hard Rule

If a service/path is not in `docker-compose.yml`, do not treat it as active runtime.
