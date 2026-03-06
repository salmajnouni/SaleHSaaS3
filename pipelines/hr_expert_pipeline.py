"""
HR Expert Pipeline - خبير الموارد البشرية
==========================================
Pipeline مخصصة لـ Open WebUI تقوم بـ:
1. تمرير الطلبات لنموذج hr-expert مع RAG على سياسات الموارد البشرية
2. حقن سياق نظام العمل السعودي تلقائياً
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
        HR_EXPERT_MODEL_ID: str = "hr-expert"
        ENABLE_HR_CONTEXT: bool = True
        DEFAULT_TEMPERATURE: float = 0.3
        MAX_TOKENS: int = 8192

    def __init__(self):
        self.name = "👥 HR Management Expert"
        self.id = "hr-expert-pipeline"
        self.valves = self.Valves()

    async def on_startup(self):
        print(f"✅ HR Expert Pipeline جاهزة — النموذج: {self.valves.HR_EXPERT_MODEL_ID}")

    async def on_shutdown(self):
        print("⏹️ HR Expert Pipeline أُوقفت")

    def _build_headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.valves.OPENWEBUI_API_KEY:
            headers["Authorization"] = f"Bearer {self.valves.OPENWEBUI_API_KEY}"
        return headers

    def _inject_hr_context(self, messages: List[dict]) -> List[dict]:
        """حقن سياق الموارد البشرية ونظام العمل السعودي"""
        if not self.valves.ENABLE_HR_CONTEXT:
            return messages

        has_system = any(m.get("role") == "system" for m in messages)
        if has_system:
            return messages

        hr_context = {
            "role": "system",
            "content": (
                "أنت \"خبير الموارد البشرية\" في نظام SaleHSaaS، متخصص في إدارة الموارد البشرية وفق نظام العمل السعودي.\n\n"
                "## الحدود القانونية الأساسية (نظام العمل السعودي)\n"
                "- ساعات العمل القصوى: 48 ساعة/أسبوع (36 في رمضان)\n"
                "- الإجازة السنوية: 21 يوماً (أقل من 5 سنوات) / 30 يوماً (5 سنوات فأكثر)\n"
                "- إجازة الأمومة: 10 أسابيع (4 قبل + 6 بعد الولادة)\n"
                "- مكافأة نهاية الخدمة: نصف راتب شهري لكل سنة (أول 5 سنوات) + راتب كامل بعدها\n"
                "- الفصل التعسفي: يستوجب تعويضاً لا يقل عن أجر شهرين عن كل سنة خدمة\n\n"
                "## مجالات خبرتك\n"
                "- **التوظيف والاختيار**: إجراءات التوظيف، المقابلات، التقييم\n"
                "- **إدارة الأداء**: KPIs، تقييمات الأداء، خطط التطوير\n"
                "- **الرواتب والمزايا**: الهياكل الراتبية، البدلات، المكافآت\n"
                "- **التدريب والتطوير**: خطط التدريب، تقييم الاحتياجات\n"
                "- **الامتثال العمالي**: نظام العمل، نظام التأمينات الاجتماعية، السعودة\n"
                "- **إدارة الإجازات**: أنواع الإجازات، الحسابات، الأرصدة\n\n"
                "## قواعد الإجابة\n"
                "1. استند دائماً إلى نظام العمل السعودي عند الإجابة على الأسئلة القانونية\n"
                "2. أجب بالعربية دائماً\n"
                "3. قدّم حسابات دقيقة عند طلب الرواتب أو المكافآت\n"
                "4. راجع قاعدة المعرفة الداخلية لسياسات الشركة المحلية"
            )
        }
        return [hr_context] + messages

    def pipe(
        self,
        user_message: str,
        model_id: str,
        messages: List[dict],
        body: dict
    ) -> Union[str, Generator, Iterator]:
        """المعالج الرئيسي — يمرر الطلب لـ hr-expert في Open WebUI"""

        enriched_messages = self._inject_hr_context(messages)
        stream = body.get("stream", False)

        payload = {
            "model": self.valves.HR_EXPERT_MODEL_ID,
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
