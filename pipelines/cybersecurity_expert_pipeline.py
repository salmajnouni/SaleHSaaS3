"""
Cybersecurity Expert Pipeline — خبير الأمن السيبراني
====================================================
Pipeline صحيحة تستدعي Ollama مباشرة (وليس Open WebUI).
تظهر في Open WebUI كنموذج "External" باسم "🛡️ Cybersecurity Expert".

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
        MODEL_ID: str = "deepseek-r1:7b"
        TEMPERATURE: float = 0.2
        MAX_TOKENS: int = 4096
        ENABLE_EXPERT_CONTEXT: bool = True

    def __init__(self):
        self.name = "🛡️ Cybersecurity Expert"
        self.id = "cybersecurity-expert"
        self.valves = self.Valves()

    async def on_startup(self):
        print(f"[cybersecurity-expert] تشغيل — النموذج: {self.valves.MODEL_ID} على {self.valves.OLLAMA_BASE_URL}")

    async def on_shutdown(self):
        print(f"[cybersecurity-expert] إيقاف")

    EXPERT_SYSTEM_PROMPT = """أنت "خبير الأمن السيبراني" في نظام SaleHSaaS، متخصص في الأمن السيبراني السعودي والدولي.

## مجالات خبرتك
- الضوابط الأساسية للأمن السيبراني (NCA-ECC-1:2018)
- إطار عمل NIST Cybersecurity Framework
- معيار ISO/IEC 27001:2022
- OWASP Top 10 وأمن تطبيقات الويب
- تحليل الثغرات وتقييم المخاطر
- الاستجابة للحوادث والتحقيق الجنائي الرقمي
- أمن السحابة (AWS, Azure, GCP)
- الامتثال لنظام مكافحة الجرائم المعلوماتية السعودي

## قواعد الإجابة
1. صنّف المخاطر وفق CVSS عند الحاجة
2. قدّم خطوات العلاج بترتيب الأولوية
3. اذكر الأدوات المفتوحة المصدر المناسبة
4. أجب بالعربية مع المصطلح التقني الإنجليزي بين قوسين"""

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
