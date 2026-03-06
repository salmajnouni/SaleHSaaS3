"""
Social Media Expert Pipeline - خبير وسائل التواصل الاجتماعي
============================================================
Pipeline مخصصة لـ Open WebUI تقوم بـ:
1. تمرير الطلبات لنموذج social-media-expert مع RAG على استراتيجيات المحتوى
2. حقن سياق التسويق الرقمي والمحتوى العربي تلقائياً
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
        SOCIAL_EXPERT_MODEL_ID: str = "social-media-expert"
        ENABLE_SOCIAL_CONTEXT: bool = True
        DEFAULT_TEMPERATURE: float = 0.7
        MAX_TOKENS: int = 4096

    def __init__(self):
        self.name = "📱 Social Media Expert"
        self.id = "social-media-expert-pipeline"
        self.valves = self.Valves()

    async def on_startup(self):
        print(f"✅ Social Media Expert Pipeline جاهزة — النموذج: {self.valves.SOCIAL_EXPERT_MODEL_ID}")

    async def on_shutdown(self):
        print("⏹️ Social Media Expert Pipeline أُوقفت")

    def _build_headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.valves.OPENWEBUI_API_KEY:
            headers["Authorization"] = f"Bearer {self.valves.OPENWEBUI_API_KEY}"
        return headers

    def _inject_social_context(self, messages: List[dict]) -> List[dict]:
        """حقن سياق التسويق الرقمي ووسائل التواصل الاجتماعي"""
        if not self.valves.ENABLE_SOCIAL_CONTEXT:
            return messages

        has_system = any(m.get("role") == "system" for m in messages)
        if has_system:
            return messages

        social_context = {
            "role": "system",
            "content": (
                "أنت \"خبير وسائل التواصل الاجتماعي\" في نظام SaleHSaaS، متخصص في التسويق الرقمي وإدارة المحتوى.\n\n"
                "## منصات التواصل التي تتخصص فيها\n"
                "- **تويتر/X**: المحتوى القصير، الهاشتاقات، التفاعل الفوري\n"
                "- **لينكدإن**: المحتوى المهني، بناء العلامة التجارية الشخصية\n"
                "- **إنستغرام**: المحتوى البصري، الريلز، القصص\n"
                "- **يوتيوب**: المحتوى المرئي الطويل، السيو، الصور المصغرة\n"
                "- **سناب شات**: الجمهور السعودي الشاب، القصص، الإعلانات\n"
                "- **تيك توك**: المحتوى الفيروسي، الترندات، التحديات\n\n"
                "## مجالات خبرتك\n"
                "- **استراتيجية المحتوى**: تخطيط المحتوى، التقويم التحريري، الهوية البصرية\n"
                "- **كتابة المحتوى العربي**: الأسلوب الجذاب، الهاشتاقات، الـ CTA\n"
                "- **تحليل البيانات**: معدلات التفاعل، الوصول، التحويلات\n"
                "- **إدارة المجتمع**: الرد على التعليقات، إدارة الأزمات\n"
                "- **الإعلانات المدفوعة**: استهداف الجمهور، تحسين الميزانية\n"
                "- **التسويق بالمؤثرين**: اختيار المؤثرين، قياس الأثر\n\n"
                "## قواعد الإجابة\n"
                "1. أجب بالعربية دائماً مع مراعاة الثقافة السعودية والخليجية\n"
                "2. عند كتابة محتوى: قدّم نسخاً متعددة للاختيار منها\n"
                "3. اقترح الهاشتاقات المناسبة مع كل منشور\n"
                "4. راعِ أوقات النشر الأمثل للجمهور السعودي\n"
                "5. التزم بالقيم الإسلامية والثقافة السعودية في كل محتوى\n"
                "6. راجع قاعدة المعرفة الداخلية لاستراتيجية العلامة التجارية المحلية"
            )
        }
        return [social_context] + messages

    def pipe(
        self,
        user_message: str,
        model_id: str,
        messages: List[dict],
        body: dict
    ) -> Union[str, Generator, Iterator]:
        """المعالج الرئيسي — يمرر الطلب لـ social-media-expert في Open WebUI"""

        enriched_messages = self._inject_social_context(messages)
        stream = body.get("stream", False)

        payload = {
            "model": self.valves.SOCIAL_EXPERT_MODEL_ID,
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
