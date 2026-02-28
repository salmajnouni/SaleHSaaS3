#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
SaleHSaaS 3.0 - Legal Compliance Agent (وكيل الامتثال القانوني)

Reviews documents, contracts, and policies for compliance with Saudi regulations.
Processes all data locally with no external transmission.
"""

import json
import re
from datetime import datetime
from typing import Optional


class LegalAgent:
    """
    AI-powered legal compliance agent for Saudi regulations.
    Specializes in NCA, PDPL, CITC, and Saudi Labor Law.
    """

    AGENT_NAME = "وكيل الامتثال القانوني"
    AGENT_VERSION = "3.0"

    # Key Saudi regulations
    REGULATIONS = {
        "نظام العمل السعودي": {
            "description": "نظام العمل الصادر بالمرسوم الملكي م/51",
            "key_articles": ["الفصل التعسفي", "الإجازات", "ساعات العمل", "مكافأة نهاية الخدمة"]
        },
        "نظام حماية البيانات الشخصية (PDPL)": {
            "description": "نظام حماية البيانات الشخصية الصادر عام 2021",
            "key_articles": ["الموافقة", "الغرض", "الاحتفاظ", "حقوق الأفراد", "الإفصاح"]
        },
        "ضوابط الأمن السيبراني (NCA)": {
            "description": "الضوابط الأساسية للأمن السيبراني",
            "key_articles": ["حوكمة الأمن", "حماية الأصول", "الاستجابة للحوادث"]
        },
        "نظام مكافحة الجرائم المعلوماتية": {
            "description": "نظام مكافحة الجرائم المعلوماتية الصادر عام 2007",
            "key_articles": ["الوصول غير المصرح", "التشهير الإلكتروني", "الاحتيال الإلكتروني"]
        }
    }

    # Sensitive keywords that trigger compliance review
    SENSITIVE_KEYWORDS = {
        "بيانات شخصية": "PDPL",
        "personal data": "PDPL",
        "رقم هوية": "PDPL",
        "بصمة": "PDPL",
        "موقع جغرافي": "PDPL",
        "اختراق": "NCA",
        "تسريب": "NCA",
        "كلمة مرور": "NCA",
        "password": "NCA",
        "فصل": "نظام العمل",
        "إنهاء خدمة": "نظام العمل",
        "تمييز": "نظام العمل",
    }

    def __init__(self, ollama_url: str = "http://ollama:11434", model: str = "llama3"):
        self.ollama_url = ollama_url
        self.model = model
        print(f"✅ {self.AGENT_NAME} v{self.AGENT_VERSION} initialized.")

    def _ask_llm(self, prompt: str) -> str:
        """Sends a prompt to the local Ollama LLM."""
        import requests
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False},
                timeout=180
            )
            response.raise_for_status()
            return response.json().get("response", "لا توجد استجابة.")
        except Exception as e:
            return f"❌ خطأ في الاتصال بالنموذج: {e}"

    def review_document(self, text: str, document_type: str = "عام") -> dict:
        """
        Reviews a document for legal compliance issues.

        Args:
            text (str): The document text to review.
            document_type (str): Type of document (e.g., 'عقد', 'سياسة', 'إجراء').

        Returns:
            dict: Review results with compliance flags and recommendations.
        """
        print(f"⚖️ مراجعة {document_type} ({len(text)} حرف)...")

        # Keyword-based compliance scan
        triggered_regulations = {}
        for keyword, regulation in self.SENSITIVE_KEYWORDS.items():
            if keyword.lower() in text.lower():
                if regulation not in triggered_regulations:
                    triggered_regulations[regulation] = []
                triggered_regulations[regulation].append(keyword)

        # Risk level assessment
        risk_level = "منخفض"
        if len(triggered_regulations) >= 3:
            risk_level = "عالٍ"
        elif len(triggered_regulations) >= 1:
            risk_level = "متوسط"

        # AI-powered legal review
        prompt = f"""
أنت مستشار قانوني متخصص في الأنظمة السعودية. راجع النص التالي ({document_type}) وحدد:
1. المخاوف القانونية الرئيسية
2. الأنظمة المنطبقة (نظام العمل، PDPL، NCA، إلخ)
3. التوصيات التحسينية

النص:
{text[:2000]}  

المراجعة القانونية (باللغة العربية):
"""
        ai_review = self._ask_llm(prompt)

        return {
            "agent": self.AGENT_NAME,
            "timestamp": datetime.now().isoformat(),
            "document_type": document_type,
            "text_length": len(text),
            "risk_level": risk_level,
            "triggered_regulations": triggered_regulations,
            "ai_legal_review": ai_review,
            "recommendations": self._generate_recommendations(triggered_regulations)
        }

    def _generate_recommendations(self, triggered_regulations: dict) -> list:
        """Generates specific recommendations based on triggered regulations."""
        recommendations = []
        if "PDPL" in triggered_regulations:
            recommendations.append("✅ أضف بند الموافقة الصريحة على معالجة البيانات الشخصية")
            recommendations.append("✅ حدد مدة الاحتفاظ بالبيانات وآلية الحذف")
            recommendations.append("✅ وضح حقوق أصحاب البيانات في الوصول والتصحيح والحذف")
        if "NCA" in triggered_regulations:
            recommendations.append("✅ راجع سياسة كلمات المرور وتشفير البيانات")
            recommendations.append("✅ أضف إجراءات الاستجابة لحوادث الأمن السيبراني")
        if "نظام العمل" in triggered_regulations:
            recommendations.append("✅ تأكد من توافق شروط الإنهاء مع نظام العمل السعودي")
            recommendations.append("✅ راجع احتساب مكافأة نهاية الخدمة")
        return recommendations

    def check_contract(self, contract_text: str) -> dict:
        """Specialized contract review for Saudi law compliance."""
        return self.review_document(contract_text, document_type="عقد")

    def check_privacy_policy(self, policy_text: str) -> dict:
        """Specialized privacy policy review for PDPL compliance."""
        return self.review_document(policy_text, document_type="سياسة الخصوصية")


if __name__ == '__main__':
    agent = LegalAgent()
    sample_contract = """
    عقد عمل
    يُعيَّن الموظف في المنصب المحدد ويخضع لنظام العمل السعودي.
    يلتزم الموظف بالحفاظ على سرية بيانات العملاء الشخصية وأرقام هوياتهم.
    يحق للشركة إنهاء الخدمة في حال الإخلال بالشروط.
    """
    result = agent.check_contract(sample_contract)
    print(json.dumps(result, ensure_ascii=False, indent=2))
