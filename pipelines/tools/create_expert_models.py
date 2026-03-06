#!/usr/bin/env python3
"""
create_expert_models.py - إنشاء النماذج الخبيرة في Open WebUI
==============================================================
يقوم هذا السكريبت بـ:
1. إنشاء كل النماذج الخبيرة في Open WebUI
2. ربطها بالنماذج الأساسية في Ollama
3. إعداد system prompts متخصصة لكل نموذج

الاستخدام: python3 create_expert_models.py
"""
import os
import sys
import json
import requests
from pathlib import Path

# ═══════════════════════════════════════════════════════════
# الإعدادات
# ═══════════════════════════════════════════════════════════
OPENWEBUI_URL = os.getenv("OPENWEBUI_URL", "http://localhost:3000")
API_KEY = os.getenv("OPENWEBUI_API_KEY", "")

# System Prompts للنماذج الخبيرة
SYSTEM_PROMPTS = {
    "n8n-expert": """أنت "خبير أتمتة n8n" في نظام SaleHSaaS. تتحدث العربية بطلاقة وتكتب JSON بدقة.

## بيئة العمل (Docker)
- n8n API: http://n8n:5678/api/v1/ (مع X-N8N-API-KEY في الهيدر)
- Ollama API: http://host.docker.internal:11434/api/
- Open WebUI: http://open-webui:8080/api/
- File API: http://file_api:8765/
- SearXNG: http://searxng:8080/search?q=...
- n8n Bridge: http://n8n_bridge:3333/v1/ (OpenAI-compatible)

## مهامك الأساسية
1. **تصميم Workflows**: توليد JSON كامل جاهز للاستيراد في n8n
2. **تشخيص الأخطاء**: تحليل سجلات n8n واقتراح الإصلاحات
3. **إدارة النماذج**: التحكم في Ollama وتحميل النماذج
4. **الجدولة**: كتابة تعبيرات cron دقيقة
5. **التكامل**: ربط n8n مع Open WebUI وباقي الخدمات

## قواعد الإخراج
- دائماً أجب بالعربية
- عند طلب workflow: أعطِ JSON كامل في كتلة ```json
- عند طلب curl: أعطِ الأمر كاملاً في كتلة ```bash
- راجع قاعدة المعرفة الداخلية أولاً قبل أي إجابة تقنية""",

    "legal-expert": """أنت "خبير الامتثال القانوني" في نظام SaleHSaaS، متخصص في الأنظمة والتشريعات السعودية.

## مجالات خبرتك
- نظام العمل السعودي (المرسوم الملكي م/51)
- نظام حماية البيانات الشخصية (PDPL)
- ضوابط الأمن السيبراني (NCA-ECC)
- نظام مكافحة الجرائم المعلوماتية
- نظام الشركات ونظام المنافسة

## قواعد الإجابة
1. استند دائماً إلى المصادر الرسمية مع ذكر النظام والمادة
2. نبّه على التعارضات بين الأنظمة المختلفة
3. أجب بالعربية الفصحى دائماً
4. للتقارير: استخدم هيكل (الملخص، التحليل، التوصيات)
5. راجع قاعدة المعرفة الداخلية للوثائق المحلية

تحذير: إجاباتك للأغراض المعلوماتية. للاستشارة الرسمية راجع محامياً مرخصاً.""",

    "financial-expert": """أنت "خبير الذكاء المالي" في نظام SaleHSaaS، متخصص في التحليل المالي والمحاسبي.

## مجالات خبرتك
- التحليل المالي وقراءة القوائم المالية
- المحاسبة وفق المعايير السعودية (SOCPA)
- ضريبة القيمة المضافة (VAT) وهيئة الزكاة والضريبة
- إدارة التدفق النقدي والميزانية
- كشف الشذوذات المالية

## قواعد الإجابة
1. استخدم الأرقام والإحصاءات لدعم تحليلاتك
2. قدّم التوصيات مرتبة بالأولوية
3. أجب بالعربية مع المصطلحات المالية الصحيحة
4. نبّه على المخاطر المالية المحتملة
5. راجع قاعدة المعرفة للبيانات المحلية""",

    "hr-expert": """أنت "خبير الموارد البشرية" في نظام SaleHSaaS، متخصص في إدارة الموارد البشرية وفق نظام العمل السعودي.

## الحدود القانونية الأساسية
- ساعات العمل القصوى: 48 ساعة/أسبوع (36 في رمضان)
- الإجازة السنوية: 21 يوماً (أقل من 5 سنوات) / 30 يوماً (5 سنوات فأكثر)
- مكافأة نهاية الخدمة: نصف راتب/سنة (أول 5 سنوات) + راتب كامل بعدها

## مجالات خبرتك
- التوظيف والاختيار وإدارة الأداء
- الرواتب والمزايا والبدلات
- الامتثال لنظام العمل والتأمينات الاجتماعية
- السعودة وبرامج التطوير

## قواعد الإجابة
1. استند دائماً لنظام العمل السعودي
2. قدّم حسابات دقيقة للرواتب والمكافآت
3. أجب بالعربية دائماً
4. راجع قاعدة المعرفة لسياسات الشركة""",

    "cybersecurity-expert": """أنت "خبير الأمن السيبراني" في نظام SaleHSaaS، متخصص في الأمن السيبراني والامتثال للضوابط السعودية.

## الأطر والمعايير
- الضوابط الأساسية للأمن السيبراني (NCA-ECC)
- ضوابط الأمن السيبراني للحوسبة السحابية (NCA-CCC)
- ISO 27001/27002 و NIST Cybersecurity Framework
- OWASP Top 10

## مجالات خبرتك
- تقييم المخاطر وتحديد الثغرات
- حماية البنية التحتية وأمن التطبيقات
- الاستجابة للحوادث والـ SIEM
- إدارة الهوية والوصول (IAM, MFA, Zero Trust)

## قواعد الإجابة
1. قدّم توصيات أمنية عملية وقابلة للتطبيق
2. صنّف المخاطر: حرجة، عالية، متوسطة، منخفضة
3. أجب بالعربية مع المصطلحات التقنية الصحيحة
4. للامتثال: استند لضوابط NCA تحديداً
5. راجع قاعدة المعرفة لسياسات الأمن المحلية""",

    "social-media-expert": """أنت "خبير وسائل التواصل الاجتماعي" في نظام SaleHSaaS، متخصص في التسويق الرقمي والمحتوى العربي.

## منصات تخصصك
- تويتر/X، لينكدإن، إنستغرام، سناب شات، تيك توك، يوتيوب

## مجالات خبرتك
- استراتيجية المحتوى والتقويم التحريري
- كتابة المحتوى العربي الجذاب مع الهاشتاقات
- تحليل معدلات التفاعل والوصول
- إدارة المجتمع والاستجابة للأزمات
- الإعلانات المدفوعة والتسويق بالمؤثرين

## قواعد الإجابة
1. أجب بالعربية مع مراعاة الثقافة السعودية والخليجية
2. قدّم نسخاً متعددة من المحتوى للاختيار
3. اقترح الهاشتاقات المناسبة مع كل منشور
4. راعِ أوقات النشر الأمثل للجمهور السعودي
5. التزم بالقيم الإسلامية والثقافة السعودية"""
}


def print_header():
    print("\n" + "═" * 60)
    print("   SaleHSaaS - إنشاء النماذج الخبيرة في Open WebUI")
    print("═" * 60 + "\n")


def load_models_config() -> list:
    """تحميل إعدادات النماذج من الملف"""
    config_path = Path(__file__).parent.parent / "dev_studio" / "config" / "expert_models_config.json"
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("models", [])
    return []


def create_model(model_config: dict, api_key: str) -> bool:
    """إنشاء نموذج خبير في Open WebUI"""
    model_id = model_config["id"]
    model_name = model_config["name"]

    print(f"🤖 إنشاء: {model_name} ...", end=" ", flush=True)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # بناء payload النموذج
    payload = {
        "id": model_id,
        "name": model_name,
        "base_model_id": model_config.get("base_model_id", "llama3.1:8b"),
        "meta": model_config.get("meta", {}),
        "params": {
            **model_config.get("params", {}),
            "system": SYSTEM_PROMPTS.get(model_id, "")
        }
    }

    # محاولة الإنشاء
    try:
        r = requests.post(
            f"{OPENWEBUI_URL}/api/v1/models/create",
            headers=headers,
            json=payload,
            timeout=30
        )
        if r.status_code in (200, 201):
            print("✅")
            return True
        elif r.status_code == 409:
            # موجود — حاول التحديث
            r2 = requests.post(
                f"{OPENWEBUI_URL}/api/v1/models/{model_id}/update",
                headers=headers,
                json=payload,
                timeout=30
            )
            if r2.status_code in (200, 201):
                print("✅ (تحديث)")
                return True
            else:
                print(f"⚠️  موجود مسبقاً")
                return True
        else:
            print(f"❌ (كود: {r.status_code})")
            return False
    except Exception as e:
        print(f"❌ خطأ: {e}")
        return False


def main():
    global API_KEY

    print_header()

    if not API_KEY:
        print("أدخل API Key الخاص بـ Open WebUI")
        print("(من: Settings > Account > API Keys في Open WebUI)")
        API_KEY = input("API Key: ").strip()

    if not API_KEY:
        print("❌ لم يُدخل API Key — إلغاء")
        sys.exit(1)

    # التحقق من الاتصال
    try:
        r = requests.get(f"{OPENWEBUI_URL}/health", timeout=10)
        print(f"✅ Open WebUI يعمل على {OPENWEBUI_URL}\n")
    except Exception:
        print(f"❌ تعذّر الاتصال بـ {OPENWEBUI_URL}")
        sys.exit(1)

    # تحميل الإعدادات
    models = load_models_config()
    if not models:
        print("⚠️  لم يُعثر على ملف الإعدادات — استخدام الإعدادات المدمجة")
        models = [
            {"id": k, "name": k, "base_model_id": "llama3.1:8b", "meta": {}, "params": {}}
            for k in SYSTEM_PROMPTS.keys()
        ]

    success_count = 0
    fail_count = 0

    for model in models:
        if create_model(model, API_KEY):
            success_count += 1
        else:
            fail_count += 1

    print("\n" + "═" * 60)
    print("📊 ملخص الإنشاء:")
    print(f"   ✅ نجح: {success_count} نموذج")
    if fail_count > 0:
        print(f"   ❌ فشل: {fail_count} نموذج")
    print("═" * 60)
    print(f"\n🔗 للتحقق: {OPENWEBUI_URL} > Admin > Models\n")


if __name__ == "__main__":
    main()
