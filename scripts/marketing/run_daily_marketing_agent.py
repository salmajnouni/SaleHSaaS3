#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Run the omnichannel marketing agent with a default Saudi engineering brief."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.social_media.omnichannel_marketing_agent import (
    OmnichannelMarketingAgent,
    load_config,
)


def main() -> None:
    config_path = Path("config/marketing/accounts.json")
    if not config_path.exists():
        raise FileNotFoundError(
            "Missing config/marketing/accounts.json. Copy accounts.example.json to accounts.json first."
        )

    config = load_config(config_path)
    agent = OmnichannelMarketingAgent(config)

    brief = (
        "ركز على مشكلة تأخر المكاتب الهندسية في التحقق من الامتثال للكود السعودي "
        "وكيف يمكن للمساعد الذكي تقليل الوقت والأخطاء في مشاريع HVAC وPlumbing وFire Safety."
    )
    cta = "احجز جلسة تعريف مجانية لمدة 20 دقيقة عبر الإيميل أو لينكدإن."

    campaign = agent.build_daily_campaign(campaign_brief=brief, cta=cta)
    queued_path = agent.save_to_queue(campaign, Path("data/marketing/queue"))
    print(f"Queued campaign file: {queued_path}")


if __name__ == "__main__":
    main()
