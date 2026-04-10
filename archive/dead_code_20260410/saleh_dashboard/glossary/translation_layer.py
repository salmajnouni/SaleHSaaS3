"""
SaleH Brain - Translation Layer
طبقة الترجمة الذكية الهجينة

المصادر:
1. هيئة الخبراء بمجلس الوزراء (المرجع الرسمي الأعلى)
2. مجمع الملك سلمان للغة العربية (منصة سوار)
3. وزارة العدل - معجم المصطلحات العدلية
4. Fallback: llama3 مع تعليمات دقيقة
"""

import json
import os
import requests
from pathlib import Path

# ===== قاعدة المصطلحات الرسمية =====
# مستخرجة من مسرد هيئة الخبراء (1,492 مصطلح) ومعجم وزارة العدل
OFFICIAL_TERMS = {
    # ===== أ =====
    "إمضاء": {"en": "Signature", "source": "هيئة الخبراء", "context": "عام"},
    "ابتزاز": {"en": "Extortion / Blackmail", "source": "هيئة الخبراء", "context": "جنائي"},
    "إبراء": {"en": "Release / Discharge", "source": "هيئة الخبراء", "context": "مدني"},
    "إبرام العقد": {"en": "Conclusion of Contract", "source": "هيئة الخبراء", "context": "عقود"},
    "إبطال العقد": {"en": "Annulment of Contract", "source": "هيئة الخبراء", "context": "عقود"},
    "إبعاد": {"en": "Deportation", "source": "هيئة الخبراء", "context": "إداري"},
    "اتجار بالأشخاص": {"en": "Trafficking in Persons", "source": "هيئة الخبراء", "context": "جنائي"},
    "أتعاب": {"en": "Fees / Remuneration", "source": "هيئة الخبراء", "context": "عام"},
    "اتفاق التحكيم": {"en": "Arbitration Agreement", "source": "هيئة الخبراء", "context": "تحكيم"},
    "اتفاقية": {"en": "Convention / Agreement", "source": "هيئة الخبراء", "context": "دولي"},
    "اتفاقية إطارية": {"en": "Framework Agreement", "source": "هيئة الخبراء", "context": "دولي"},
    "اتفاقية دولية": {"en": "International Convention", "source": "هيئة الخبراء", "context": "دولي"},
    "إجراء": {"en": "Procedure", "source": "هيئة الخبراء", "context": "عام"},
    "إجراء إداري": {"en": "Administrative Procedure", "source": "هيئة الخبراء", "context": "إداري"},
    "إجراء باطل": {"en": "Void Procedure", "source": "هيئة الخبراء", "context": "قانوني"},
    "إجراء قانوني": {"en": "Legal Procedure", "source": "هيئة الخبراء", "context": "قانوني"},
    "أجر": {"en": "Wage / Salary", "source": "هيئة الخبراء", "context": "عمل"},
    "إثبات": {"en": "Evidence / Proof", "source": "هيئة الخبراء", "context": "قضائي"},
    "أثر رجعي": {"en": "Retroactive Effect", "source": "هيئة الخبراء", "context": "قانوني"},
    "إثراء بلا سبب": {"en": "Unjust Enrichment", "source": "هيئة الخبراء", "context": "مدني"},

    # ===== ب =====
    "بطلان": {"en": "Nullity / Invalidity", "source": "هيئة الخبراء", "context": "قانوني"},
    "بيع": {"en": "Sale", "source": "هيئة الخبراء", "context": "تجاري"},
    "بيع بالمزاد": {"en": "Auction Sale", "source": "هيئة الخبراء", "context": "تجاري"},

    # ===== ت =====
    "تحكيم": {"en": "Arbitration", "source": "هيئة الخبراء", "context": "تحكيم"},
    "تحقيق": {"en": "Investigation / Inquiry", "source": "هيئة الخبراء", "context": "قضائي"},
    "تدليس": {"en": "Fraud / Deceit", "source": "هيئة الخبراء", "context": "مدني"},
    "ترخيص": {"en": "License / Permit", "source": "هيئة الخبراء", "context": "إداري"},
    "تسوية": {"en": "Settlement", "source": "هيئة الخبراء", "context": "عام"},
    "تصفية": {"en": "Liquidation", "source": "هيئة الخبراء", "context": "تجاري"},
    "تعويض": {"en": "Compensation / Damages", "source": "هيئة الخبراء", "context": "مدني"},
    "تفتيش": {"en": "Inspection", "source": "هيئة الخبراء", "context": "إداري"},
    "تقادم": {"en": "Prescription / Limitation", "source": "هيئة الخبراء", "context": "مدني"},
    "توكيل": {"en": "Power of Attorney", "source": "هيئة الخبراء", "context": "عام"},

    # ===== ج =====
    "جريمة": {"en": "Crime / Offense", "source": "هيئة الخبراء", "context": "جنائي"},
    "جزاء": {"en": "Penalty / Sanction", "source": "هيئة الخبراء", "context": "عام"},
    "جهة مختصة": {"en": "Competent Authority", "source": "هيئة الخبراء", "context": "إداري"},

    # ===== ح =====
    "حجز": {"en": "Seizure / Attachment", "source": "هيئة الخبراء", "context": "قضائي"},
    "حق": {"en": "Right", "source": "هيئة الخبراء", "context": "عام"},
    "حق الامتياز": {"en": "Privilege / Lien", "source": "هيئة الخبراء", "context": "مدني"},
    "حكم": {"en": "Judgment / Ruling", "source": "هيئة الخبراء", "context": "قضائي"},
    "حكم ابتدائي": {"en": "First Instance Judgment", "source": "هيئة الخبراء", "context": "قضائي"},
    "حكم نهائي": {"en": "Final Judgment", "source": "هيئة الخبراء", "context": "قضائي"},
    "حوكمة": {"en": "Governance", "source": "هيئة الخبراء", "context": "حوكمة"},
    "حوكمة الشركات": {"en": "Corporate Governance", "source": "هيئة الخبراء", "context": "حوكمة"},

    # ===== د =====
    "دعوى": {"en": "Lawsuit / Action / Claim", "source": "هيئة الخبراء", "context": "قضائي"},
    "دعوى جزائية": {"en": "Criminal Action", "source": "هيئة الخبراء", "context": "جنائي"},
    "دعوى مدنية": {"en": "Civil Action", "source": "هيئة الخبراء", "context": "مدني"},
    "دليل": {"en": "Evidence / Proof", "source": "هيئة الخبراء", "context": "قضائي"},

    # ===== ع =====
    "عقد": {"en": "Contract / Agreement", "source": "هيئة الخبراء", "context": "عقود"},
    "عقد إداري": {"en": "Administrative Contract", "source": "هيئة الخبراء", "context": "إداري"},
    "عقد عمل": {"en": "Employment Contract", "source": "هيئة الخبراء", "context": "عمل"},
    "عقد مقاولة": {"en": "Construction Contract", "source": "هيئة الخبراء", "context": "بناء"},
    "عقوبة": {"en": "Punishment / Penalty", "source": "هيئة الخبراء", "context": "جنائي"},

    # ===== ف =====
    "فسخ العقد": {"en": "Rescission of Contract", "source": "هيئة الخبراء", "context": "عقود"},
    "فساد": {"en": "Corruption", "source": "هيئة الخبراء", "context": "حوكمة"},

    # ===== ق =====
    "قانون": {"en": "Law", "source": "هيئة الخبراء", "context": "عام"},
    "قرار": {"en": "Decision / Resolution", "source": "هيئة الخبراء", "context": "إداري"},
    "قرار إداري": {"en": "Administrative Decision", "source": "هيئة الخبراء", "context": "إداري"},
    "قضاء": {"en": "Judiciary", "source": "هيئة الخبراء", "context": "قضائي"},

    # ===== ل =====
    "لائحة": {"en": "By-law / Implementing Regulation", "source": "هيئة الخبراء", "context": "تشريعي"},
    "لائحة تنفيذية": {"en": "Implementing Regulation", "source": "هيئة الخبراء", "context": "تشريعي"},

    # ===== م =====
    "مخالفة": {"en": "Violation / Infringement", "source": "هيئة الخبراء", "context": "عام"},
    "مرسوم": {"en": "Royal Decree", "source": "هيئة الخبراء", "context": "تشريعي"},
    "مرسوم ملكي": {"en": "Royal Decree", "source": "هيئة الخبراء", "context": "تشريعي"},
    "مستأجر": {"en": "Tenant / Lessee", "source": "هيئة الخبراء", "context": "مدني"},
    "مشتريات": {"en": "Procurement", "source": "هيئة الخبراء", "context": "مشتريات"},
    "مصالحة": {"en": "Reconciliation / Settlement", "source": "هيئة الخبراء", "context": "عام"},
    "مقاول": {"en": "Contractor", "source": "هيئة الخبراء", "context": "بناء"},
    "مقاول من الباطن": {"en": "Subcontractor", "source": "هيئة الخبراء", "context": "بناء"},
    "مكافحة الفساد": {"en": "Anti-Corruption", "source": "هيئة الخبراء", "context": "حوكمة"},
    "منافسات": {"en": "Competitive Bidding / Tenders", "source": "هيئة الخبراء", "context": "مشتريات"},
    "موجب": {"en": "Obligation", "source": "هيئة الخبراء", "context": "مدني"},

    # ===== ن =====
    "نزاع": {"en": "Dispute", "source": "هيئة الخبراء", "context": "عام"},
    "نظام": {"en": "Regulation / Act", "source": "هيئة الخبراء", "context": "تشريعي"},
    "نظام العمل": {"en": "Labor Law", "source": "هيئة الخبراء", "context": "عمل"},
    "نظام المشتريات": {"en": "Government Tenders and Procurement Law", "source": "هيئة الخبراء", "context": "مشتريات"},
    "نظام مكافحة الفساد": {"en": "Anti-Corruption Law", "source": "هيئة الخبراء", "context": "حوكمة"},

    # ===== و =====
    "وكالة": {"en": "Agency / Power of Attorney", "source": "هيئة الخبراء", "context": "مدني"},
    "وكيل": {"en": "Agent / Attorney", "source": "هيئة الخبراء", "context": "مدني"},

    # ===== مصطلحات البناء والمقاولات (مجموعة بن السعودي) =====
    "نطاق العمل": {"en": "Scope of Work (SOW)", "source": "معجم المقاولات", "context": "بناء"},
    "مواصفات": {"en": "Specifications", "source": "معجم المقاولات", "context": "بناء"},
    "مخططات": {"en": "Drawings / Plans", "source": "معجم المقاولات", "context": "بناء"},
    "كميات": {"en": "Bill of Quantities (BOQ)", "source": "معجم المقاولات", "context": "بناء"},
    "ضمان حسن التنفيذ": {"en": "Performance Bond", "source": "معجم المقاولات", "context": "بناء"},
    "ضمان ابتدائي": {"en": "Bid Bond", "source": "معجم المقاولات", "context": "بناء"},
    "ضمان نهائي": {"en": "Performance Guarantee", "source": "معجم المقاولات", "context": "بناء"},
    "غرامة تأخير": {"en": "Liquidated Damages (LD)", "source": "معجم المقاولات", "context": "بناء"},
    "أمر تغيير": {"en": "Change Order / Variation Order (VO)", "source": "معجم المقاولات", "context": "بناء"},
    "مطالبة": {"en": "Claim", "source": "معجم المقاولات", "context": "بناء"},
    "استلام ابتدائي": {"en": "Provisional Acceptance", "source": "معجم المقاولات", "context": "بناء"},
    "استلام نهائي": {"en": "Final Acceptance", "source": "معجم المقاولات", "context": "بناء"},
    "فترة الضمان": {"en": "Defects Liability Period (DLP)", "source": "معجم المقاولات", "context": "بناء"},
    "مهندس المشروع": {"en": "Project Engineer", "source": "معجم المقاولات", "context": "بناء"},
    "مدير المشروع": {"en": "Project Manager (PM)", "source": "معجم المقاولات", "context": "بناء"},
    "مشرف الموقع": {"en": "Site Supervisor", "source": "معجم المقاولات", "context": "بناء"},
    "طلب استفسار": {"en": "Request for Information (RFI)", "source": "معجم المقاولات", "context": "بناء"},
    "طلب موافقة": {"en": "Request for Approval (RFA)", "source": "معجم المقاولات", "context": "بناء"},
    "جدول أعمال": {"en": "Schedule / Programme", "source": "معجم المقاولات", "context": "بناء"},
    "المسار الحرج": {"en": "Critical Path", "source": "معجم المقاولات", "context": "بناء"},
    "تمديد المدة": {"en": "Extension of Time (EOT)", "source": "معجم المقاولات", "context": "بناء"},

    # ===== مصطلحات الحوكمة والامتثال (GRC) =====
    "حوكمة المخاطر والامتثال": {"en": "Governance, Risk and Compliance (GRC)", "source": "معجم GRC", "context": "حوكمة"},
    "إدارة المخاطر": {"en": "Risk Management", "source": "معجم GRC", "context": "حوكمة"},
    "الامتثال": {"en": "Compliance", "source": "معجم GRC", "context": "حوكمة"},
    "الرقابة الداخلية": {"en": "Internal Control", "source": "معجم GRC", "context": "حوكمة"},
    "التدقيق الداخلي": {"en": "Internal Audit", "source": "معجم GRC", "context": "حوكمة"},
    "التدقيق الخارجي": {"en": "External Audit", "source": "معجم GRC", "context": "حوكمة"},
    "مجلس الإدارة": {"en": "Board of Directors", "source": "معجم GRC", "context": "حوكمة"},
    "الرئيس التنفيذي": {"en": "Chief Executive Officer (CEO)", "source": "معجم GRC", "context": "حوكمة"},
    "الإفصاح والشفافية": {"en": "Disclosure and Transparency", "source": "معجم GRC", "context": "حوكمة"},
    "تضارب المصالح": {"en": "Conflict of Interest", "source": "معجم GRC", "context": "حوكمة"},
    "الرشوة": {"en": "Bribery", "source": "معجم GRC", "context": "حوكمة"},
    "غسيل الأموال": {"en": "Money Laundering", "source": "معجم GRC", "context": "حوكمة"},
    "تمويل الإرهاب": {"en": "Terrorism Financing", "source": "معجم GRC", "context": "حوكمة"},
    "الجهة الرقابية": {"en": "Regulatory Authority", "source": "معجم GRC", "context": "حوكمة"},
    "السياسة": {"en": "Policy", "source": "معجم GRC", "context": "حوكمة"},
    "الإجراء": {"en": "Procedure", "source": "معجم GRC", "context": "حوكمة"},
    "دليل العمل": {"en": "Work Instruction", "source": "معجم GRC", "context": "حوكمة"},

    # ===== مصطلحات نظام المشتريات الحكومية =====
    "منافسة عامة": {"en": "Public Tender", "source": "نظام المنافسات والمشتريات", "context": "مشتريات"},
    "منافسة محدودة": {"en": "Limited Tender", "source": "نظام المنافسات والمشتريات", "context": "مشتريات"},
    "أمر شراء مباشر": {"en": "Direct Purchase Order", "source": "نظام المنافسات والمشتريات", "context": "مشتريات"},
    "لجنة فتح العروض": {"en": "Bid Opening Committee", "source": "نظام المنافسات والمشتريات", "context": "مشتريات"},
    "لجنة فحص العروض": {"en": "Bid Evaluation Committee", "source": "نظام المنافسات والمشتريات", "context": "مشتريات"},
    "الجهة الحكومية": {"en": "Government Entity", "source": "نظام المنافسات والمشتريات", "context": "مشتريات"},
    "المورد": {"en": "Supplier / Vendor", "source": "نظام المنافسات والمشتريات", "context": "مشتريات"},
    "الاستشاري": {"en": "Consultant", "source": "نظام المنافسات والمشتريات", "context": "مشتريات"},
    "كراسة الشروط": {"en": "Tender Documents / Bidding Documents", "source": "نظام المنافسات والمشتريات", "context": "مشتريات"},
    "ضمان العطاء": {"en": "Bid Security / Bid Bond", "source": "نظام المنافسات والمشتريات", "context": "مشتريات"},
    "الترسية": {"en": "Award of Contract", "source": "نظام المنافسات والمشتريات", "context": "مشتريات"},

    # ===== مصطلحات نظام العمل السعودي =====
    "صاحب العمل": {"en": "Employer", "source": "نظام العمل", "context": "عمل"},
    "العامل": {"en": "Worker / Employee", "source": "نظام العمل", "context": "عمل"},
    "عقد العمل المحدد المدة": {"en": "Fixed-Term Employment Contract", "source": "نظام العمل", "context": "عمل"},
    "عقد العمل غير المحدد المدة": {"en": "Open-Ended Employment Contract", "source": "نظام العمل", "context": "عمل"},
    "فترة التجربة": {"en": "Probationary Period", "source": "نظام العمل", "context": "عمل"},
    "إنهاء الخدمة": {"en": "Termination of Service", "source": "نظام العمل", "context": "عمل"},
    "مكافأة نهاية الخدمة": {"en": "End-of-Service Gratuity", "source": "نظام العمل", "context": "عمل"},
    "إجازة سنوية": {"en": "Annual Leave", "source": "نظام العمل", "context": "عمل"},
    "إجازة مرضية": {"en": "Sick Leave", "source": "نظام العمل", "context": "عمل"},
    "ساعات العمل": {"en": "Working Hours", "source": "نظام العمل", "context": "عمل"},
    "العمل الإضافي": {"en": "Overtime", "source": "نظام العمل", "context": "عمل"},
    "السعودة": {"en": "Saudization / Nitaqat", "source": "نظام العمل", "context": "عمل"},
    "تصريح العمل": {"en": "Work Permit", "source": "نظام العمل", "context": "عمل"},
    "الإقامة": {"en": "Residency Permit (Iqama)", "source": "نظام العمل", "context": "عمل"},

    # ===== مصطلحات رؤية 2030 =====
    "رؤية 2030": {"en": "Vision 2030", "source": "رؤية 2030", "context": "استراتيجي"},
    "التحول الوطني": {"en": "National Transformation", "source": "رؤية 2030", "context": "استراتيجي"},
    "الاقتصاد غير النفطي": {"en": "Non-Oil Economy", "source": "رؤية 2030", "context": "استراتيجي"},
    "الاستثمار الأجنبي المباشر": {"en": "Foreign Direct Investment (FDI)", "source": "رؤية 2030", "context": "استراتيجي"},
    "التخصيص": {"en": "Privatization", "source": "رؤية 2030", "context": "استراتيجي"},
    "الشراكة بين القطاعين العام والخاص": {"en": "Public-Private Partnership (PPP)", "source": "رؤية 2030", "context": "استراتيجي"},
    "صندوق الاستثمارات العامة": {"en": "Public Investment Fund (PIF)", "source": "رؤية 2030", "context": "استراتيجي"},
    "هيئة السوق المالية": {"en": "Capital Market Authority (CMA)", "source": "رؤية 2030", "context": "مالي"},
}

# ===== مصطلحات لها تعريفات متعددة حسب السياق =====
MULTI_CONTEXT_TERMS = {
    "نظام": {
        "default": "Regulation / Act",
        "contexts": {
            "تشريعي": "Regulation (e.g., Labor Regulation, Procurement Regulation)",
            "تقني": "System",
            "إداري": "System / Framework",
        },
        "note": "في الأنظمة السعودية يُترجم دائماً بـ Regulation وليس Law",
        "source": "هيئة الخبراء"
    },
    "مقاول": {
        "default": "Contractor",
        "contexts": {
            "بناء": "Main Contractor",
            "مشتريات": "Contractor (Party to a Government Contract)",
            "عمل": "Employer (in Labor Law context)",
        },
        "note": "في نظام العمل قد يُشير لصاحب العمل، في البناء يُشير للمنفذ",
        "source": "هيئة الخبراء"
    },
    "عقد": {
        "default": "Contract",
        "contexts": {
            "مدني": "Contract / Agreement",
            "بناء": "Construction Contract",
            "عمل": "Employment Contract",
            "مشتريات": "Government Contract",
            "دولي": "Treaty / Convention",
        },
        "note": "يُترجم حسب السياق",
        "source": "هيئة الخبراء"
    },
    "جزاء": {
        "default": "Penalty",
        "contexts": {
            "عمل": "Disciplinary Penalty",
            "بناء": "Liquidated Damages",
            "جنائي": "Criminal Sanction",
            "إداري": "Administrative Penalty",
        },
        "note": "في عقود البناء يُترجم بـ Liquidated Damages",
        "source": "هيئة الخبراء"
    },
    "لائحة": {
        "default": "By-law",
        "contexts": {
            "تشريعي": "Implementing Regulation",
            "داخلي": "Internal By-law / Articles of Association",
            "شركات": "Articles of Association",
        },
        "note": "اللائحة التنفيذية = Implementing Regulation، لائحة الشركة = Articles of Association",
        "source": "هيئة الخبراء"
    },
    "مرسوم": {
        "default": "Royal Decree",
        "contexts": {
            "ملكي": "Royal Decree (M/)",
            "وزاري": "Ministerial Resolution",
        },
        "note": "المرسوم الملكي يبدأ بـ م/ والأمر الملكي بـ أ/",
        "source": "هيئة الخبراء"
    },
    "حكم": {
        "default": "Judgment",
        "contexts": {
            "قضائي": "Court Judgment / Ruling",
            "تحكيم": "Arbitral Award",
            "إداري": "Administrative Decision",
        },
        "note": "في التحكيم يُسمى Award وليس Judgment",
        "source": "هيئة الخبراء"
    },
    "دليل": {
        "default": "Evidence",
        "contexts": {
            "قضائي": "Evidence / Proof",
            "إداري": "Manual / Guide",
            "تقني": "Manual",
        },
        "note": "في القضاء = Evidence، في الإدارة = Manual",
        "source": "هيئة الخبراء"
    },
}


def translate_term(term: str, context: str = None) -> dict:
    """
    ترجمة مصطلح مع مراعاة السياق
    
    Args:
        term: المصطلح العربي
        context: السياق (بناء، عمل، مشتريات، إلخ)
    
    Returns:
        dict: نتيجة الترجمة مع المصدر والملاحظات
    """
    # 1. البحث في المصطلحات متعددة السياقات أولاً
    if term in MULTI_CONTEXT_TERMS:
        entry = MULTI_CONTEXT_TERMS[term]
        result = {
            "term_ar": term,
            "term_en": entry["default"],
            "source": entry["source"],
            "has_multiple_contexts": True,
            "contexts": entry["contexts"],
            "note": entry.get("note", ""),
            "confidence": "رسمي - هيئة الخبراء"
        }
        if context and context in entry["contexts"]:
            result["term_en"] = entry["contexts"][context]
            result["context_used"] = context
        return result

    # 2. البحث في قاعدة المصطلحات الرسمية
    if term in OFFICIAL_TERMS:
        entry = OFFICIAL_TERMS[term]
        return {
            "term_ar": term,
            "term_en": entry["en"],
            "source": entry["source"],
            "context": entry["context"],
            "has_multiple_contexts": False,
            "confidence": "رسمي - هيئة الخبراء"
        }

    # 3. Fallback: llama3 مع تعليمات دقيقة
    return translate_with_llama3(term, context)


def translate_with_llama3(term: str, context: str = None) -> dict:
    """
    ترجمة بـ llama3 مع تعليمات دقيقة للترجمة القانونية السعودية
    """
    ollama_url = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434")
    
    context_hint = f" في سياق {context}" if context else ""
    
    prompt = f"""أنت مترجم قانوني متخصص في الأنظمة السعودية.

مهمتك: ترجمة المصطلح التالي إلى الإنجليزية{context_hint}.

قواعد الترجمة:
1. استخدم المصطلحات الرسمية لهيئة الخبراء بمجلس الوزراء
2. "نظام" تُترجم بـ Regulation وليس Law
3. "لائحة تنفيذية" تُترجم بـ Implementing Regulation
4. "مرسوم ملكي" تُترجم بـ Royal Decree
5. "جهة مختصة" تُترجم بـ Competent Authority
6. إذا كان للمصطلح أكثر من ترجمة، اذكرها جميعاً

المصطلح: {term}

أجب بصيغة JSON فقط:
{{"term_en": "الترجمة الرئيسية", "alternatives": ["بديل1", "بديل2"], "note": "ملاحظة إن وجدت"}}"""

    try:
        response = requests.post(
            f"{ollama_url}/api/generate",
            json={"model": "llama3.1:latest", "prompt": prompt, "stream": False},
            timeout=30
        )
        if response.status_code == 200:
            result_text = response.json().get("response", "")
            # استخراج JSON من الاستجابة
            import re
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                llm_result = json.loads(json_match.group())
                return {
                    "term_ar": term,
                    "term_en": llm_result.get("term_en", term),
                    "alternatives": llm_result.get("alternatives", []),
                    "note": llm_result.get("note", ""),
                    "source": "llama3.1 (AI - غير رسمي)",
                    "confidence": "AI - يُنصح بالتحقق",
                    "has_multiple_contexts": False
                }
    except Exception as e:
        pass

    return {
        "term_ar": term,
        "term_en": term,
        "source": "غير موجود",
        "confidence": "غير معروف",
        "error": "لم يتم العثور على الترجمة"
    }


def get_all_terms(category: str = None) -> list:
    """إرجاع جميع المصطلحات مع إمكانية الفلترة بالفئة"""
    terms = []
    
    # المصطلحات الأحادية
    for term_ar, data in OFFICIAL_TERMS.items():
        if category is None or data.get("context") == category:
            terms.append({
                "term_ar": term_ar,
                "term_en": data["en"],
                "source": data["source"],
                "context": data["context"],
                "has_multiple_contexts": False
            })
    
    # المصطلحات متعددة السياقات
    for term_ar, data in MULTI_CONTEXT_TERMS.items():
        terms.append({
            "term_ar": term_ar,
            "term_en": data["default"],
            "source": data["source"],
            "context": "متعدد",
            "has_multiple_contexts": True,
            "contexts": data["contexts"],
            "note": data.get("note", "")
        })
    
    return terms


def get_categories() -> list:
    """إرجاع قائمة الفئات المتاحة"""
    categories = set()
    for data in OFFICIAL_TERMS.values():
        categories.add(data["context"])
    return sorted(list(categories))


if __name__ == "__main__":
    # اختبار
    print("=== اختبار طبقة الترجمة ===\n")
    
    test_terms = [
        ("نظام", "تشريعي"),
        ("نظام", "تقني"),
        ("مقاول", "بناء"),
        ("مقاول", "عمل"),
        ("جزاء", "بناء"),
        ("جزاء", "جنائي"),
        ("عقد مقاولة", None),
        ("غرامة تأخير", None),
        ("حوكمة الشركات", None),
    ]
    
    for term, ctx in test_terms:
        result = translate_term(term, ctx)
        ctx_str = f" [{ctx}]" if ctx else ""
        print(f"  {term}{ctx_str} → {result['term_en']} ({result['source']})")
        if result.get("note"):
            print(f"    ملاحظة: {result['note']}")
    
    print(f"\nإجمالي المصطلحات: {len(OFFICIAL_TERMS) + len(MULTI_CONTEXT_TERMS)}")
    print(f"الفئات: {get_categories()}")
