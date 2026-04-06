# fix_chroma_v2.py
import requests
import json
import sys

# التكوين لبيئة Windows (الوصول من الخارج للحاوية)
CHROMA_URL = "http://localhost:8010/api/v1"
COLLECTION_NAME = "saleh_knowledge"

def run_fix():
    print(f"--- [SaleHSaaS3 Chroma Re-Creation] ---")
    
    # 1. محاولة حذف المجموعة إذا كانت موجودة (للتأكد من تصفير الأبعاد)
    try:
        print(f"[*] Deleting existing collection: {COLLECTION_NAME}...")
        resp = requests.delete(f"{CHROMA_URL}/collections/{COLLECTION_NAME}", timeout=10)
        if resp.status_code == 200:
            print(f"[+] Successfully deleted.")
        else:
            print(f"[-] Collection might not exist or already deleted: {resp.status_code}")
    except Exception as e:
        print(f"[!] Delete error (ignoring): {e}")

    # 2. إنشاء المجموعة مع تعريف الأبعاد يدوياً في الميتا
    # ملاحظة: ChromaDB يقوم بتعيينDimension تلقائياً عند أول إضافة، 
    # لكننا سنمرره في الـ metadata كتوثيق.
    print(f"[*] Creating fresh collection: {COLLECTION_NAME} with dimension 768...")
    create_payload = {
        "name": COLLECTION_NAME,
        "metadata": {
            "hnsw:space": "cosine",
            "dimension": 768,
            "description": "Saudi Legal Knowledge Base (Nomic-768)"
        },
        "get_or_create": True
    }
    
    try:
        resp = requests.post(f"{CHROMA_URL}/collections", json=create_payload, timeout=10)
        if resp.status_code in [200, 201]:
            print(f"[OK] Collection '{COLLECTION_NAME}' is ready.")
            print(f"Response: {resp.json()}")
        else:
            print(f"[ERROR] Could not create collection: {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"[FATAL] Connection error: {e}")

if __name__ == "__main__":
    run_fix()
