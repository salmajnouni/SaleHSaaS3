#!/usr/bin/env python3
"""
install_pipelines.py - تثبيت كل الـ Pipelines في Open WebUI
=============================================================
الاستخدام: python3 install_pipelines.py
المتطلبات: pip install requests
"""
import os
import sys
import requests
from pathlib import Path

# ═══════════════════════════════════════════════════════════
# الإعدادات
# ═══════════════════════════════════════════════════════════
OPENWEBUI_URL = os.getenv("OPENWEBUI_URL", "http://localhost:3000")
API_KEY = os.getenv("OPENWEBUI_API_KEY", "")

PIPELINES_DIR = Path(__file__).parent

# قائمة الـ Pipelines للتثبيت (بالترتيب)
PIPELINES = [
    {
        "file": "n8n_expert_pipeline.py",
        "name": "🔄 n8n Automation Expert",
        "id": "n8n-expert-pipeline",
    },
    {
        "file": "legal_expert_pipeline.py",
        "name": "⚖️ Legal Compliance Expert",
        "id": "legal-expert-pipeline",
    },
    {
        "file": "financial_expert_pipeline.py",
        "name": "💰 Financial Intelligence Expert",
        "id": "financial-expert-pipeline",
    },
    {
        "file": "hr_expert_pipeline.py",
        "name": "👥 HR Management Expert",
        "id": "hr-expert-pipeline",
    },
    {
        "file": "cybersecurity_expert_pipeline.py",
        "name": "🛡️ Cybersecurity Expert",
        "id": "cybersecurity-expert-pipeline",
    },
    {
        "file": "social_media_expert_pipeline.py",
        "name": "📱 Social Media Expert",
        "id": "social-media-expert-pipeline",
    },
    {
        "file": "orchestrator_pipeline.py",
        "name": "🎯 SaleHSaaS Orchestrator",
        "id": "orchestrator-pipeline",
    },
]


def print_header():
    print("\n" + "═" * 60)
    print("   SaleHSaaS - تثبيت الـ Pipelines في Open WebUI")
    print("═" * 60 + "\n")


def check_connection(api_key: str) -> bool:
    """التحقق من الاتصال بـ Open WebUI"""
    try:
        r = requests.get(f"{OPENWEBUI_URL}/health", timeout=10)
        if r.status_code == 200:
            print(f"✅ Open WebUI يعمل على {OPENWEBUI_URL}")
            return True
        else:
            print(f"⚠️  Open WebUI أعاد كود: {r.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ تعذّر الاتصال بـ {OPENWEBUI_URL}")
        print("   تأكد من تشغيل: docker-compose up -d")
        return False


def install_pipeline(pipeline: dict, api_key: str) -> bool:
    """تثبيت Pipeline واحدة"""
    file_path = PIPELINES_DIR / pipeline["file"]

    if not file_path.exists():
        print(f"⚠️  الملف غير موجود: {pipeline['file']} — تخطي")
        return False

    print(f"📦 تثبيت: {pipeline['name']} ...", end=" ", flush=True)

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    headers = {"Authorization": f"Bearer {api_key}"}

    # الطريقة 1: رفع الملف مباشرة
    try:
        files = {
            "file": (pipeline["file"], content.encode("utf-8"), "text/x-python")
        }
        r = requests.post(
            f"{OPENWEBUI_URL}/api/v1/pipelines/upload",
            headers=headers,
            files=files,
            timeout=30
        )
        if r.status_code in (200, 201):
            print("✅")
            return True
        elif r.status_code == 409:
            # موجود بالفعل — حاول التحديث
            r2 = requests.post(
                f"{OPENWEBUI_URL}/api/v1/pipelines/{pipeline['id']}/update",
                headers={**headers, "Content-Type": "application/json"},
                json={"content": content},
                timeout=30
            )
            if r2.status_code in (200, 201):
                print("✅ (تحديث)")
                return True
            else:
                print(f"⚠️  موجود مسبقاً (كود: {r2.status_code})")
                return True
        else:
            print(f"❌ (كود: {r.status_code}) — {r.text[:100]}")
            return False
    except Exception as e:
        print(f"❌ خطأ: {e}")
        return False


def list_installed_pipelines(api_key: str):
    """عرض قائمة الـ Pipelines المثبتة"""
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        r = requests.get(
            f"{OPENWEBUI_URL}/api/v1/pipelines/list",
            headers=headers,
            timeout=10
        )
        if r.status_code == 200:
            data = r.json()
            pipelines = data if isinstance(data, list) else data.get("data", [])
            print(f"\n📋 الـ Pipelines المثبتة ({len(pipelines)}):")
            for p in pipelines:
                print(f"   • {p.get('name', p.get('id', 'Unknown'))}")
        else:
            print(f"⚠️  تعذّر جلب القائمة (كود: {r.status_code})")
    except Exception as e:
        print(f"⚠️  خطأ في جلب القائمة: {e}")


def main():
    global API_KEY

    print_header()

    # طلب API Key إذا لم يُعطَ
    if not API_KEY:
        print("أدخل API Key الخاص بـ Open WebUI")
        print("(من: Settings > Account > API Keys في Open WebUI)")
        API_KEY = input("API Key: ").strip()

    if not API_KEY:
        print("❌ لم يُدخل API Key — إلغاء")
        sys.exit(1)

    # التحقق من الاتصال
    if not check_connection(API_KEY):
        sys.exit(1)

    print()
    success_count = 0
    fail_count = 0

    for pipeline in PIPELINES:
        if install_pipeline(pipeline, API_KEY):
            success_count += 1
        else:
            fail_count += 1

    # ملخص
    print("\n" + "═" * 60)
    print("📊 ملخص التثبيت:")
    print(f"   ✅ نجح: {success_count} Pipeline")
    if fail_count > 0:
        print(f"   ❌ فشل: {fail_count} Pipeline")
    print("═" * 60)

    # عرض القائمة النهائية
    list_installed_pipelines(API_KEY)

    print(f"\n🔗 للتحقق اليدوي: {OPENWEBUI_URL} > Admin > Pipelines")
    print("🔗 للاستخدام من n8n: استخدم n8n_bridge مع model_id من القائمة أعلاه\n")


if __name__ == "__main__":
    main()
