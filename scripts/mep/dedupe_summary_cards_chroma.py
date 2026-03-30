"""Deduplicate summary-card entries in Chroma by metadata.source.

Policy:
- Only process rows where metadata.source contains "summary-card_".
- Keep one row per source: longest document wins.
- If lengths tie, keep lexicographically smallest id for determinism.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

import requests


DEFAULT_BASE_URL = "http://localhost:8010/api/v1"


@dataclass
class SummaryRow:
    row_id: str
    source: str
    doc_len: int


def _get_collection_id(base_url: str, collection_name: str) -> str:
    resp = requests.get(f"{base_url}/collections", timeout=30)
    resp.raise_for_status()
    cols = resp.json()
    name_to_id = {c.get("name"): c.get("id") for c in cols}
    cid = name_to_id.get(collection_name)
    if not cid:
        raise RuntimeError(
            f"Collection '{collection_name}' not found. Available: {list(name_to_id.keys())}"
        )
    return cid


def _fetch_summary_rows(base_url: str, collection_id: str) -> list[SummaryRow]:
    count_resp = requests.get(f"{base_url}/collections/{collection_id}/count", timeout=30)
    count_resp.raise_for_status()
    total_count = count_resp.json()

    get_resp = requests.post(
        f"{base_url}/collections/{collection_id}/get",
        json={"include": ["documents", "metadatas"], "limit": total_count},
        timeout=120,
    )
    get_resp.raise_for_status()
    payload = get_resp.json()

    ids = payload.get("ids", [])
    docs = payload.get("documents", [])
    metas = payload.get("metadatas", [])

    rows: list[SummaryRow] = []
    for row_id, doc, meta in zip(ids, docs, metas):
        if not isinstance(meta, dict):
            continue
        source = str(meta.get("source", ""))
        if "summary-card_" not in source:
            continue
        rows.append(SummaryRow(row_id=row_id, source=source, doc_len=len(doc or "")))
    return rows


def _compute_delete_plan(rows: list[SummaryRow]) -> tuple[dict[str, str], list[str], dict[str, Any]]:
    by_source: dict[str, list[SummaryRow]] = defaultdict(list)
    for row in rows:
        by_source[row.source].append(row)

    keep_by_source: dict[str, str] = {}
    delete_ids: list[str] = []
    duplicate_sources: dict[str, Any] = {}

    for source, source_rows in sorted(by_source.items()):
        if len(source_rows) == 1:
            keep_by_source[source] = source_rows[0].row_id
            continue

        # Keep the row with longest document for better retrieval context.
        winner = sorted(source_rows, key=lambda r: (-r.doc_len, r.row_id))[0]
        keep_by_source[source] = winner.row_id

        losers = [r for r in source_rows if r.row_id != winner.row_id]
        delete_ids.extend(r.row_id for r in losers)
        duplicate_sources[source] = {
            "keep_id": winner.row_id,
            "keep_doc_len": winner.doc_len,
            "delete": [{"id": r.row_id, "doc_len": r.doc_len} for r in losers],
        }

    stats = {
        "summary_total_rows": len(rows),
        "summary_unique_sources": len(by_source),
        "duplicate_source_count": sum(1 for v in by_source.values() if len(v) > 1),
        "rows_to_delete": len(delete_ids),
        "duplicate_sources": duplicate_sources,
    }
    return keep_by_source, delete_ids, stats


def _delete_rows(base_url: str, collection_id: str, ids: list[str]) -> None:
    if not ids:
        return
    resp = requests.post(
        f"{base_url}/collections/{collection_id}/delete",
        json={"ids": ids},
        timeout=60,
    )
    resp.raise_for_status()


def main() -> int:
    parser = argparse.ArgumentParser(description="Deduplicate summary-card chunks in Chroma")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--collection", default="saleh_knowledge")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply deletion plan. Without this flag, the script runs in dry-run mode.",
    )
    args = parser.parse_args()

    collection_id = _get_collection_id(args.base_url, args.collection)
    rows = _fetch_summary_rows(args.base_url, collection_id)
    _, delete_ids, stats = _compute_delete_plan(rows)

    output: dict[str, Any] = {
        "mode": "apply" if args.apply else "dry_run",
        "base_url": args.base_url,
        "collection": args.collection,
        "collection_id": collection_id,
        **stats,
    }

    if args.apply and delete_ids:
        _delete_rows(args.base_url, collection_id, delete_ids)
        output["deleted_ids"] = delete_ids

    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
