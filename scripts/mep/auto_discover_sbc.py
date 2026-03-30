#!/usr/bin/env python3
"""Auto-discover likely SBC files on local machine and optionally register them.

Default behavior:
- scan common roots for candidate files
- write report to data/mep_rag/discovery_report.json
- print best candidates for SBC 501/701/801

Optional:
- --register-best to update source_register.csv directly
"""

from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Dict, List, Optional

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "data" / "mep_rag" / "discovery_report.json"

ALLOWED_EXT = {".pdf", ".doc", ".docx"}

PATTERNS = {
    "SBC-501-BASE": [
        r"\b501\b",
        r"mechanical",
        r"sbc\s*501",
        r"ميكانيك",
        r"تكييف",
    ],
    "SBC-701-BASE": [
        r"\b701\b",
        r"plumbing",
        r"sbc\s*701",
        r"سباكة",
        r"صحي",
    ],
    "SBC-801-BASE": [
        r"\b801\b",
        r"fire",
        r"sbc\s*801",
        r"حريق",
        r"إطفاء",
    ],
}

SKIP_DIR_TOKENS = {
    "windows",
    "$recycle.bin",
    "programdata",
    "appdata",
    "node_modules",
    ".git",
    "venv",
    ".venv",
    "docs",
    "guides",
    "knowledge_archive",
    "knowledge_processed",
    "knowledge_failed",
    "saleh_core_data",
}


@dataclass
class Match:
    source_id: str
    path: str
    score: int
    size: int
    modified: str


def _normalize_name(path: Path) -> str:
    return path.name.lower()


def _score_file(name: str, source_id: str) -> int:
    score = 0
    for pat in PATTERNS[source_id]:
        if re.search(pat, name, flags=re.IGNORECASE):
            score += 10

    if "sbc" in name:
        score += 8
    if "code" in name or "الكود" in name:
        score += 6
    if name.endswith(".pdf"):
        score += 4

    # Strongly prefer filenames explicitly containing target code number.
    if source_id == "SBC-501-BASE" and "501" in name:
        score += 20
    if source_id == "SBC-701-BASE" and "701" in name:
        score += 20
    if source_id == "SBC-801-BASE" and "801" in name:
        score += 20

    return score


def _should_skip_dir(dir_name: str) -> bool:
    name = dir_name.lower()
    return any(token in name for token in SKIP_DIR_TOKENS)


def _scan_root(root_path: Path, limit: int) -> List[Path]:
    found: List[Path] = []
    for current_root, dirs, files in os.walk(root_path, topdown=True):
        dirs[:] = [d for d in dirs if not _should_skip_dir(d)]

        for fn in files:
            p = Path(current_root) / fn
            if p.suffix.lower() not in ALLOWED_EXT:
                continue

            name = _normalize_name(p)
            if not any(token in name for token in ["sbc", "501", "701", "801", "code", "كود", "السعود"]):
                continue

            found.append(p)
            if len(found) >= limit:
                return found
    return found


def _discover(roots: List[Path], per_root_limit: int) -> Dict[str, List[Match]]:
    buckets: Dict[str, List[Match]] = {k: [] for k in PATTERNS}

    for root in roots:
        if not root.exists():
            continue
        files = _scan_root(root, limit=per_root_limit)

        for p in files:
            name = _normalize_name(p)
            try:
                stat = p.stat()
                size = stat.st_size
                modified = datetime.fromtimestamp(stat.st_mtime, tz=UTC).isoformat()
            except Exception:
                size = 0
                modified = ""

            for source_id in PATTERNS:
                score = _score_file(name, source_id)
                if score < 20:
                    continue
                buckets[source_id].append(
                    Match(
                        source_id=source_id,
                        path=str(p),
                        score=score,
                        size=size,
                        modified=modified,
                    )
                )

    for key in buckets:
        buckets[key].sort(key=lambda m: (m.score, m.size), reverse=True)
        buckets[key] = buckets[key][:20]

    return buckets


def _write_report(buckets: Dict[str, List[Match]], roots: List[Path]) -> None:
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "roots": [str(r) for r in roots],
        "results": {k: [asdict(m) for m in v] for k, v in buckets.items()},
    }
    REPORT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _pick_best(buckets: Dict[str, List[Match]]) -> Dict[str, Optional[str]]:
    result: Dict[str, Optional[str]] = {}
    for source_id, items in buckets.items():
        result[source_id] = items[0].path if items else None
    return result


def _run_register(best: Dict[str, Optional[str]], args: argparse.Namespace) -> int:
    register_script = ROOT / "scripts" / "mep" / "register_sbc_sources.py"
    cmd = [
        str(ROOT / ".venv" / "Scripts" / "python.exe"),
        str(register_script),
    ]

    if best.get("SBC-501-BASE"):
        cmd += ["--sbc501", str(best["SBC-501-BASE"])]
    if best.get("SBC-701-BASE"):
        cmd += ["--sbc701", str(best["SBC-701-BASE"])]
    if best.get("SBC-801-BASE"):
        cmd += ["--sbc801", str(best["SBC-801-BASE"])]

    if args.edition:
        cmd += ["--edition", args.edition]
    if args.publication_date:
        cmd += ["--publication-date", args.publication_date]
    if args.effective_date:
        cmd += ["--effective-date", args.effective_date]
    if args.approved_by:
        cmd += ["--approved-by", args.approved_by]

    import subprocess

    completed = subprocess.run(cmd, cwd=str(ROOT), check=False)
    return int(completed.returncode)


def main() -> int:
    parser = argparse.ArgumentParser(description="Auto-discover SBC sources and optionally register best matches")
    parser.add_argument("--roots", nargs="*", default=[], help="Custom roots to scan")
    parser.add_argument("--per-root-limit", type=int, default=600, help="Maximum candidate files to collect per root")
    parser.add_argument("--register-best", action="store_true", help="Register best match for each SBC row")
    parser.add_argument("--edition", default="", help="Edition label for register update")
    parser.add_argument("--publication-date", default="", help="YYYY-MM-DD")
    parser.add_argument("--effective-date", default="", help="YYYY-MM-DD")
    parser.add_argument("--approved-by", default="", help="Approver name")
    args = parser.parse_args()

    if args.roots:
        roots = [Path(r) for r in args.roots]
    else:
        user = Path.home()
        roots = [
            user / "Downloads",
            user / "Documents",
            user / "Desktop",
            Path("D:/"),
            ROOT,
        ]

    buckets = _discover(roots=roots, per_root_limit=args.per_root_limit)
    _write_report(buckets, roots)

    best = _pick_best(buckets)

    print(f"Discovery report: {REPORT}")
    for sid in ["SBC-501-BASE", "SBC-701-BASE", "SBC-801-BASE"]:
        picked = best.get(sid)
        print(f"{sid}: {picked if picked else 'NOT FOUND'}")

    if args.register_best:
        rc = _run_register(best, args)
        if rc != 0:
            return rc

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
