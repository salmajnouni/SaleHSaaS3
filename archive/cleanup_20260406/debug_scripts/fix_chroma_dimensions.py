import requests
import json
import sys

# الإعدادات المعتمدة في SaleHSaaS3
CHROMADB_URL = "http://localhost:8010" # المنفذ الخارجي لـ ChromaDB في الويندوز
COLLECTION_NAME = "saleh_knowledge"

def repair_collection():
    print(f"--- [SaleHSaaS3 RAG Repair] ---")
    print(f"Targeting ChromaDB at: {CHROMADB_URL}")
    
    # 1. محاولة الحصول على الـ ID الخاص بالمجموعة الحالية للتحقق من الاتصال
    try:
        url = f"{CHROMADB_URL}/api/v1/collections/{COLLECTION_NAME}"
        print(f"[*] Checking for existing collection: {COLLECTION_NAME}...")
        resp = requests.get(url, timeout=10)
        
        if resp.status_code == 200:
            col_id = resp.json()['id']
            print(f"[*] Found existing collection (ID: {col_id})")
            
            # 2. حذف المجموعة القديمة ذات الأبعاد الخاطئة
            print(f"[!] Deleting mismatched collection to fix dimensions...")
            del_resp = requests.delete(url, timeout=10)
            if del_resp.status_code == 200:
                print(f"[*] Collection deleted successfully.")
            else:
                print(f"[-] Delete status: {del_resp.status_code}")
        else:
            print(f"[*] Collection '{COLLECTION_NAME}' not found. No deletion needed.")
        
        # 3. إنشاء مجموعة جديدة نظيفة
        # ملاحظة: في ChromaDB v1، يتم تحديد أبعاد التضمين تلقائياً عند أول عملية إدخال.
        print(f"[+] Creating fresh collection: {COLLECTION_NAME}")
        create_url = f"{CHROMADB_URL}/api/v1/collections"
        resp = requests.post(create_url, json={"name": COLLECTION_NAME, "metadata": {"hnsw:space": "cosine"}}, timeout=10)
        
        if resp.status_code == 201:
            print(f"✅ SUCCESS: Collection '{COLLECTION_NAME}' is now ready for Nomic-Embed (768 dimensions).")
            print(f"[*] Future ingestions will now use the correct dimensions automatically.")
        else:
            print(f"❌ Error creating collection (Status {resp.status_code}): {resp.text}")

    except requests.exceptions.ConnectionError:
        print(f"❌ Connection Error: Could not reach ChromaDB at {CHROMADB_URL}.")
        print(f"   Please ensure Docker containers are running (docker-compose up -d).")
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")

if __name__ == "__main__":
    repair_collection()
