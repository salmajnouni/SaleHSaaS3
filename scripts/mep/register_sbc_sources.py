#!/usr/bin/env python3
"""Update data/mep_rag/source_register.csv for SBC 501/701/801 quickly.

Usage example:
  python scripts/mep/register_sbc_sources.py \
    --sbc501 "D:/codes/SBC-501.pdf" \
    --sbc701 "D:/codes/SBC-701.pdf" \
    --sbc801 "D:/codes/SBC-801.pdf" \
    --edition "2024" \
    --publication-date "2024-01-01" \
    --effective-date "2024-07-01" \
    --approved-by "Saleh"
"""

from __future__ import annotations

import argparse
import csv
from datetime import UTC, datetime
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "data" / "mep_rag" / "source_register.csv"


def _abs_or_rel(raw: str | None) -> str:
    if not raw:
        return ""
    p = Path(raw)
    if p.is_absolute():
        return str(p)
    return str((ROOT / p).resolve())


def _read_rows() -> tuple[List[Dict[str, str]], List[str]]:
    if not REGISTRY.exists():
        raise FileNotFoundError(f"Missing registry: {REGISTRY}")

    with REGISTRY.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = list(reader.fieldnames or [])

    if not fieldnames:
        raise RuntimeError("Registry has no header")

    return rows, fieldnames


def _write_rows(rows: List[Dict[str, str]], fieldnames: List[str]) -> None:
    with REGISTRY.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _update_row(
    row: Dict[str, str],
    path_value: str,
    edition: str,
    publication_date: str,
    effective_date: str,
    approved_by: str,
    source_url: str,
) -> None:
    if path_value:
        row["local_file_path"] = path_value
        row["license_status"] = "approved"
        if row.get("ingest_scope", "").strip().lower() in {"", "pending", "none"}:
            row["ingest_scope"] = "full_text"

    if edition:
        row["edition"] = edition
    if publication_date:
        row["publication_date"] = publication_date
    if effective_date:
        row["effective_date"] = effective_date
    if source_url:
        row["source_url"] = source_url

    if approved_by and path_value:
        row["approval_by"] = approved_by
        row["approval_date"] = datetime.now(UTC).date().isoformat()


def main() -> int:
    parser = argparse.ArgumentParser(description="Register SBC source files into source_register.csv")
    parser.add_argument("--sbc501", help="Path to SBC 501 file")
    parser.add_argument("--sbc701", help="Path to SBC 701 file")
    parser.add_argument("--sbc801", help="Path to SBC 801 file")
    parser.add_argument("--edition", default="", help="Edition label (example: 2024)")
    parser.add_argument("--publication-date", default="", help="YYYY-MM-DD")
    parser.add_argument("--effective-date", default="", help="YYYY-MM-DD")
    parser.add_argument("--approved-by", default="", help="Approver name")
    parser.add_argument("--source-url-501", default="", help="Reference URL for SBC 501")
    parser.add_argument("--source-url-701", default="", help="Reference URL for SBC 701")
    parser.add_argument("--source-url-801", default="", help="Reference URL for SBC 801")
    args = parser.parse_args()

    rows, fieldnames = _read_rows()

    updates = {
        "SBC-501-BASE": (_abs_or_rel(args.sbc501), args.source_url_501),
        "SBC-701-BASE": (_abs_or_rel(args.sbc701), args.source_url_701),
        "SBC-801-BASE": (_abs_or_rel(args.sbc801), args.source_url_801),
    }

    updated_count = 0
    for row in rows:
        sid = (row.get("source_id") or "").strip()
        if sid not in updates:
            continue
        path_value, source_url = updates[sid]
        if not path_value and not args.edition and not args.publication_date and not args.effective_date and not source_url:
            continue

        _update_row(
            row=row,
            path_value=path_value,
            edition=args.edition,
            publication_date=args.publication_date,
            effective_date=args.effective_date,
            approved_by=args.approved_by,
            source_url=source_url,
        )
        updated_count += 1

    _write_rows(rows, fieldnames)

    print(f"Updated rows: {updated_count}")
    print(f"Registry: {REGISTRY}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
