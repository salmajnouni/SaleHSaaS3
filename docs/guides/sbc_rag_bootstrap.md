# SBC RAG Bootstrap Guide

> Runtime note: for current operational facts, defer to `الحقائق التشغيلية الحاكمة - v0.1.md` and `docker-compose.yml` when any detail conflicts with this guide.

This guide starts a controlled ingestion of Saudi Building Code documents into the local RAG stack.

## Scope (Phase 1)
- Build a source register for engineering codes.
- Validate licensing status before ingestion.
- Ingest approved files through existing pipeline.
- Validate retrieval quality with benchmark questions.

If full-text licensed standards are not available yet, use summary-only track:
- `docs/guides/mep_summary_only_rag.md`

## Prerequisites
- Docker stack running (`chromadb`, `tika`, `data_pipeline`, `open_webui`).
- Source files available locally (PDF/DOCX/TXT).
- Approved ingestion scope per source (`full_text`, `summary_only`, `metadata_only`).

## Files Added
- `data/mep_rag/source_register.csv`
- `data/mep_rag/chunk_metadata_schema.json`
- `data/mep_rag/benchmark_questions_mep.json`
- `scripts/mep/prepare_sbc_manifest.py`
- `scripts/mep/register_sbc_sources.py`
- `scripts/mep/stage_sbc_ingestion.py`
- `scripts/mep/auto_discover_sbc.py`
- `scripts/mep/build_summary_cards.py`
- `data/mep_rag/summary_cards_template.csv`

## Step 1: Fill Source Register
Edit `data/mep_rag/source_register.csv` and set:
- `license_status`: `approved`, `restricted`, or `pending`
- `ingest_scope`: `full_text`, `summary_only`, or `metadata_only`
- `local_file_path`: absolute or workspace-relative path of each source file

Only rows with `license_status=approved` and non-empty `local_file_path` are eligible.

Optional fast update command:

```powershell
c:/saleh26/salehsaas/SaleHSaaS3/.venv/Scripts/python.exe scripts/mep/register_sbc_sources.py \
	--sbc501 "D:/codes/SBC-501.pdf" \
	--sbc701 "D:/codes/SBC-701.pdf" \
	--sbc801 "D:/codes/SBC-801.pdf" \
	--edition "2024" \
	--publication-date "2024-01-01" \
	--effective-date "2024-07-01" \
	--approved-by "Saleh"
```

Optional auto-discovery command:

```powershell
c:/saleh26/salehsaas/SaleHSaaS3/.venv/Scripts/python.exe scripts/mep/auto_discover_sbc.py --register-best --edition "2024" --approved-by "Saleh"
```

This writes `data/mep_rag/discovery_report.json` and updates register rows when confident matches are found.

## Step 2: Build Manifest
Run:

```powershell
c:/saleh26/salehsaas/SaleHSaaS3/.venv/Scripts/python.exe scripts/mep/prepare_sbc_manifest.py
```

This generates:
- `data/mep_rag/ingestion_manifest.json`
- `data/mep_rag/ingestion_candidates.txt`

One-command Windows orchestration (optional):

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "scripts/windows/BOOTSTRAP_SBC_RAG.ps1" -Stage -DryRun
```

When paths are ready, run full bootstrap:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "scripts/windows/BOOTSTRAP_SBC_RAG.ps1" \
	-Sbc501 "D:/codes/SBC-501.pdf" \
	-Sbc701 "D:/codes/SBC-701.pdf" \
	-Sbc801 "D:/codes/SBC-801.pdf" \
	-Edition "2024" \
	-PublicationDate "2024-01-01" \
	-EffectiveDate "2024-07-01" \
	-ApprovedBy "Saleh" \
	-Stage
```

## Step 3: Move Approved Files to Ingestion Inbox
Copy files listed in `ingestion_candidates.txt` to:
- `knowledge_inbox/`

Optional automated staging:

```powershell
c:/saleh26/salehsaas/SaleHSaaS3/.venv/Scripts/python.exe scripts/mep/stage_sbc_ingestion.py --dry-run
c:/saleh26/salehsaas/SaleHSaaS3/.venv/Scripts/python.exe scripts/mep/stage_sbc_ingestion.py
```

Recommended filename pattern:
- `SBC-501_<edition>_<short-title>.pdf`
- `SBC-701_<edition>_<short-title>.pdf`
- `SBC-801_<edition>_<short-title>.pdf`

## Step 4: Wait for Auto Ingestion
Existing watcher ingests files from `knowledge_inbox/` automatically.
Track results in:
- `knowledge_processed/` for success
- `knowledge_failed/` for failures

## Step 5: Validate Quality
Use `data/mep_rag/benchmark_questions_mep.json` to run 20 checks.
Acceptance targets:
- Citation precision >= 0.85
- Hallucination rate <= 0.10
- Clause-grounding >= 0.85

## Operational Rules
- Never ingest documents with `license_status` not equal to `approved`.
- Keep source versions explicit in register (`edition`, `effective_date`).
- Re-run manifest generation after any source update.
