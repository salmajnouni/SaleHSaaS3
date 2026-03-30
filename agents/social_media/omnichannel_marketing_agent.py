#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Omnichannel Marketing Agent for solo founder operations.

This agent prepares channel-specific drafts for:
- LinkedIn
- TikTok
- YouTube
- Email outreach

It does not auto-post by default. It writes approval-ready drafts to disk,
so the owner can review and publish manually or wire approved outputs to n8n.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import requests


@dataclass
class AgentConfig:
    ollama_url: str
    model: str
    owner_name: str
    company_name: str
    offer_name: str
    offer_url: str
    owner_email: str
    linkedin_profile: str
    linkedin_company_page: str
    linktree_url: str


class OmnichannelMarketingAgent:
    """Builds campaign drafts and saves them in a local approval queue."""

    def __init__(self, config: AgentConfig):
        self.config = config

    def _ask_llm(self, prompt: str) -> str:
        try:
            response = requests.post(
                f"{self.config.ollama_url}/api/generate",
                json={"model": self.config.model, "prompt": prompt, "stream": False},
                timeout=180,
            )
            response.raise_for_status()
            return response.json().get("response", "")
        except Exception:
            # Keep the workflow running even when LLM is unavailable.
            return ""

    def _extract_json(self, text: str) -> Dict[str, Any]:
        match = re.search(r"\{[\s\S]*\}", text)
        if not match:
            raise ValueError("Model response did not include JSON object")
        return json.loads(match.group(0))

    def build_daily_campaign(self, campaign_brief: str, cta: str) -> Dict[str, Any]:
        now_iso = datetime.now().isoformat(timespec="seconds")
        prompt = f"""
You are a senior Arabic B2B marketing strategist for Saudi engineering offices.

Business context:
- Brand: {self.config.company_name}
- Founder: {self.config.owner_name}
- Core offer: {self.config.offer_name}
- Offer URL: {self.config.offer_url}
- Contact email: {self.config.owner_email}
- LinkedIn profile: {self.config.linkedin_profile}
- LinkedIn company page: {self.config.linkedin_company_page}
- Link page: {self.config.linktree_url}

Campaign brief:
{campaign_brief}

CTA to use:
{cta}

Create one coherent daily campaign in Arabic with these exact JSON keys:
{{
    "linkedin_post_personal": "120 to 220 words, founder voice, practical value, one CTA",
    "linkedin_post_page": "100 to 180 words, brand voice, clear offer positioning, one CTA",
  "tiktok_script": "Short hook + 3 value bullets + closing CTA (<= 70 seconds)",
  "youtube_short_script": "45 to 60 seconds script with opening hook and CTA",
  "outreach_email_subject": "Compelling B2B subject line",
  "outreach_email_body": "120 to 180 words, personalized style for engineering office manager",
  "hashtags": ["8 to 12 Arabic/English hashtags relevant to engineering and compliance"],
  "target_persona": "One sentence persona",
  "lead_magnet": "One sentence downloadable/free consultation idea",
  "follow_up_message": "A short follow-up message for WhatsApp or LinkedIn DM"
}}

Rules:
- Do not use hype or fake claims.
- Keep it specific to Saudi engineering offices.
- Keep language professional and concise.
- Return JSON only.
"""

        raw = self._ask_llm(prompt)
        parsed: Dict[str, Any]
        try:
            parsed = self._extract_json(raw)
        except Exception:
            parsed = self._fallback_campaign_content(campaign_brief, cta)

        return {
            "generated_at": now_iso,
            "status": "pending_approval",
            "campaign_brief": campaign_brief,
            "cta": cta,
            "channels": {
                "linkedin_personal": parsed.get("linkedin_post_personal", ""),
                "linkedin_page": parsed.get("linkedin_post_page", ""),
                "tiktok": parsed.get("tiktok_script", ""),
                "youtube": parsed.get("youtube_short_script", ""),
                "email_subject": parsed.get("outreach_email_subject", ""),
                "email_body": parsed.get("outreach_email_body", ""),
                "follow_up_message": parsed.get("follow_up_message", ""),
            },
            "meta": {
                "hashtags": parsed.get("hashtags", []),
                "target_persona": parsed.get("target_persona", ""),
                "lead_magnet": parsed.get("lead_magnet", ""),
            },
        }

    def _fallback_campaign_content(self, campaign_brief: str, cta: str) -> Dict[str, Any]:
        short_brief = campaign_brief.strip()
        if len(short_brief) > 180:
            short_brief = short_brief[:180] + "..."

        return {
            "linkedin_post_personal": (
                "تواجه المكاتب الهندسية ضغطا مستمرا في مراجعة متطلبات الكود السعودي، "
                "خصوصا في مسارات HVAC والسباكة والحريق.\n\n"
                "نساعدك في تسريع التحقق ورفع دقة الامتثال عبر مساعد ذكي يقدم إجابات عملية مع مراجع واضحة.\n\n"
                f"محور اليوم: {short_brief}\n\n"
                f"{cta}"
            ),
            "linkedin_post_page": (
                "تقدم منصة SaleHSaaS دعما عمليا للمكاتب الهندسية في تسريع مراجعة الامتثال للكود السعودي "
                "وتحسين جودة التسليم في تخصصات HVAC والسباكة والحريق.\n\n"
                f"موضوع اليوم: {short_brief}\n"
                "نساعد فرق التصميم على تقليل الأخطاء وإظهار المراجع بشكل واضح قبل الاعتماد.\n\n"
                f"{cta}"
            ),
            "tiktok_script": (
                "هوك: لماذا تضيع المكاتب الهندسية ساعات في التحقق من الكود؟\n"
                "1) تحديد المتطلبات بسرعة حسب نوع المشروع\n"
                "2) تقليل أخطاء المراجعة قبل التسليم\n"
                "3) توثيق المراجع لتسهيل الاعتماد\n"
                f"الخاتمة: {cta}"
            ),
            "youtube_short_script": (
                "اليوم بنشرح كيف تقلل وقت التحقق من الامتثال للكود السعودي في أقل من دقيقة. "
                "الخطوة الأولى: اسأل عن المتطلب بدقة. "
                "الخطوة الثانية: راجع المرجع المعروض. "
                "الخطوة الثالثة: طبق النتيجة على مخططك مباشرة. "
                f"إذا تبي تجربة عملية، {cta}"
            ),
            "outreach_email_subject": "تقليل وقت مراجعة الامتثال للكود السعودي في مكتبكم",
            "outreach_email_body": (
                "السلام عليكم،\n\n"
                "أشارككم حلا عمليا يساعد المكتب الهندسي على تسريع التحقق من متطلبات الكود السعودي "
                "في تخصصات HVAC والسباكة والحريق، مع إبراز المراجع بشكل واضح.\n\n"
                "الفكرة الأساسية: تقليل الوقت الضائع في البحث اليدوي، ورفع جودة المراجعة قبل التسليم.\n\n"
                f"{cta}\n\n"
                f"للتواصل: {self.config.owner_email}"
            ),
            "hashtags": [
                "#SaudiEngineering",
                "#SBC",
                "#HVAC",
                "#Plumbing",
                "#FireSafety",
                "#EngineeringOffice",
                "#Compliance",
                "#SaudiArabia",
            ],
            "target_persona": "مدير مكتب هندسي يبحث عن تسريع الامتثال ورفع جودة التسليم.",
            "lead_magnet": "جلسة تقييم مجانية لمدة 20 دقيقة لحالة امتثال مشروع واحد.",
            "follow_up_message": "مرحبا، أرسلت لكم تفاصيل مختصرة. هل يناسبكم موعد 20 دقيقة هذا الأسبوع؟",
        }

    def save_to_queue(self, campaign: Dict[str, Any], queue_dir: Path) -> Path:
        queue_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_file = queue_dir / f"campaign_{ts}.json"
        out_file.write_text(json.dumps(campaign, ensure_ascii=False, indent=2), encoding="utf-8")
        return out_file


def load_config(config_path: Path) -> AgentConfig:
    data = json.loads(config_path.read_text(encoding="utf-8"))
    return AgentConfig(
        ollama_url=data["ollama_url"],
        model=data["model"],
        owner_name=data["owner_name"],
        company_name=data["company_name"],
        offer_name=data["offer_name"],
        offer_url=data["offer_url"],
        owner_email=data["owner_email"],
        linkedin_profile=data["linkedin_profile"],
        linkedin_company_page=data.get("linkedin_company_page", ""),
        linktree_url=data["linktree_url"],
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate one omnichannel campaign draft")
    parser.add_argument("--config", required=True, help="Path to config json")
    parser.add_argument("--brief", required=True, help="Daily campaign brief")
    parser.add_argument("--cta", required=True, help="Call to action text")
    parser.add_argument("--queue", default="data/marketing/queue", help="Output queue directory")
    args = parser.parse_args()

    cfg = load_config(Path(args.config))
    agent = OmnichannelMarketingAgent(cfg)
    campaign = agent.build_daily_campaign(args.brief, args.cta)
    saved = agent.save_to_queue(campaign, Path(args.queue))
    print(f"Campaign queued for approval: {saved}")
