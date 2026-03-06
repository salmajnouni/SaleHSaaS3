"""
n8n Expert Pipeline - وكيل أتمتة n8n الذكي
=============================================
Pipeline مخصصة لـ Open WebUI تقوم بـ:
1. تمرير الطلبات لنموذج n8n-expert (deepseek-r1:7b + RAG)
2. إضافة سياق n8n تلقائياً لكل محادثة
3. الظهور في /v1/models لاستخدامه من n8n مباشرة
4. دعم كامل لأدوات Open WebUI (web_search, code_interpreter, knowledge)
5. دعم Streaming للردود الطويلة
"""

from typing import List, Optional, Generator, Iterator, Union
from pydantic import BaseModel
import requests
import json
import os


class Pipeline:
    class Valves(BaseModel):
        # عنوان Open WebUI الداخلي
        OPENWEBUI_BASE_URL: str = "http://open-webui:8080"
        # API Key لـ Open WebUI (يُعيَّن من متغيرات البيئة)
        OPENWEBUI_API_KEY: str = os.getenv("OPENWEBUI_API_KEY", "")
        # اسم نموذج n8n-expert في Open WebUI
        N8N_EXPERT_MODEL_ID: str = "n8n-expert"
        # تفعيل السياق الإضافي
        ENABLE_N8N_CONTEXT: bool = True
        # درجة الحرارة الافتراضية
        DEFAULT_TEMPERATURE: float = 0.3
        # الحد الأقصى للتوكنات
        MAX_TOKENS: int = 8192

    def __init__(self):
        self.name = "🔄 n8n Automation Expert"
        self.id = "n8n-expert-pipeline"
        self.valves = self.Valves()

    async def on_startup(self):
        print(f"✅ n8n Expert Pipeline جاهزة — النموذج: {self.valves.N8N_EXPERT_MODEL_ID}")

    async def on_shutdown(self):
        print("⏹️ n8n Expert Pipeline أُوقفت")

    def _build_headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.valves.OPENWEBUI_API_KEY:
            headers["Authorization"] = f"Bearer {self.valves.OPENWEBUI_API_KEY}"
        return headers

    def _inject_n8n_context(self, messages: List[dict]) -> List[dict]:
        """حقن سياق n8n في بداية المحادثة إذا لم يكن موجوداً"""
        if not self.valves.ENABLE_N8N_CONTEXT:
            return messages

        # تحقق إذا كان هناك system message بالفعل
        has_system = any(m.get("role") == "system" for m in messages)
        if has_system:
            return messages

        n8n_context = {
            "role": "system",
            "content": (
                "أنت \"خبير أتمتة n8n\" في نظام SaleHSaaS. تتحدث العربية بطلاقة وتكتب JSON بدقة.\n\n"
                "## بيئة العمل (Docker)\n"
                "- n8n API: http://n8n:5678/api/v1/ (مع X-N8N-API-KEY في الهيدر)\n"
                "- Ollama API: http://host.docker.internal:11434/api/\n"
                "- Open WebUI: http://open-webui:8080/api/\n"
                "- File API: http://file_api:8765/\n"
                "- SearXNG: http://searxng:8080/search?q=...\n"
                "- n8n Bridge: http://n8n_bridge:3333/v1/ (OpenAI-compatible)\n\n"
                "## مهامك الأساسية\n"
                "1. **تصميم Workflows**: توليد JSON كامل جاهز للاستيراد في n8n\n"
                "2. **تشخيص الأخطاء**: تحليل سجلات n8n واقتراح الإصلاحات\n"
                "3. **إدارة النماذج**: التحكم في Ollama وتحميل النماذج\n"
                "4. **الجدولة**: كتابة تعبيرات cron دقيقة\n"
                "5. **التكامل**: ربط n8n مع Open WebUI وباقي الخدمات\n\n"
                "## قواعد الإخراج\n"
                "- دائماً أجب بالعربية\n"
                "- عند طلب workflow: أعطِ JSON كامل في كتلة ```json\n"
                "- عند طلب curl: أعطِ الأمر كاملاً في كتلة ```bash\n"
                "- راجع قاعدة المعرفة الداخلية أولاً قبل أي إجابة تقنية"
            )
        }
        return [n8n_context] + messages

    def pipe(
        self,
        user_message: str,
        model_id: str,
        messages: List[dict],
        body: dict
    ) -> Union[str, Generator, Iterator]:
        """المعالج الرئيسي — يمرر الطلب لـ n8n-expert في Open WebUI"""

        # حقن سياق n8n
        enriched_messages = self._inject_n8n_context(messages)
        stream = body.get("stream", False)

        # بناء الطلب
        payload = {
            "model": self.valves.N8N_EXPERT_MODEL_ID,
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
            return "⏱️ انتهت مهلة الاتصال (180 ثانية) — النموذج يستغرق وقتاً طويلاً."
        except Exception as e:
            return f"❌ خطأ غير متوقع: {str(e)}"
