#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Generate a month-long campaign queue from predefined briefs."""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.social_media.omnichannel_marketing_agent import (  # noqa: E402
    OmnichannelMarketingAgent,
    load_config,
)


DEFAULT_BRIEFS = [
    "لماذا تتأخر مراجعات الامتثال في مكاتب الهندسة؟",
    "كيف نقلل أخطاء HVAC قبل التسليم النهائي؟",
    "دور المراجع الواضحة في تسريع موافقات المشاريع",
    "كيف يساعد التوثيق المنهجي في تقليل إعادة العمل؟",
    "3 أخطاء شائعة في Plumbing compliance وكيف تتجنبها",
    "كيف ترفع جودة تدقيق Fire Safety داخليا؟",
    "تأثير الوقت الضائع في البحث اليدوي على ربحية المكتب",
    "بناء سير مراجعة امتثال أسرع لفريق صغير",
    "كيف تستخدم الأسئلة الموحدة لتقليل التباين بين المهندسين",
    "فوائد جلسة تقييم سريعة قبل تقديم المخططات",
]


def main() -> None:
    config_path = Path("config/marketing/accounts.json")
    if not config_path.exists():
        raise FileNotFoundError("Missing config/marketing/accounts.json")

    config = load_config(config_path)
    agent = OmnichannelMarketingAgent(config)

    queue_dir = Path("data/marketing/queue")
    queue_dir.mkdir(parents=True, exist_ok=True)

    target_days = 30
    cta = "احجز جلسة تقييم مجانية لمدة 20 دقيقة عبر الإيميل أو لينكدإن."

    for i in range(target_days):
        brief = DEFAULT_BRIEFS[i % len(DEFAULT_BRIEFS)]
        campaign = agent.build_daily_campaign(campaign_brief=brief, cta=cta)
        campaign["plan_day"] = i + 1
        agent.save_to_queue(campaign, queue_dir)

    print(f"Generated {target_days} queued campaigns in {queue_dir}")


if __name__ == "__main__":
    main()
