#!/usr/bin/env python3
"""Prepare an ingestion manifest from data/mep_rag/source_register.csv.

Rules:
- include only rows with license_status == approved
- local_file_path must be non-empty and exist
- output machine-readable manifest + human-readable candidates list
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "data" / "mep_rag" / "source_register.csv"
OUT_MANIFEST = ROOT / "data" / "mep_rag" / "ingestion_manifest.json"
OUT_CANDIDATES = ROOT / "data" / "mep_rag" / "ingestion_candidates.txt"


@dataclass
class Candidate:
    source_id: str
    title_ar: str
    title_en: str
    code_family: str
    code_number: str
    edition: str
    ingest_scope: str
    source_url: str
    local_file_path: str


def _resolve_path(raw_path: str) -> Path:
    p = Path(raw_path)
    if p.is_absolute():
        return p
    return (ROOT / p).resolve()


def _load_candidates() -> List[Candidate]:
    if not REGISTRY.exists():
        raise FileNotFoundError(f"Missing registry: {REGISTRY}")

    candidates: List[Candidate] = []

    with REGISTRY.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            license_status = (row.get("license_status") or "").strip().lower()
            local_path_raw = (row.get("local_file_path") or "").strip()
            if license_status != "approved":
                continue
            if not local_path_raw:
                continue

            resolved = _resolve_path(local_path_raw)
            if not resolved.exists():
                continue

            candidates.append(
                Candidate(
                    source_id=(row.get("source_id") or "").strip(),
                    title_ar=(row.get("title_ar") or "").strip(),
                    title_en=(row.get("title_en") or "").strip(),
                    code_family=(row.get("code_family") or "").strip(),
                    code_number=(row.get("code_number") or "").strip(),
                    edition=(row.get("edition") or "").strip(),
                    ingest_scope=(row.get("ingest_scope") or "").strip(),
                    source_url=(row.get("source_url") or "").strip(),
                    local_file_path=str(resolved),
                )
            )

    return candidates


def _write_outputs(candidates: List[Candidate]) -> None:
    OUT_MANIFEST.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "total_candidates": len(candidates),
        "candidates": [asdict(c) for c in candidates],
    }

    OUT_MANIFEST.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    lines = [
        "SBC ingestion candidates",
        f"Total: {len(candidates)}",
        "",
    ]
    for i, c in enumerate(candidates, 1):
        lines.append(f"{i}. {c.source_id} | {c.code_family}-{c.code_number} | {c.local_file_path}")

    OUT_CANDIDATES.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    candidates = _load_candidates()
    _write_outputs(candidates)

    print(f"Manifest written: {OUT_MANIFEST}")
    print(f"Candidates list: {OUT_CANDIDATES}")
    print(f"Eligible sources: {len(candidates)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
