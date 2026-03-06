#!/usr/bin/env python3
"""
SaleH SaaS - استيراد الـ Workflows في n8n
الاستخدام: python restore_workflows.py --api-key YOUR_API_KEY
"""
import json
import os
import sys
import argparse
import requests
from pathlib import Path

def load_env(env_file=".env"):
    """قراءة ملف .env"""
    env = {}
    if os.path.exists(env_file):
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, val = line.partition("=")
                    env[key.strip()] = val.strip()
    return env

def import_workflow(api_key: str, workflow_path: Path, n8n_url: str = "http://localhost:5678") -> bool:
    """استيراد workflow واحد"""
    headers = {"X-N8N-API-KEY": api_key, "Content-Type": "application/json"}
    
    with open(workflow_path, encoding='utf-8') as f:
        content = f.read()
    
    # قراءة بـ strict=False لتجاوز control characters
    wf = json.loads(content, strict=False)
    
    # إزالة الحقول التي يرفضها n8n API v1
    # يقبل فقط: name, nodes, connections, settings, staticData
    for field in ["id", "createdAt", "updatedAt", "versionId", "pinData", "active", "tags"]:
        wf.pop(field, None)
    
    try:
        r = requests.post(f"{n8n_url}/api/v1/workflows", headers=headers, json=wf, timeout=10)
        if r.status_code in (200, 201):
            data = r.json()
            name = data.get("name", workflow_path.stem)
            wf_id = data.get("id", "?")
            print(f"  ✅ [{wf_id}] {name}")
            return True
        else:
            print(f"  ❌ {workflow_path.name}: HTTP {r.status_code} — {r.text[:100]}")
            return False
    except Exception as e:
        print(f"  ❌ {workflow_path.name}: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="استيراد workflows في n8n")
    parser.add_argument("--api-key", help="n8n API Key")
    parser.add_argument("--n8n-url", default="http://localhost:5678", help="n8n URL")
    parser.add_argument("--workflows-dir", default="n8n_workflows", help="مجلد الـ workflows")
    args = parser.parse_args()

    # قراءة الـ API Key من .env إذا لم يُعطَ
    api_key = args.api_key
    if not api_key:
        env = load_env()
        api_key = env.get("N8N_API_KEY", "")
    
    if not api_key or "REPLACE_WITH" in api_key:
        print("❌ يجب تحديد N8N_API_KEY")
        print("")
        print("الخيارات:")
        print("  1. python restore_workflows.py --api-key YOUR_KEY")
        print("  2. أضف N8N_API_KEY=YOUR_KEY في ملف .env")
        print("")
        print("للحصول على الـ Key:")
        print("  افتح http://localhost:5678 → Settings → n8n API → Add API Key")
        sys.exit(1)

    # التحقق من اتصال n8n
    try:
        r = requests.get(f"{args.n8n_url}/healthz", timeout=5)
        if r.status_code != 200:
            raise Exception(f"HTTP {r.status_code}")
        print(f"✅ n8n متصل على {args.n8n_url}")
    except Exception as e:
        print(f"❌ لا يمكن الاتصال بـ n8n: {e}")
        print(f"   تأكد من تشغيل: docker compose up -d")
        sys.exit(1)

    # البحث عن ملفات الـ workflows
    workflows_dir = Path(args.workflows_dir)
    if not workflows_dir.exists():
        print(f"❌ المجلد غير موجود: {workflows_dir}")
        sys.exit(1)

    workflow_files = sorted(workflows_dir.glob("*.json"))
    if not workflow_files:
        print(f"❌ لا توجد ملفات .json في {workflows_dir}")
        sys.exit(1)

    print(f"\nاستيراد {len(workflow_files)} workflows...\n")
    
    success = 0
    failed = 0
    for wf_file in workflow_files:
        if import_workflow(api_key, wf_file, args.n8n_url):
            success += 1
        else:
            failed += 1

    print(f"\n{'='*50}")
    print(f"النتيجة: {success} مستورد ✅  |  {failed} فشل ❌")
    print(f"{'='*50}")
    
    if success > 0:
        print(f"\nافتح n8n: {args.n8n_url}")
        print("ستجد الـ workflows في قسم Workflows")

if __name__ == "__main__":
    main()
