"""
title: المجالس الاستشارية
description: استدعاء المجالس الاستشارية الثلاثة (ابتكار، حوكمة تقنية، مراجعة قانونية) مباشرة من الشات.
             يمكن للرئيس استشارة أي مجلس عند الحاجة لرأي متخصص.
author: Saleh Almajnouni
version: 1.0
"""

import json
import urllib.request
import urllib.error
from typing import Any
from pydantic import BaseModel, Field


class Valves(BaseModel):
    n8n_url: str = Field(
        default="http://n8n:5678",
        description="n8n base URL (Docker internal). Use http://n8n:5678 from Docker, http://localhost:5678 from host.",
    )
    timeout: int = Field(
        default=1500,
        description="Request timeout in seconds (councils take 15-20 min with deepseek-r1:32b)",
    )


class Tools:
    """
    المجالس الاستشارية — Advisory Councils Tool

    أداة تتيح للرئيس استدعاء المجالس الثلاثة مباشرة من المحادثة:
    - مجلس الابتكار: لتقييم الأفكار والمشاريع الجديدة
    - مجلس الحوكمة التقنية: لتقييم القرارات التقنية والمعمارية
    - مجلس المراجعة القانونية: لمراجعة التوافق مع الأنظمة السعودية

    كل مجلس يضم خبراء متخصصين يناقشون السؤال ويصدرون قراراً مدعوماً بالأدلة.
    """

    def __init__(self):
        self.valves = Valves()

    def _call_council(self, webhook_path: str, question: str, context: str = "") -> dict:
        """Internal: call a council webhook and return the response."""
        url = f"{self.valves.n8n_url}{webhook_path}"
        payload = {"question": question}
        if context:
            payload["context"] = context
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/json; charset=utf-8"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.valves.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as e:
            return {"error": f"لم أتمكن من الوصول لـ n8n: {e}"}
        except TimeoutError:
            return {"error": "انتهى الوقت المحدد. المجلس يحتاج وقت أطول أو Ollama متوقف."}
        except Exception as e:
            return {"error": f"خطأ: {e}"}

    def _format_response(self, council_name: str, result: dict) -> str:
        """Internal: format council response for chat."""
        if "error" in result:
            return f"❌ فشل استدعاء {council_name}: {result['error']}"

        decision = result.get("decision", "")
        session_id = result.get("sessionId", "")
        status = result.get("status", "")
        sources = result.get("sources", {})
        web = sources.get("web", 0)
        rag = sources.get("rag", 0)

        if not decision:
            return f"⚠️ {council_name} لم يصدر قراراً. الحالة: {status}"

        lines = [
            f"## قرار {council_name}",
            "",
            decision,
            "",
            "---",
            f"📋 جلسة: `{session_id}`" if session_id else "",
            f"🌐 مصادر ويب: {web} | 📚 مصادر RAG: {rag}",
        ]
        return "\n".join(line for line in lines if line is not None)

    async def ask_innovation_council(self, question: str, context: str = "") -> str:
        """
        استشارة مجلس الابتكار — Ask the Innovation Council.
        استخدم هذه الأداة عندما يطلب المستخدم تقييم فكرة جديدة أو مشروع أو ميزة أو استراتيجية.
        المجلس يضم: خبير ريادة أعمال + خبير تقني + خبير استراتيجي.
        ⏱️ يستغرق 15-20 دقيقة.

        :param question: السؤال أو الفكرة المراد تقييمها
        :param context: سياق إضافي اختياري (مثل: المنصة، الصناعة، الميزانية)
        :return: قرار المجلس مع التحليل والتوصيات
        """
        result = self._call_council("/webhook/council-innovation", question, context)
        return self._format_response("مجلس الابتكار", result)

    async def ask_tech_governance_council(self, question: str, context: str = "") -> str:
        """
        استشارة مجلس الحوكمة التقنية — Ask the Tech Governance Council.
        استخدم هذه الأداة عندما يطلب المستخدم تقييم قرار تقني أو معماري أو أمني.
        المجلس يضم: خبير أمن سيبراني + خبير معمارية + خبير جودة + محامي شيطان.
        ⏱️ يستغرق 15-20 دقيقة.

        :param question: السؤال أو القرار التقني المراد تقييمه
        :param context: سياق إضافي اختياري
        :return: قرار المجلس مع التحليل والتوصيات
        """
        result = self._call_council("/webhook/council-tech-governance", question, context)
        return self._format_response("مجلس الحوكمة التقنية", result)

    async def ask_legal_review_council(self, question: str, context: str = "") -> str:
        """
        استشارة مجلس المراجعة القانونية — Ask the Legal Review Council.
        استخدم هذه الأداة عندما يطلب المستخدم مراجعة قانونية أو تحقق من توافق مع الأنظمة السعودية.
        المجلس يضم: محلل مؤيد + محلل معارض + جولتا مرافعة + قاضٍ يصدر الحكم.
        ⏱️ يستغرق 15-20 دقيقة.

        :param question: السؤال أو السياسة المراد مراجعتها قانونياً
        :param context: سياق إضافي اختياري
        :return: حكم المجلس مع التحليل والمرافعات
        """
        result = self._call_council("/webhook/council-legal-review", question, context)
        return self._format_response("مجلس المراجعة القانونية", result)
