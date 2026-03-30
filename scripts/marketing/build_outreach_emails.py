#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Build personalized outreach email drafts from latest queued campaign + leads.csv."""

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List


def load_latest_campaign(queue_dir: Path) -> Dict:
    files = sorted(queue_dir.glob("campaign_*.json"))
    if not files:
        raise FileNotFoundError("No campaign files found in queue")
    latest = files[-1]
    return json.loads(latest.read_text(encoding="utf-8"))


def load_leads(leads_csv: Path) -> List[Dict[str, str]]:
    with leads_csv.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def personalize_email(base_body: str, lead: Dict[str, str]) -> str:
    contact = lead.get("contact_name", "") or "الأستاذ/الأستاذة"
    company = lead.get("company_name", "مكتبكم الكريم")
    city = lead.get("city", "السعودية")

    intro = (
        f"السلام عليكم {contact}،\n\n"
        f"أتواصل معكم بخصوص دعم أعمال {company} في {city} "
        "لتسريع مراجعة الامتثال للكود السعودي.\n\n"
    )

    return intro + base_body


def main() -> None:
    queue_dir = Path("data/marketing/queue")
    leads_csv = Path("data/marketing/leads.csv")
    out_dir = Path("data/marketing/outreach")
    out_dir.mkdir(parents=True, exist_ok=True)

    campaign = load_latest_campaign(queue_dir)
    leads = load_leads(leads_csv)

    base_subject = campaign["channels"]["email_subject"]
    base_body = campaign["channels"]["email_body"]

    drafts = []
    for lead in leads:
        if (lead.get("status", "").strip().lower() or "new") in {"closed", "won", "lost", "do_not_contact"}:
            continue

        email = (lead.get("email") or "").strip()
        if not email:
            continue

        drafts.append(
            {
                "to": email,
                "subject": base_subject,
                "body": personalize_email(base_body, lead),
                "company_name": lead.get("company_name", ""),
                "contact_name": lead.get("contact_name", ""),
                "status": "pending_approval",
            }
        )

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = out_dir / f"email_drafts_{ts}.json"
    out_file.write_text(json.dumps(drafts, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Drafted {len(drafts)} outreach emails: {out_file}")


if __name__ == "__main__":
    main()
