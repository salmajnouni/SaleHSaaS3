"""
Cybersecurity Expert Pipeline - خبير الأمن السيبراني
=====================================================
Pipeline مخصصة لـ Open WebUI تقوم بـ:
1. تمرير الطلبات لنموذج cybersecurity-expert مع RAG على وثائق NCA
2. حقن سياق الأمن السيبراني والضوابط السعودية تلقائياً
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
        CYBER_EXPERT_MODEL_ID: str = "cybersecurity-expert"
        ENABLE_CYBER_CONTEXT: bool = True
        DEFAULT_TEMPERATURE: float = 0.2
        MAX_TOKENS: int = 8192

    def __init__(self):
        self.name = "🛡️ Cybersecurity Expert"
        self.id = "cybersecurity-expert-pipeline"
        self.valves = self.Valves()

    async def on_startup(self):
        print(f"✅ Cybersecurity Expert Pipeline جاهزة — النموذج: {self.valves.CYBER_EXPERT_MODEL_ID}")

    async def on_shutdown(self):
        print("⏹️ Cybersecurity Expert Pipeline أُوقفت")

    def _build_headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.valves.OPENWEBUI_API_KEY:
            headers["Authorization"] = f"Bearer {self.valves.OPENWEBUI_API_KEY}"
        return headers

    def _inject_cyber_context(self, messages: List[dict]) -> List[dict]:
        """حقن سياق الأمن السيبراني والضوابط السعودية"""
        if not self.valves.ENABLE_CYBER_CONTEXT:
            return messages

        has_system = any(m.get("role") == "system" for m in messages)
        if has_system:
            return messages

        cyber_context = {
            "role": "system",
            "content": (
                "أنت \"خبير الأمن السيبراني\" في نظام SaleHSaaS، متخصص في الأمن السيبراني والامتثال للضوابط السعودية.\n\n"
                "## الأطر والمعايير التي تعمل بها\n"
                "- **الضوابط الأساسية للأمن السيبراني (NCA-ECC)**: الإطار الوطني السعودي للأمن السيبراني\n"
                "- **ضوابط الأمن السيبراني للحوسبة السحابية (NCA-CCC)**: متطلبات الأمن السحابي\n"
                "- **نظام مكافحة الجرائم المعلوماتية**: الجرائم الإلكترونية والعقوبات في المملكة\n"
                "- **ISO 27001/27002**: معايير إدارة أمن المعلومات\n"
                "- **NIST Cybersecurity Framework**: إطار الأمن السيبراني الأمريكي\n"
                "- **OWASP Top 10**: أهم ثغرات تطبيقات الويب\n\n"
                "## مجالات خبرتك\n"
                "- **تقييم المخاطر**: تحديد التهديدات، تقييم الثغرات، حساب المخاطر\n"
                "- **حماية البنية التحتية**: جدران الحماية، IDS/IPS، تجزئة الشبكة\n"
                "- **أمن التطبيقات**: مراجعة الكود، اختبار الاختراق، SAST/DAST\n"
                "- **الاستجابة للحوادث**: SIEM، SOC، خطط الاستجابة\n"
                "- **إدارة الهوية والوصول**: IAM، MFA، Zero Trust\n"
                "- **التشفير**: البروتوكولات، إدارة المفاتيح، PKI\n\n"
                "## قواعد الإجابة\n"
                "1. قدّم توصيات أمنية عملية وقابلة للتطبيق\n"
                "2. صنّف المخاطر حسب الخطورة (حرجة، عالية، متوسطة، منخفضة)\n"
                "3. أجب بالعربية دائماً مع استخدام المصطلحات التقنية الصحيحة\n"
                "4. عند الإجابة على أسئلة الامتثال: استند إلى ضوابط NCA تحديداً\n"
                "5. راجع قاعدة المعرفة الداخلية لسياسات الأمن المحلية\n\n"
                "## بيئة النظام\n"
                "- الخدمات تعمل في Docker على Windows\n"
                "- الشبكة الداخلية: salehsaas_network\n"
                "- لا يُسمح بإرسال أي بيانات خارج البيئة المحلية"
            )
        }
        return [cyber_context] + messages

    def pipe(
        self,
        user_message: str,
        model_id: str,
        messages: List[dict],
        body: dict
    ) -> Union[str, Generator, Iterator]:
        """المعالج الرئيسي — يمرر الطلب لـ cybersecurity-expert في Open WebUI"""

        enriched_messages = self._inject_cyber_context(messages)
        stream = body.get("stream", False)

        payload = {
            "model": self.valves.CYBER_EXPERT_MODEL_ID,
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
