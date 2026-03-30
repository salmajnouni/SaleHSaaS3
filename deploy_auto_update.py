#!/usr/bin/env python3
"""
deploy_auto_update.py - تنصيب وتفعيل نظام التحديث الذاتي للقوانين
====================================================================
1. يرفع workflow التحديث الذاتي إلى n8n
2. يفعّل الجدولة الأسبوعية
3. يشغّل أول تحديث فوري (اختياري)

الاستخدام:
  python deploy_auto_update.py              # تنصيب + تفعيل
  python deploy_auto_update.py --run-now    # تنصيب + تشغيل فوري
"""
import json
import requests
import sys
import os

N8N_URL = os.environ.get("N8N_URL", "http://localhost:5678")
API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2MzM4ZjBkYi1kOTIwLTRmMGItOTE3Yi0xZjg3MDAyMDdiNjgiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwianRpIjoiNjkxNDA2MDctZTQ0MC00ZDZiLTk3NjktOWJiNmFhNjkxMTliIiwiaWF0IjoxNzcyNTIwMTYzLCJleHAiOjE3NzUwNzcyMDB9.sET4Cp57eYI5y_w9gfmFiPY260YolvUh9sVIglp7muA"

HEADERS = {
    "X-N8N-API-KEY": API_KEY,
    "Content-Type": "application/json"
}

WORKFLOW_FILE = os.path.join(os.path.dirname(__file__), "n8n_workflows", "saudi_laws_auto_update.json")


def main():
    print("=" * 60)
    print("  🚀 تنصيب نظام التحديث الذاتي للقوانين السعودية")
    print("=" * 60)

    # Load workflow
    print("\n📄 Loading workflow...")
    with open(WORKFLOW_FILE, 'r', encoding='utf-8') as f:
        wf_data = json.load(f)
    print(f"   Nodes: {len(wf_data.get('nodes', []))}")

    # Connect to n8n
    print("\n🔌 Connecting to n8n...")
    try:
        resp = requests.get(f"{N8N_URL}/api/v1/workflows", headers=HEADERS, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        print(f"   ❌ Cannot connect to n8n: {e}")
        print(f"\n   الرجاء استيراد الملف يدوياً من n8n UI:")
        print(f"   {WORKFLOW_FILE}")
        return

    workflows = resp.json().get('data', [])
    print(f"   Found {len(workflows)} existing workflows")

    # Check if auto-update workflow exists
    existing_id = None
    for wf in workflows:
        name = wf.get('name', '')
        if 'Auto-Update' in name or 'التحديث الذاتي' in name:
            existing_id = wf['id']
            print(f"   Found existing: {name} (ID: {existing_id})")
            break

    payload = {
        "name": wf_data.get("name"),
        "nodes": wf_data.get("nodes", []),
        "connections": wf_data.get("connections", {}),
        "settings": wf_data.get("settings", {}),
        "staticData": None
    }

    if existing_id:
        print(f"\n🔄 Updating workflow (ID: {existing_id})...")
        r = requests.put(
            f"{N8N_URL}/api/v1/workflows/{existing_id}",
            headers=HEADERS, json=payload, timeout=30
        )
    else:
        print("\n📤 Creating new workflow...")
        r = requests.post(
            f"{N8N_URL}/api/v1/workflows",
            headers=HEADERS, json=payload, timeout=30
        )

    if r.status_code not in [200, 201]:
        print(f"   ❌ Error: {r.status_code} - {r.text[:300]}")
        return

    wf_id = r.json().get('id', existing_id)
    print(f"   ✅ Workflow ready! ID: {wf_id}")

    # Activate the workflow
    print("\n⚡ Activating workflow...")
    r = requests.patch(
        f"{N8N_URL}/api/v1/workflows/{wf_id}",
        headers=HEADERS,
        json={"active": True},
        timeout=10
    )
    if r.status_code == 200:
        print("   ✅ Workflow activated! (يشتغل كل اثنين 3 صباحاً)")
    else:
        print(f"   ⚠️ Activation: {r.status_code} - activate manually in n8n UI")

    # Run now if requested
    if "--run-now" in sys.argv:
        print("\n🏃 Running first update now...")
        print("   (This will take several minutes)")
        try:
            r = requests.post(
                f"{N8N_URL}/api/v1/workflows/{wf_id}/run",
                headers=HEADERS,
                json={"runData": {}},
                timeout=600
            )
            if r.status_code == 200:
                print("   ✅ Update started!")
            else:
                print(f"   ⚠️ Could not auto-run. Please trigger manually in n8n UI.")
        except Exception as e:
            print(f"   ⚠️ {e} - Please trigger manually.")

    # Summary
    print("\n" + "=" * 60)
    print("  ✅ التنصيب اكتمل بنجاح!")
    print("=" * 60)
    print(f"\n  📋 Workflow: {wf_data.get('name')}")
    print(f"  🆔 ID: {wf_id}")
    print(f"  ⏰ Schedule: Every Monday 3:00 AM (Riyadh)")
    print(f"  🌐 n8n UI: {N8N_URL}")
    print(f"\n  الخطوات التالية:")
    print(f"  1. افتح n8n: {N8N_URL}")
    print(f"  2. اضغط Execute Workflow للتشغيل الفوري")
    print(f"  3. أو انتظر الجدولة التلقائية")
    print(f"\n  للتشغيل المباشر بدون n8n:")
    print(f"  python auto_update_laws.py --dry-run    # معاينة الناقص")
    print(f"  python auto_update_laws.py              # سحب الناقص")
    print(f"  python auto_update_laws.py --report     # تقرير كامل")
    print("=" * 60)


if __name__ == "__main__":
    main()
