#!/usr/bin/env python3
"""Build summary-only knowledge cards as Markdown files for ingestion.

Input:
- data/mep_rag/summary_cards_template.csv

Output:
- data/mep_rag/generated_cards/*.md
- optionally stage into knowledge_inbox/ (use --stage)

Policy:
- summary/paraphrase only
- includes mandatory citation reference and source URL
- no raw copyrighted long-form text ingestion
"""

from __future__ import annotations

import argparse
import csv
import shutil
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parents[2]
CARDS_CSV = ROOT / "data" / "mep_rag" / "summary_cards_template.csv"
OUT_DIR = ROOT / "data" / "mep_rag" / "generated_cards"
INBOX = ROOT / "knowledge_inbox"

REQUIRED = {
    "card_id",
    "source_id",
    "domain",
    "title_ar",
    "title_en",
    "applicability",
    "key_requirement_paraphrase",
    "citation_ref",
    "source_url",
    "license_scope",
    "review_status",
}


@dataclass
class Card:
    card_id: str
    source_id: str
    domain: str
    title_ar: str
    title_en: str
    applicability: str
    key_requirement_paraphrase: str
    calculation_hint: str
    citation_ref: str
    source_url: str
    confidence: str
    license_scope: str
    review_status: str
    prepared_by: str
    reviewed_by: str
    last_updated: str


def _validate_header(fieldnames: List[str]) -> None:
    missing = REQUIRED - set(fieldnames)
    if missing:
        raise ValueError(f"Missing required CSV columns: {sorted(missing)}")


def _read_cards() -> List[Card]:
    if not CARDS_CSV.exists():
        raise FileNotFoundError(f"Missing cards CSV: {CARDS_CSV}")

    cards: List[Card] = []
    with CARDS_CSV.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        _validate_header(reader.fieldnames or [])
        for row in reader:
            if not (row.get("card_id") or "").strip():
                continue
            cards.append(
                Card(
                    card_id=(row.get("card_id") or "").strip(),
                    source_id=(row.get("source_id") or "").strip(),
                    domain=(row.get("domain") or "").strip(),
                    title_ar=(row.get("title_ar") or "").strip(),
                    title_en=(row.get("title_en") or "").strip(),
                    applicability=(row.get("applicability") or "").strip(),
                    key_requirement_paraphrase=(row.get("key_requirement_paraphrase") or "").strip(),
                    calculation_hint=(row.get("calculation_hint") or "").strip(),
                    citation_ref=(row.get("citation_ref") or "").strip(),
                    source_url=(row.get("source_url") or "").strip(),
                    confidence=(row.get("confidence") or "").strip(),
                    license_scope=(row.get("license_scope") or "").strip(),
                    review_status=(row.get("review_status") or "").strip(),
                    prepared_by=(row.get("prepared_by") or "").strip(),
                    reviewed_by=(row.get("reviewed_by") or "").strip(),
                    last_updated=(row.get("last_updated") or "").strip(),
                )
            )
    return cards


def _slug(text: str) -> str:
    s = "".join(ch if ch.isalnum() else "-" for ch in text)
    s = "-".join(part for part in s.split("-") if part)
    return (s or "card").lower()


def _render(card: Card) -> str:
    generated_at = datetime.now(UTC).isoformat()
    return "\n".join(
        [
            f"# {card.title_ar or card.title_en}",
            "",
            "## Compliance Note",
            "This card is summary-only and must not be treated as verbatim code text.",
            "Always verify against official source documents before final engineering decisions.",
            "",
            "## Card Metadata",
            f"- card_id: {card.card_id}",
            f"- source_id: {card.source_id}",
            f"- domain: {card.domain}",
            f"- license_scope: {card.license_scope}",
            f"- review_status: {card.review_status}",
            f"- confidence: {card.confidence}",
            f"- prepared_by: {card.prepared_by}",
            f"- reviewed_by: {card.reviewed_by}",
            f"- last_updated: {card.last_updated}",
            f"- generated_at: {generated_at}",
            "",
            "## Applicability",
            card.applicability,
            "",
            "## Key Requirement (Paraphrased)",
            card.key_requirement_paraphrase,
            "",
            "## Calculation Hint",
            card.calculation_hint or "N/A",
            "",
            "## Citation",
            f"- reference: {card.citation_ref}",
            f"- source_url: {card.source_url}",
            "",
        ]
    ) + "\n"


def _write_cards(cards: List[Card], stage: bool, overwrite: bool) -> tuple[int, int]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    INBOX.mkdir(parents=True, exist_ok=True)

    generated = 0
    staged = 0

    for card in cards:
        filename = f"summary-card_{_slug(card.card_id)}.md"
        out_path = OUT_DIR / filename
        out_path.write_text(_render(card), encoding="utf-8")
        generated += 1

        if stage:
            inbox_path = INBOX / filename
            if inbox_path.exists() and not overwrite:
                continue
            shutil.copy2(out_path, inbox_path)
            staged += 1

    return generated, staged


def main() -> int:
    parser = argparse.ArgumentParser(description="Build and stage summary-only MEP cards")
    parser.add_argument("--stage", action="store_true", help="Copy generated cards to knowledge_inbox")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing staged files")
    args = parser.parse_args()

    cards = _read_cards()
    generated, staged = _write_cards(cards, stage=args.stage, overwrite=args.overwrite)

    print(f"Cards source: {CARDS_CSV}")
    print(f"Generated cards: {generated} -> {OUT_DIR}")
    if args.stage:
        print(f"Staged to inbox: {staged} -> {INBOX}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
