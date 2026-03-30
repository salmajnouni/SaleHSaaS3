"""
SaleH Legal Pipeline - المعالج القانوني الذكي
==============================================
Pipeline مخصصة لـ Open WebUI تقوم بـ:
1. حقن المعجم القانوني السعودي تلقائياً في كل محادثة
2. كشف المصطلحات القانونية في السؤال وإضافة تعريفاتها
3. تنبيه النموذج بالتعارضات بين الأنظمة
4. توليد تقارير قانونية منظمة عند الطلب
"""

from typing import List, Optional, Generator, Iterator
from pydantic import BaseModel
import json
import os
import re


class Pipe:
    class Valves(BaseModel):
        # إعدادات قابلة للتعديل من واجهة Open WebUI
        ENABLE_LEGAL_CONTEXT: bool = True
        ENABLE_CONFLICT_DETECTION: bool = True
        ENABLE_REPORT_MODE: bool = True
        MAX_TERMS_PER_QUERY: int = 5
        GLOSSARY_PATH: str = "/app/backend/data/glossary/legal_lexicon.json"
        SYSTEM_PROMPT_ADDITION: str = """
أنت مساعد قانوني متخصص في الأنظمة والتشريعات السعودية.
تستند في إجاباتك إلى المصادر الرسمية: المراسيم الملكية، الأنظمة، اللوائح التنفيذية.
عند ذكر أي مصطلح قانوني، اذكر النظام والمادة المصدر.
إذا كان للمصطلح تعريفات مختلفة في أنظمة مختلفة، نبّه على ذلك صراحةً.
"""

    def __init__(self):
        self.name = "SaleH Legal Pipeline - المعالج القانوني"
        self.valves = self.Valves()
        self.lexicon = {}
        self.load_lexicon()

    def load_lexicon(self):
        """تحميل المعجم القانوني من الملف"""
        try:
            if os.path.exists(self.valves.GLOSSARY_PATH):
                with open(self.valves.GLOSSARY_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # بناء فهرس سريع بالمصطلحات العربية والإنجليزية
                    for term_id, term_data in data.items():
                        arabic = term_data.get("arabic", "").strip()
                        english = term_data.get("english", "").strip().lower()
                        if arabic:
                            self.lexicon[arabic] = term_data
                        if english:
                            self.lexicon[english] = term_data
                print(f"✅ تم تحميل {len(self.lexicon)} مصطلح قانوني")
            else:
                print(f"⚠️ ملف المعجم غير موجود: {self.valves.GLOSSARY_PATH}")
                self._load_fallback_lexicon()
        except Exception as e:
            print(f"❌ خطأ في تحميل المعجم: {e}")
            self._load_fallback_lexicon()

    def _load_fallback_lexicon(self):
        """معجم احتياطي مدمج للمصطلحات الأساسية"""
        self.lexicon = {
            "العقد": {
                "arabic": "العقد",
                "english": "Contract",
                "definitions": [
                    {
                        "source": "نظام المنافسات والمشتريات الحكومية",
                        "article": "المادة الأولى",
                        "text": "اتفاق مكتوب بين جهة حكومية ومتعاقد معها، لتأمين أصناف أو تنفيذ أعمال أو تقديم خدمات وفق الشروط والمواصفات المحددة.",
                        "context": ["مشتريات", "حكومي"]
                    },
                    {
                        "source": "نظام الشركات",
                        "article": "المادة الثانية",
                        "text": "الاتفاق الذي يلتزم بموجبه شخصان أو أكثر بالمساهمة في مشروع مشترك بتقديم حصة من مال أو عمل أو غير ذلك.",
                        "context": ["شركات", "التزامات"]
                    }
                ],
                "has_conflict": True
            },
            "المقاول": {
                "arabic": "المقاول",
                "english": "Contractor",
                "definitions": [
                    {
                        "source": "نظام المنافسات والمشتريات الحكومية",
                        "article": "المادة الأولى",
                        "text": "الشخص الطبيعي أو الاعتباري الذي يمارس نشاط المقاولات لتنفيذ أعمال البناء والتشييد والصيانة.",
                        "context": ["مقاولات", "مشتريات"]
                    },
                    {
                        "source": "نظام العمل",
                        "article": "المادة الثانية",
                        "text": "كل شخص طبيعي أو اعتباري يتعهد بتنفيذ عمل لحساب صاحب العمل مقابل أجر.",
                        "context": ["عمل", "توظيف"]
                    }
                ],
                "has_conflict": True
            },
            "الحوكمة": {
                "arabic": "الحوكمة",
                "english": "Governance",
                "definitions": [
                    {
                        "source": "لوائح الحوكمة - هيئة السوق المالية",
                        "article": "المادة الأولى",
                        "text": "منظومة القواعد والإجراءات والمعايير التي تحكم العلاقة بين الإدارة والمساهمين وأصحاب المصلحة، وتضمن الشفافية والمساءلة وحماية الحقوق.",
                        "context": ["حوكمة", "شركات", "امتثال"]
                    }
                ],
                "has_conflict": False
            }
        }

    def detect_legal_terms(self, text: str) -> List[dict]:
        """كشف المصطلحات القانونية في النص"""
        found_terms = []
        text_lower = text.lower()

        for term, data in self.lexicon.items():
            if term in text or term.lower() in text_lower:
                found_terms.append({
                    "term": term,
                    "data": data
                })
                if len(found_terms) >= self.valves.MAX_TERMS_PER_QUERY:
                    break

        return found_terms

    def build_legal_context(self, terms: List[dict]) -> str:
        """بناء السياق القانوني للحقن في المحادثة"""
        if not terms:
            return ""

        context_parts = ["\n\n---\n📚 **السياق القانوني المرجعي:**\n"]

        for item in terms:
            term = item["term"]
            data = item["data"]
            definitions = data.get("definitions", [])

            if not definitions:
                continue

            arabic = data.get("arabic", term)
            english = data.get("english", "")
            has_conflict = data.get("has_conflict", False)

            if has_conflict:
                context_parts.append(f"\n⚠️ **{arabic}** ({english}) - *تعريفات متعارضة بين الأنظمة:*")
            else:
                context_parts.append(f"\n✅ **{arabic}** ({english}):")

            for defn in definitions[:3]:  # أقصى 3 تعريفات
                source = defn.get("source", "")
                article = defn.get("article", "")
                text_def = defn.get("text", "")
                context_tags = defn.get("context", [])

                context_parts.append(
                    f"\n  - **{source}** | {article}\n"
                    f"    > {text_def}\n"
                    f"    🏷️ {' | '.join(context_tags)}"
                )

        context_parts.append("\n---\n")
        return "".join(context_parts)

    def is_report_request(self, text: str) -> bool:
        """كشف طلبات التقارير"""
        report_keywords = [
            "اكتب تقرير", "أكتب تقرير", "اعمل تقرير", "أعمل تقرير",
            "write report", "generate report", "create report",
            "تقرير عن", "تقرير حول", "ملخص قانوني", "تحليل قانوني",
            "وثّق", "وثق", "document"
        ]
        text_lower = text.lower()
        return any(kw in text or kw in text_lower for kw in report_keywords)

    def build_report_prompt(self, user_message: str) -> str:
        """بناء prompt خاص بالتقارير القانونية"""
        return f"""
أنت خبير قانوني متخصص في الأنظمة السعودية. المطلوب منك كتابة تقرير قانوني احترافي.

**تعليمات التقرير:**
1. ابدأ بعنوان واضح وتاريخ التقرير
2. اذكر الأساس القانوني (النظام، المرسوم الملكي، المادة)
3. استخدم الأرقام والبنود المنظمة
4. أضف خلاصة تنفيذية في النهاية
5. اذكر المراجع القانونية المستخدمة
6. الصياغة رسمية وأكاديمية

**الطلب:** {user_message}
"""

    async def on_startup(self):
        """تشغيل عند بدء الـ Pipeline"""
        print(f"🚀 SaleH Legal Pipeline تعمل - {len(self.lexicon)} مصطلح محمّل")
        self.load_lexicon()  # إعادة تحميل المعجم

    async def on_shutdown(self):
        """إيقاف الـ Pipeline"""
        print("⏹️ SaleH Legal Pipeline متوقفة")

    def pipe(
        self,
        user_message: str,
        model_id: str,
        messages: List[dict],
        body: dict
    ) -> str | Generator | Iterator:
        """
        المعالج الرئيسي - يُستدعى مع كل رسالة
        """

        if not self.valves.ENABLE_LEGAL_CONTEXT:
            # Pipeline معطلة - مرر الرسالة كما هي
            return self._passthrough(messages, body)

        # 1. كشف المصطلحات القانونية
        found_terms = self.detect_legal_terms(user_message)

        # 2. بناء السياق القانوني
        legal_context = ""
        if found_terms and self.valves.ENABLE_LEGAL_CONTEXT:
            legal_context = self.build_legal_context(found_terms)

        # 3. تعديل system prompt
        system_content = self.valves.SYSTEM_PROMPT_ADDITION

        # 4. معالجة طلبات التقارير
        if self.valves.ENABLE_REPORT_MODE and self.is_report_request(user_message):
            user_message = self.build_report_prompt(user_message)

        # 5. حقن السياق في الرسالة
        if legal_context:
            enhanced_message = user_message + legal_context
        else:
            enhanced_message = user_message

        # 6. بناء الرسائل المعدّلة
        modified_messages = []

        # إضافة/تعديل system message
        has_system = False
        for msg in messages:
            if msg.get("role") == "system":
                modified_messages.append({
                    "role": "system",
                    "content": msg["content"] + "\n\n" + system_content
                })
                has_system = True
            elif msg.get("role") == "user" and msg == messages[-1]:
                # آخر رسالة مستخدم - أضف السياق
                modified_messages.append({
                    "role": "user",
                    "content": enhanced_message
                })
            else:
                modified_messages.append(msg)

        if not has_system:
            modified_messages.insert(0, {
                "role": "system",
                "content": system_content
            })

        # تحديث body بالرسائل المعدّلة
        body["messages"] = modified_messages

        return body

    def _passthrough(self, messages, body):
        """تمرير بدون تعديل"""
        return body
