"""
Financial Expert Pipeline - خبير الذكاء المالي
================================================
Pipeline مخصصة لـ Open WebUI تقوم بـ:
1. تمرير الطلبات لنموذج financial-expert مع RAG على البيانات المالية
2. حقن سياق التحليل المالي والمحاسبي تلقائياً
3. الظهور في /v1/models لاستخدامه من n8n وأي تطبيق
4. دعم Streaming للردود الطويلة
"""
from typing import List, Optional, Generator, Iterator, Union
from pydantic import BaseModel
import requests
import json
import os


class Pipeline:
    class Valves(BaseModel):
        OPENWEBUI_BASE_URL: str = "http://open-webui:8080"
        OPENWEBUI_API_KEY: str = os.getenv("OPENWEBUI_API_KEY", "")
        FINANCIAL_EXPERT_MODEL_ID: str = "financial-expert"
        ENABLE_FINANCIAL_CONTEXT: bool = True
        DEFAULT_TEMPERATURE: float = 0.2
        MAX_TOKENS: int = 8192

    def __init__(self):
        self.name = "💰 Financial Intelligence Expert"
        self.id = "financial-expert-pipeline"
        self.valves = self.Valves()

    async def on_startup(self):
        print(f"✅ Financial Expert Pipeline جاهزة — النموذج: {self.valves.FINANCIAL_EXPERT_MODEL_ID}")

    async def on_shutdown(self):
        print("⏹️ Financial Expert Pipeline أُوقفت")

    def _build_headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.valves.OPENWEBUI_API_KEY:
            headers["Authorization"] = f"Bearer {self.valves.OPENWEBUI_API_KEY}"
        return headers

    def _inject_financial_context(self, messages: List[dict]) -> List[dict]:
        """حقن سياق التحليل المالي"""
        if not self.valves.ENABLE_FINANCIAL_CONTEXT:
            return messages

        has_system = any(m.get("role") == "system" for m in messages)
        if has_system:
            return messages

        financial_context = {
            "role": "system",
            "content": (
                "أنت \"خبير الذكاء المالي\" في نظام SaleHSaaS، متخصص في التحليل المالي والمحاسبي.\n\n"
                "## مجالات خبرتك\n"
                "- **التحليل المالي**: قراءة القوائم المالية، نسب السيولة، الربحية، الكفاءة\n"
                "- **المحاسبة السعودية**: المعايير المحاسبية السعودية (SOCPA)، ضريبة القيمة المضافة (VAT)\n"
                "- **إدارة التدفق النقدي**: التنبؤ، تحليل الفجوات، تحسين رأس المال العامل\n"
                "- **الميزانية والتخطيط**: إعداد الميزانيات، تحليل الانحرافات، التخطيط المالي\n"
                "- **كشف الشذوذات**: تحديد الأنماط غير الطبيعية في البيانات المالية\n"
                "- **التقارير المالية**: إعداد التقارير التنفيذية والتفصيلية\n"
                "- **ضريبة القيمة المضافة (VAT)**: الحسابات، الإقرارات، الامتثال لهيئة الزكاة والضريبة\n\n"
                "## قواعد الإجابة\n"
                "1. استخدم الأرقام والإحصاءات لدعم تحليلاتك\n"
                "2. قدّم التوصيات بشكل واضح ومرتب بالأولوية\n"
                "3. أجب بالعربية دائماً مع استخدام المصطلحات المالية الصحيحة\n"
                "4. عند طلب تقرير: استخدم هيكلاً منظماً (الملخص التنفيذي، التحليل، التوصيات)\n"
                "5. نبّه على المخاطر المالية المحتملة في أي تحليل\n"
                "6. راجع قاعدة المعرفة الداخلية للبيانات المالية المحلية\n\n"
                "## بيئة العمل\n"
                "- قاعدة البيانات: PostgreSQL (salehsaas_postgres)\n"
                "- API المالي: http://file_api:8765/\n"
                "- n8n للأتمتة: http://n8n:5678/api/v1/"
            )
        }
        return [financial_context] + messages

    def pipe(
        self,
        user_message: str,
        model_id: str,
        messages: List[dict],
        body: dict
    ) -> Union[str, Generator, Iterator]:
        """المعالج الرئيسي — يمرر الطلب لـ financial-expert في Open WebUI"""

        enriched_messages = self._inject_financial_context(messages)
        stream = body.get("stream", False)

        payload = {
            "model": self.valves.FINANCIAL_EXPERT_MODEL_ID,
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
                def stream_generator():
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
                    return data["choices"][0]["message"]["content"]
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
