"""
n8n Expert Pipeline — خبير أتمتة n8n
======================================
Pipeline صحيحة تستدعي Ollama مباشرة (وليس Open WebUI).
تظهر في Open WebUI كنموذج "External" باسم "🔄 n8n Automation Expert".

البنية الصحيحة (من الوثائق الرسمية):
    المستخدم → Open WebUI → Pipelines Server (هنا) → Ollama → النموذج

المرجع: https://github.com/open-webui/pipelines
"""

from typing import List, Union, Generator, Iterator
from pydantic import BaseModel
import requests
import json
import os


class Pipeline:

    class Valves(BaseModel):
        # عنوان Ollama — داخل Docker يكون host.docker.internal
        OLLAMA_BASE_URL: str = "http://host.docker.internal:11434"
        # النموذج الأساسي في Ollama
        MODEL_ID: str = "deepseek-r1:7b"
        # درجة الإبداعية (منخفضة للدقة التقنية)
        TEMPERATURE: float = 0.3
        # الحد الأقصى للرموز
        MAX_TOKENS: int = 4096
        # تفعيل حقن السياق المتخصص
        ENABLE_EXPERT_CONTEXT: bool = True

    def __init__(self):
        self.name = "🔄 n8n Automation Expert"
        self.id = "n8n-expert"
        self.valves = self.Valves()

    async def on_startup(self):
        print(f"[n8n Expert] تشغيل — النموذج: {self.valves.MODEL_ID} على {self.valves.OLLAMA_BASE_URL}")

    async def on_shutdown(self):
        print("[n8n Expert] إيقاف")

    # ─────────────────────────────────────────────
    # السياق المتخصص لخبير n8n
    # ─────────────────────────────────────────────
    EXPERT_SYSTEM_PROMPT = """أنت "خبير أتمتة n8n" في نظام SaleHSaaS. تتحدث العربية بطلاقة وتكتب JSON بدقة.

## بيئة العمل (Docker Compose)
- n8n: http://n8n:5678 — API: /api/v1/ (Header: X-N8N-API-KEY)
- Open WebUI: http://open-webui:8080
- Ollama: http://host.docker.internal:11434
- n8n Bridge: http://n8n_bridge:3333/v1/ (OpenAI-compatible)
- File API: http://file_api:8765
- SearXNG: http://searxng:8080/search?q=...&format=json
- ChromaDB: http://chromadb:8000
- Tika: http://tika:9998

## مهامك
1. تصميم Workflows: JSON كامل جاهز للاستيراد في n8n
2. تشخيص الأخطاء: تحليل سجلات n8n واقتراح الإصلاحات
3. إدارة Ollama: تحميل النماذج، مراقبة الحالة
4. الجدولة: تعبيرات cron دقيقة (6 حقول: ثانية دقيقة ساعة يوم شهر أسبوع)
5. التكامل: ربط الخدمات مع بعضها

## قواعد الإخراج
- أجب بالعربية دائماً
- Workflow JSON: في كتلة ```json
- أوامر curl/bash: في كتلة ```bash
- عند الشك في عقدة n8n: اذكر typeVersion الصحيح
- لا تخترع عقداً غير موجود في n8n"""

    def _inject_context(self, messages: List[dict]) -> List[dict]:
        """حقن السياق المتخصص إذا لم يكن موجوداً"""
        if not self.valves.ENABLE_EXPERT_CONTEXT:
            return messages
        if any(m.get("role") == "system" for m in messages):
            return messages
        return [{"role": "system", "content": self.EXPERT_SYSTEM_PROMPT}] + messages

    def pipe(
        self,
        user_message: str,
        model_id: str,
        messages: List[dict],
        body: dict,
    ) -> Union[str, Generator, Iterator]:
        """الاستدعاء المباشر لـ Ollama — الطريقة الصحيحة"""

        enriched = self._inject_context(messages)
        stream = body.get("stream", False)

        payload = {
            "model": self.valves.MODEL_ID,
            "messages": enriched,
            "stream": stream,
            "options": {
                "temperature": body.get("temperature", self.valves.TEMPERATURE),
                "num_predict": body.get("max_tokens", self.valves.MAX_TOKENS),
            },
        }

        try:
            r = requests.post(
                f"{self.valves.OLLAMA_BASE_URL}/api/chat",
                json=payload,
                timeout=300,
                stream=stream,
            )
            r.raise_for_status()

            if stream:
                def _stream():
                    for line in r.iter_lines():
                        if not line:
                            continue
                        try:
                            chunk = json.loads(line)
                            content = chunk.get("message", {}).get("content", "")
                            if content:
                                yield content
                            if chunk.get("done"):
                                break
                        except json.JSONDecodeError:
                            pass
                return _stream()
            else:
                data = r.json()
                return data.get("message", {}).get("content", "⚠️ لم يُعد الرد.")

        except requests.exceptions.ConnectionError:
            return f"❌ تعذّر الاتصال بـ Ollama على {self.valves.OLLAMA_BASE_URL}\nتحقق من تشغيل Ollama."
        except requests.exceptions.Timeout:
            return "⏱️ انتهت مهلة الانتظار (300 ثانية) — النموذج يستغرق وقتاً طويلاً."
        except requests.exceptions.HTTPError as e:
            return f"❌ خطأ HTTP من Ollama: {e.response.status_code} — {e.response.text[:200]}"
        except Exception as e:
            return f"❌ خطأ غير متوقع: {str(e)}"
