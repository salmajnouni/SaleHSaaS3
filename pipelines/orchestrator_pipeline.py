"""
Orchestrator Pipeline — المنسق الرئيسي للنماذج الخبيرة
======================================================
Pipeline صحيحة تستدعي Ollama مباشرة (وليس Open WebUI).
تظهر في Open WebUI كنموذج "External" باسم "🎯 SaleHSaaS Orchestrator".

البنية الصحيحة (من الوثائق الرسمية):
    المستخدم → Open WebUI → Pipelines Server (هنا) → Ollama → النموذج

المرجع: https://github.com/open-webui/pipelines
"""

from typing import List, Union, Generator, Iterator
from pydantic import BaseModel
import requests
import json


class Pipeline:

    class Valves(BaseModel):
        OLLAMA_BASE_URL: str = "http://host.docker.internal:11434"
        MODEL_ID: str = "llama3.1:8b"
        TEMPERATURE: float = 0.3
        MAX_TOKENS: int = 4096
        ENABLE_EXPERT_CONTEXT: bool = True

    def __init__(self):
        self.name = "🎯 SaleHSaaS Orchestrator"
        self.id = "orchestrator"
        self.valves = self.Valves()

    async def on_startup(self):
        print(f"[orchestrator] تشغيل — النموذج: {self.valves.MODEL_ID} على {self.valves.OLLAMA_BASE_URL}")

    async def on_shutdown(self):
        print(f"[orchestrator] إيقاف")

    EXPERT_SYSTEM_PROMPT = """أنت "المنسق الرئيسي" لنظام SaleHSaaS. مهمتك تحليل طلب المستخدم وتقديم أفضل إجابة.

## النماذج الخبيرة المتاحة
- n8n-expert: أتمتة n8n، workflows، تكامل الخدمات
- legal-expert: الأنظمة السعودية، PDPL، نظام العمل
- financial-expert: المحاسبة، VAT، الزكاة، التحليل المالي
- hr-expert: الموارد البشرية، GOSI، نطاقات، الرواتب
- cybersecurity-expert: الأمن السيبراني، NCA، ISO 27001
- social-media-expert: التسويق الرقمي، المحتوى العربي

## تعليمات
1. حلّل الطلب وحدّد المجال المناسب
2. أجب بشكل شامل ومفيد
3. إذا تداخلت المجالات، اجمع بين الخبرات
4. أجب بالعربية دائماً"""

    def _inject_context(self, messages: List[dict]) -> List[dict]:
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
                return r.json().get("message", {}).get("content", "⚠️ لم يُعد الرد.")

        except requests.exceptions.ConnectionError:
            return f"❌ تعذّر الاتصال بـ Ollama على {self.valves.OLLAMA_BASE_URL}\nتحقق من تشغيل Ollama."
        except requests.exceptions.Timeout:
            return "⏱️ انتهت مهلة الانتظار (300 ثانية)."
        except requests.exceptions.HTTPError as e:
            return f"❌ خطأ HTTP: {e.response.status_code} — {e.response.text[:200]}"
        except Exception as e:
            return f"❌ خطأ غير متوقع: {str(e)}"
