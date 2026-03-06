"""
Orchestrator Pipeline - المنسق الرئيسي لكل الوكلاء
====================================================
Pipeline مخصصة لـ Open WebUI تقوم بـ:
1. تحليل الطلب وتوجيهه للخبير المناسب تلقائياً
2. تنسيق العمل بين عدة خبراء عند الحاجة
3. الظهور في /v1/models كنقطة دخول موحدة
4. دعم Streaming للردود الطويلة

الخبراء المتاحون:
- n8n-expert-pipeline: خبير أتمتة n8n
- legal-expert-pipeline: خبير الامتثال القانوني
- financial-expert-pipeline: خبير الذكاء المالي
- hr-expert-pipeline: خبير الموارد البشرية
- cybersecurity-expert-pipeline: خبير الأمن السيبراني
- social-media-expert-pipeline: خبير وسائل التواصل
"""
from typing import List, Optional, Generator, Iterator, Union
from pydantic import BaseModel
import requests
import json
import os
import re


class Pipeline:
    class Valves(BaseModel):
        OPENWEBUI_BASE_URL: str = "http://open-webui:8080"
        OPENWEBUI_API_KEY: str = os.getenv("OPENWEBUI_API_KEY", "")
        # نموذج التوجيه (خفيف وسريع)
        ROUTER_MODEL_ID: str = "llama3.1:8b"
        # النموذج الافتراضي عند عدم التعرف
        DEFAULT_EXPERT_MODEL: str = "n8n-expert"
        DEFAULT_TEMPERATURE: float = 0.3
        MAX_TOKENS: int = 8192

    # خريطة الكلمات المفتاحية للخبراء
    EXPERT_KEYWORDS = {
        "n8n-expert": [
            "n8n", "workflow", "أتمتة", "automation", "trigger", "node",
            "webhook", "schedule", "cron", "سير عمل", "مهمة مجدولة",
            "json workflow", "تكامل", "integration"
        ],
        "legal-expert": [
            "قانون", "نظام", "تشريع", "عقد", "امتثال", "مخالفة",
            "نظام العمل", "pdpl", "nca", "جريمة", "محكمة", "دعوى",
            "لائحة", "مرسوم", "حقوق", "واجبات", "legal", "compliance"
        ],
        "financial-expert": [
            "مالي", "محاسبة", "ميزانية", "ربح", "خسارة", "إيرادات",
            "مصروفات", "ضريبة", "vat", "قيمة مضافة", "تدفق نقدي",
            "قوائم مالية", "تحليل مالي", "financial", "accounting"
        ],
        "hr-expert": [
            "موارد بشرية", "موظف", "راتب", "إجازة", "توظيف", "فصل",
            "تقييم أداء", "تدريب", "hr", "human resources", "عمالة",
            "مكافأة نهاية خدمة", "تأمينات", "سعودة"
        ],
        "cybersecurity-expert": [
            "أمن", "سيبراني", "اختراق", "ثغرة", "هجوم", "حماية",
            "تشفير", "جدار حماية", "firewall", "security", "cyber",
            "nca", "iso 27001", "owasp", "siem", "soc"
        ],
        "social-media-expert": [
            "تويتر", "انستغرام", "لينكدإن", "سناب", "تيك توك",
            "محتوى", "منشور", "هاشتاق", "تسويق", "social media",
            "marketing", "content", "إعلان", "متابعون", "تفاعل"
        ]
    }

    def __init__(self):
        self.name = "🎯 SaleHSaaS Orchestrator"
        self.id = "orchestrator-pipeline"
        self.valves = self.Valves()

    async def on_startup(self):
        print("✅ Orchestrator Pipeline جاهزة — المنسق الرئيسي لكل الوكلاء")

    async def on_shutdown(self):
        print("⏹️ Orchestrator Pipeline أُوقفت")

    def _build_headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.valves.OPENWEBUI_API_KEY:
            headers["Authorization"] = f"Bearer {self.valves.OPENWEBUI_API_KEY}"
        return headers

    def _detect_expert(self, user_message: str) -> str:
        """كشف الخبير المناسب بناءً على الكلمات المفتاحية"""
        message_lower = user_message.lower()
        scores = {}

        for expert, keywords in self.EXPERT_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw.lower() in message_lower)
            if score > 0:
                scores[expert] = score

        if scores:
            return max(scores, key=scores.get)

        return self.valves.DEFAULT_EXPERT_MODEL

    def _build_routing_message(self, expert_id: str) -> str:
        """بناء رسالة توضيحية عن التوجيه"""
        expert_names = {
            "n8n-expert": "🔄 خبير أتمتة n8n",
            "legal-expert": "⚖️ خبير الامتثال القانوني",
            "financial-expert": "💰 خبير الذكاء المالي",
            "hr-expert": "👥 خبير الموارد البشرية",
            "cybersecurity-expert": "🛡️ خبير الأمن السيبراني",
            "social-media-expert": "📱 خبير وسائل التواصل",
        }
        return expert_names.get(expert_id, f"🤖 {expert_id}")

    def pipe(
        self,
        user_message: str,
        model_id: str,
        messages: List[dict],
        body: dict
    ) -> Union[str, Generator, Iterator]:
        """المعالج الرئيسي — يوجه الطلب للخبير المناسب"""

        # كشف الخبير المناسب
        target_expert = self._detect_expert(user_message)
        expert_name = self._build_routing_message(target_expert)
        stream = body.get("stream", False)

        # إضافة system message للتوجيه
        routing_system = {
            "role": "system",
            "content": (
                f"أنت المنسق الرئيسي لنظام SaleHSaaS. لقد وجّهت هذا الطلب إلى {expert_name}.\n"
                "أجب بالعربية دائماً وقدّم إجابة شاملة ومفيدة."
            )
        }

        enriched_messages = messages.copy()
        if not any(m.get("role") == "system" for m in enriched_messages):
            enriched_messages = [routing_system] + enriched_messages

        payload = {
            "model": target_expert,
            "messages": enriched_messages,
            "stream": stream,
            "temperature": body.get("temperature", self.valves.DEFAULT_TEMPERATURE),
            "max_tokens": body.get("max_tokens", self.valves.MAX_TOKENS),
        }

        try:
            response = requests.post(
                f"{self.valves.OPENWEBUI_BASE_URL}/api/chat/completions",
                headers=self._build_headers(),
                json=payload,
                timeout=180,
                stream=stream
            )
            response.raise_for_status()

            if stream:
                # إرسال رسالة التوجيه أولاً
                routing_info = f"*تم التوجيه إلى: {expert_name}*\n\n"

                def stream_generator():
                    yield routing_info
                    for line in response.iter_lines():
                        if line:
                            decoded = line.decode("utf-8")
                            if decoded.startswith("data: "):
                                decoded = decoded[6:]
                            if decoded == "[DONE]":
                                break
                            try:
                                chunk = json.loads(decoded)
                                delta = chunk.get("choices", [{}])[0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield content
                            except json.JSONDecodeError:
                                pass
                return stream_generator()
            else:
                data = response.json()
                if "choices" in data and len(data["choices"]) > 0:
                    content = data["choices"][0]["message"]["content"]
                    return f"*تم التوجيه إلى: {expert_name}*\n\n{content}"
                else:
                    return "⚠️ لم يُعد النموذج أي رد."

        except requests.exceptions.ConnectionError:
            return (
                "❌ تعذّر الاتصال بـ Open WebUI.\n"
                f"تحقق من أن الخدمة تعمل على: {self.valves.OPENWEBUI_BASE_URL}"
            )
        except requests.exceptions.Timeout:
            return "⏱️ انتهت مهلة الاتصال (180 ثانية)."
        except Exception as e:
            return f"❌ خطأ غير متوقع: {str(e)}"
