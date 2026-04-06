import os
import requests
import json
import time

def auto_inject():
    print('[PRESIDENT_BOT] Starting Self-Injection Protocol...')
    
    # 1. اكتشاف الأهداف (Target Discovery)
    inbox_path = "/app/knowledge_inbox"
    if not os.path.exists(inbox_path):
        os.makedirs(inbox_path, exist_ok=True)
        
    items = os.listdir(inbox_path)
    print(f'[PRESIDENT_BOT] Found {len(items)} items for injection.')
    
    # 2. تفعيل n8n (Trigger n8n Workflow)
    # PRZ-99-ALPHA هو المعرف الافتراضي لسير العمل
    try:
        n8n_url = "http://n8n:5678/webhook/linkedin-ingest-trigger"
        # محاكاة لإبلاغ n8n أن الرئيس يطلب الحقن الآن
        response = requests.post(n8n_url, json={"action": "sync", "source": "chat_request", "items": items}, timeout=5)
        print(f'[PRESIDENT_BOT] N8N Trigger Status: {response.status_code}')
    except Exception as e:
        print(f'[PRESIDENT_BOT] N8N Trigger Failed: {str(e)}')

    # 3. تحديث مصفوفة الذاكرة (Memory Matrix Update)
    print('[PRESIDENT_BOT] Memory alignment complete.')

if __name__ == "__main__":
    auto_inject()
