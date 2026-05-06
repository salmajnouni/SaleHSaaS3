import os
import sys
import time
import requests
import shutil
import json
from pathlib import Path

# إضافة مسار المحرك القانوني
sys.path.append("/mnt/workspace/iumDLdMeLEk8LXJooJDdK1u4FnvzMAiga1jTUcLZEz/core/grc_engine")
from pdpl.pdpl_checker import PDPLComplianceChecker

# إعدادات المجلدات
INBOX_DIR = Path("/knowledge_inbox")
PROCESSING_DIR = Path("/knowledge_processing")
PROCESSED_DIR = Path("/knowledge_processed")
FAILED_DIR = Path("/knowledge_failed")

# إعدادات Open WebUI
OPEN_WEBUI_URL = os.getenv("OPEN_WEBUI_URL", "http://open_webui:8080")
WEBUI_API_KEY = os.getenv("WEBUI_API_KEY")
if not WEBUI_API_KEY:
    raise ValueError("WEBUI_API_KEY environment variable is required")

# تهيئة فاحص الامتثال
pdpl_checker = PDPLComplianceChecker()

def check_compliance(file_path):
    """فحص محتوى الملف بحثاً عن بيانات حساسة قبل الرفع"""
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        
        findings = pdpl_checker.scan_text(content, source_name=file_path.name)
        
        if findings:
            print(f"⚠️ Compliance Issue: Found {len(findings)} sensitive data patterns in {file_path.name}")
            # إنشاء تقرير خطأ صغير
            error_report = FAILED_DIR / f"{file_path.name}_compliance_error.json"
            with open(error_report, "w", encoding="utf-8") as ef:
                json.dump(findings, ef, ensure_ascii=False, indent=4)
            return False
        return True
    except Exception as e:
        print(f"❌ Error checking compliance: {e}")
        return False

def upload_to_webui(file_path):
    """رفع الملف مباشرة إلى نظام الملفات في Open WebUI"""
    try:
        # فحص الامتثال أولاً
        if not check_compliance(file_path):
            return False

        print(f"🚀 [v6.0] Ingesting: {file_path.name}...")
        
        headers = {
            "Authorization": f"Bearer {WEBUI_API_KEY}"
        }
        
        # المسار الرسمي لرفع الملفات
        url = f"{OPEN_WEBUI_URL}/api/v1/files/"
        
        with open(file_path, "rb") as f:
            files = {"file": (file_path.name, f)}
            response = requests.post(url, headers=headers, files=files, timeout=60)
            
        if response.status_code == 200:
            print(f"✅ Success: {file_path.name}")
            return True
        else:
            print(f"❌ WebUI Error ({response.status_code}): {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def process_file(file_path):
    PROCESSING_DIR.mkdir(parents=True, exist_ok=True)
    processing_path = PROCESSING_DIR / file_path.name
    shutil.move(str(file_path), str(processing_path))
    
    if upload_to_webui(processing_path):
        shutil.move(str(processing_path), str(PROCESSED_DIR / file_path.name))
        print(f"📦 Finalized: {file_path.name}")
    else:
        shutil.move(str(processing_path), str(FAILED_DIR / file_path.name))
        print(f"⚠️ Failed: {file_path.name}")

def main():
    for d in [INBOX_DIR, PROCESSING_DIR, PROCESSED_DIR, FAILED_DIR]:
        d.mkdir(parents=True, exist_ok=True)
        
    print(f"🔍 SaleH Native Watcher v5.3 Started")
    
    while True:
        try:
            for f in INBOX_DIR.glob("*"):
                if f.is_file() and not f.name.startswith("."):
                    process_file(f)
            time.sleep(5)
        except Exception as e:
            print(f"Runtime error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()
