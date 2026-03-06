"""
Legal Expert Pipeline - خبير الامتثال القانوني السعودي
=======================================================
Pipeline مخصصة لـ Open WebUI تقوم بـ:
1. تمرير الطلبات لنموذج legal-expert مع RAG على الوثائق القانونية السعودية
2. حقن سياق الأنظمة والتشريعات السعودية تلقائياً
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
        LEGAL_EXPERT_MODEL_ID: str = "legal-expert"
        ENABLE_LEGAL_CONTEXT: bool = True
        DEFAULT_TEMPERATURE: float = 0.2
        MAX_TOKENS: int = 8192

    def __init__(self):
        self.name = "⚖️ Legal Compliance Expert"
        self.id = "legal-expert-pipeline"
        self.valves = self.Valves()

    async def on_startup(self):
        print(f"✅ Legal Expert Pipeline جاهزة — النموذج: {self.valves.LEGAL_EXPERT_MODEL_ID}")

    async def on_shutdown(self):
        print("⏹️ Legal Expert Pipeline أُوقفت")

    def _build_headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.valves.OPENWEBUI_API_KEY:
            headers["Authorization"] = f"Bearer {self.valves.OPENWEBUI_API_KEY}"
        return headers

    def _inject_legal_context(self, messages: List[dict]) -> List[dict]:
        """حقن سياق الأنظمة القانونية السعودية"""
        if not self.valves.ENABLE_LEGAL_CONTEXT:
            return messages

        has_system = any(m.get("role") == "system" for m in messages)
        if has_system:
            return messages

        legal_context = {
            "role": "system",
            "content": (
                "أنت \"خبير الامتثال القانوني\" في نظام SaleHSaaS، متخصص في الأنظمة والتشريعات السعودية.\n\n"
                "## مجالات خبرتك\n"
                "- **نظام العمل السعودي**: المرسوم الملكي م/51، الإجازات، ساعات العمل، مكافأة نهاية الخدمة\n"
                "- **نظام حماية البيانات الشخصية (PDPL)**: الموافقة، الغرض، الاحتفاظ، حقوق الأفراد\n"
                "- **ضوابط الأمن السيبراني (NCA)**: الضوابط الأساسية، حوكمة الأمن، الاستجابة للحوادث\n"
                "- **نظام مكافحة الجرائم المعلوماتية**: الجرائم الإلكترونية والعقوبات\n"
                "- **نظام الشركات**: تأسيس الشركات، المسؤوليات، الحوكمة\n"
                "- **نظام المنافسة**: الممارسات التجارية، الاحتكار، حماية المستهلك\n"
                "- **نظام المشتريات الحكومية**: المناقصات، العقود، الامتثال\n\n"
                "## قواعد الإجابة\n"
                "1. استند دائماً إلى المصادر الرسمية: المراسيم الملكية، الأنظمة، اللوائح التنفيذية\n"
                "2. عند ذكر أي مصطلح قانوني، اذكر النظام والمادة المصدر\n"
                "3. إذا كان للمصطلح تعريفات مختلفة في أنظمة مختلفة، نبّه على ذلك صراحةً\n"
                "4. أجب بالعربية الفصحى دائماً\n"
                "5. عند طلب تقرير قانوني: استخدم هيكلاً منظماً (الملخص، التحليل، التوصيات)\n"
                "6. راجع قاعدة المعرفة الداخلية أولاً للوثائق القانونية المحلية\n\n"
                "## تحذير مهم\n"
                "إجاباتك للأغراض المعلوماتية فقط. للحصول على استشارة قانونية رسمية، يُنصح بمراجعة محامٍ مرخص."
            )
        }
        return [legal_context] + messages

    def pipe(
        self,
        user_message: str,
        model_id: str,
        messages: List[dict],
        body: dict
    ) -> Union[str, Generator, Iterator]:
        """المعالج الرئيسي — يمرر الطلب لـ legal-expert في Open WebUI"""

        enriched_messages = self._inject_legal_context(messages)
        stream = body.get("stream", False)

        payload = {
            "model": self.valves.LEGAL_EXPERT_MODEL_ID,
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
