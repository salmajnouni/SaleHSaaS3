# MEP Summary-Only RAG (Low-Cost Legal Track)

> Runtime note: this guide depends on the current runtime defaults. If any path, collection, or active service conflicts with another doc, defer to `الحقائق التشغيلية الحاكمة - v0.1.md` and `docker-compose.yml`.

This track enables immediate RAG value when full paid standards are unavailable.

## What It Does
- Uses paraphrased engineering cards, not full copyrighted standards text.
- Enforces citation metadata for every card.
- Allows practical assistant guidance with verification-first behavior.

## Inputs
- `data/mep_rag/summary_cards_template.csv`

## Generator
- `scripts/mep/build_summary_cards.py`
- `scripts/mep/dedupe_summary_cards_chroma.py`
- `scripts/mep/benchmark_summary_retrieval.py`
- `scripts/windows/BOOTSTRAP_MEP_SUMMARY_RAG.ps1`

## Commands

Generate cards only:

```powershell
c:/saleh26/salehsaas/SaleHSaaS3/.venv/Scripts/python.exe scripts/mep/build_summary_cards.py
```

Generate and stage to ingestion inbox:

```powershell
c:/saleh26/salehsaas/SaleHSaaS3/.venv/Scripts/python.exe scripts/mep/build_summary_cards.py --stage
```

Overwrite existing staged files:

```powershell
c:/saleh26/salehsaas/SaleHSaaS3/.venv/Scripts/python.exe scripts/mep/build_summary_cards.py --stage --overwrite
```

One-command Windows runner:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "scripts/windows/BOOTSTRAP_MEP_SUMMARY_RAG.ps1" -Overwrite
```

Deduplicate repeated summary-card chunks in Chroma:

```powershell
c:/saleh26/salehsaas/SaleHSaaS3/.venv/Scripts/python.exe scripts/mep/dedupe_summary_cards_chroma.py --apply
```

Run retrieval benchmark (summary-card subset):

```powershell
c:/saleh26/salehsaas/SaleHSaaS3/.venv/Scripts/python.exe scripts/mep/benchmark_summary_retrieval.py --top-k 10
```

## Output Locations
- Generated markdown cards: `data/mep_rag/generated_cards/`
- Staged for ingestion: `knowledge_inbox/`

## Active Collection Note
- Current watcher path stores ingested chunks in `saleh_knowledge` collection.
- If you intentionally use another collection (for example legacy migration path `saleh_knowledge_qwen3`), update watcher/pipeline routing first and document the override.

## Retrieval Tuning Note
- Current `saleh_knowledge` vectors are 768-dim and align with `nomic-embed-text:latest`.
- Benchmark result on 2026-03-28: pass rate reached 100% at `top_k=10` for MEP summary benchmark.
- For Arabic engineering prompts, use retrieval depth `top_k >= 10` or add a rerank stage.

## Policy Rules
1. Keep card text paraphrased and concise.
2. Always include `citation_ref` and `source_url`.
3. Do not paste verbatim copyrighted clauses.
4. Mark uncertain items with lower confidence and review status `draft`.

## Recommended Workflow
1. Fill `summary_cards_template.csv` with 20-50 high-value cards.
2. Run generator with `--stage`.
3. Let knowledge watcher ingest cards.
4. Run Chroma dedupe to keep one canonical row per summary source.
5. Validate retrieval using benchmark set from `data/mep_rag/benchmark_questions_mep.json`.
