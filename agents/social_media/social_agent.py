#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
SaleHSaaS 3.0 - Social Media Management Agent (وكيل إدارة التواصل الاجتماعي)

Generates Arabic content, schedules posts, analyzes engagement, and manages
social media presence - using local AI with no cloud dependency.
"""

import json
from datetime import datetime, timedelta
from typing import Optional


class SocialMediaAgent:
    """
    AI-powered social media management agent.
    Generates Arabic content and manages multi-platform publishing.
    """

    AGENT_NAME = "وكيل إدارة التواصل الاجتماعي"
    AGENT_VERSION = "3.0"

    PLATFORMS = ["تويتر/X", "لينكدإن", "إنستغرام", "فيسبوك", "تيك توك", "سناب شات"]

    CONTENT_TYPES = {
        "تعليمي": "محتوى يشرح مفهوماً أو يقدم معلومة مفيدة",
        "ترويجي": "محتوى يروج لمنتج أو خدمة",
        "إلهامي": "محتوى يحفز ويلهم الجمهور",
        "إخباري": "محتوى يشارك آخر الأخبار والتحديثات",
        "تفاعلي": "محتوى يشجع على التعليق والمشاركة"
    }

    def __init__(self, ollama_url: str = "http://ollama:11434", model: str = "llama3"):
        self.ollama_url = ollama_url
        self.model = model
        self.scheduled_posts = []
        print(f"✅ {self.AGENT_NAME} v{self.AGENT_VERSION} initialized.")

    def _ask_llm(self, prompt: str) -> str:
        """Sends a prompt to the local Ollama LLM."""
        import requests
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False},
                timeout=120
            )
            response.raise_for_status()
            return response.json().get("response", "لا توجد استجابة.")
        except Exception as e:
            return f"❌ خطأ في الاتصال بالنموذج: {e}"

    def generate_content(self, topic: str, platform: str, content_type: str = "تعليمي",
                         tone: str = "احترافي", hashtags_count: int = 5) -> dict:
        """
        Generates Arabic social media content for a given topic.

        Args:
            topic (str): The topic to write about.
            platform (str): Target platform (e.g., 'لينكدإن', 'تويتر/X').
            content_type (str): Type of content (e.g., 'تعليمي', 'ترويجي').
            tone (str): Writing tone (e.g., 'احترافي', 'ودي', 'رسمي').
            hashtags_count (int): Number of hashtags to generate.

        Returns:
            dict: Generated content with post text, hashtags, and metadata.
        """
        print(f"✍️ توليد محتوى {content_type} لـ {platform} حول: {topic}")

        # Platform-specific constraints
        char_limits = {
            "تويتر/X": 280,
            "لينكدإن": 3000,
            "إنستغرام": 2200,
            "فيسبوك": 63206,
            "تيك توك": 2200,
            "سناب شات": 250
        }
        char_limit = char_limits.get(platform, 1000)

        prompt = f"""
أنت خبير في إدارة وسائل التواصل الاجتماعي متخصص في المحتوى العربي.
اكتب منشوراً {content_type} بأسلوب {tone} حول الموضوع التالي:

الموضوع: {topic}
المنصة: {platform}
الحد الأقصى للأحرف: {char_limit}

المطلوب:
1. نص المنشور (لا يتجاوز {char_limit} حرف)
2. {hashtags_count} هاشتاق مناسب
3. أفضل وقت للنشر
4. نصيحة لزيادة التفاعل

أجب بتنسيق JSON كالتالي:
{{
  "post_text": "نص المنشور هنا",
  "hashtags": ["#هاشتاق1", "#هاشتاق2"],
  "best_time": "وقت النشر المقترح",
  "engagement_tip": "نصيحة التفاعل"
}}
"""
        ai_response = self._ask_llm(prompt)

        # Try to parse JSON response
        try:
            # Extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                content_data = json.loads(json_match.group())
            else:
                content_data = {"post_text": ai_response, "hashtags": [], "best_time": "9:00 صباحاً", "engagement_tip": ""}
        except Exception:
            content_data = {"post_text": ai_response, "hashtags": [], "best_time": "9:00 صباحاً", "engagement_tip": ""}

        return {
            "agent": self.AGENT_NAME,
            "timestamp": datetime.now().isoformat(),
            "topic": topic,
            "platform": platform,
            "content_type": content_type,
            "tone": tone,
            "generated_content": content_data
        }

    def schedule_post(self, content: dict, publish_at: datetime) -> dict:
        """
        Schedules a post for future publishing.

        Args:
            content (dict): The generated content to schedule.
            publish_at (datetime): The datetime to publish the post.

        Returns:
            dict: Scheduled post details.
        """
        post = {
            "id": len(self.scheduled_posts) + 1,
            "content": content,
            "scheduled_at": publish_at.isoformat(),
            "status": "مجدول",
            "created_at": datetime.now().isoformat()
        }
        self.scheduled_posts.append(post)
        print(f"📅 تم جدولة المنشور #{post['id']} للنشر في {publish_at.strftime('%Y-%m-%d %H:%M')}")
        return post

    def get_content_calendar(self, days: int = 7) -> list:
        """Returns the content calendar for the next N days."""
        upcoming = []
        now = datetime.now()
        for post in self.scheduled_posts:
            post_time = datetime.fromisoformat(post['scheduled_at'])
            if now <= post_time <= now + timedelta(days=days):
                upcoming.append(post)
        return sorted(upcoming, key=lambda x: x['scheduled_at'])

    def analyze_best_times(self, platform: str) -> dict:
        """Returns the best posting times for a given platform based on research."""
        best_times = {
            "تويتر/X": {"أيام": ["الثلاثاء", "الأربعاء", "الخميس"], "أوقات": ["9:00", "12:00", "18:00"]},
            "لينكدإن": {"أيام": ["الثلاثاء", "الأربعاء", "الخميس"], "أوقات": ["8:00", "12:00", "17:00"]},
            "إنستغرام": {"أيام": ["الاثنين", "الأربعاء", "الجمعة"], "أوقات": ["11:00", "14:00", "19:00"]},
            "فيسبوك": {"أيام": ["الثلاثاء", "الأربعاء", "الجمعة"], "أوقات": ["9:00", "13:00", "16:00"]},
            "تيك توك": {"أيام": ["الثلاثاء", "الخميس", "الجمعة"], "أوقات": ["7:00", "19:00", "21:00"]},
            "سناب شات": {"أيام": ["الجمعة", "السبت", "الأحد"], "أوقات": ["10:00", "20:00", "22:00"]}
        }
        return best_times.get(platform, {"أيام": ["الثلاثاء"], "أوقات": ["9:00"]})


if __name__ == '__main__':
    agent = SocialMediaAgent()
    content = agent.generate_content(
        topic="الذكاء الاصطناعي في الأعمال السعودية",
        platform="لينكدإن",
        content_type="تعليمي",
        tone="احترافي"
    )
    print(json.dumps(content, ensure_ascii=False, indent=2))
