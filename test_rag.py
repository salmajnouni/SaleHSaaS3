import requests
import os

CHROMADB = "http://localhost:8010"
OLLAMA = "http://localhost:11434"
COLLECTION_ID = "86fce70f-0753-4989-9e4c-54d1ded405cd"
EMBED_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text:latest")

def search(query, n=3):
    res = requests.post(f"{OLLAMA}/api/embeddings", json={"model": EMBED_MODEL, "prompt": query})
    emb = res.json().get("embedding")
    
    url = f"{CHROMADB}/api/v1/collections/{COLLECTION_ID}/query"
    payload = {
        "query_embeddings": [emb], 
        "n_results": n, 
        "include": ["documents", "metadatas", "distances"]
    }
    
    r = requests.post(url, json=payload).json()
    # Debug print if ids are missing
    if "ids" not in r:
        print(f"DEBUG Response Type: {type(r)}")
        print(f"DEBUG Keys: {r.keys()}")
        if "error" in r:
            print(f"DEBUG Error: {r['error']}")
    return r

queries = [
    "ما هي حقوق العامل في نظام العمل السعودي؟",
    "عقوبة الجرائم المعلوماتية في السعودية",
    "شروط التسجيل في السجل التجاري",
    "صلاحيات مجلس الشورى",
    "مخالفات المرور والغرامات",
    "نظام ضريبة الدخل ومعدلاتها",
]

print("=" * 70)
print("  اختبار استرجاع القوانين من ChromaDB")
print(f"  Embedding model: {EMBED_MODEL}")
print("=" * 70)

for i, q in enumerate(queries, 1):
    print(f"\n--- سؤال {i}: {q}")
    r = search(q)
    for j in range(min(3, len(r["ids"][0]))):
        meta = r["metadatas"][0][j]
        dist = r["distances"][0][j]
        doc = r["documents"][0][j][:150]
        law = meta.get("law_name", "?")
        cat = meta.get("category", "?")
        print(f"  [{j+1}] {law} | {cat} | distance={dist:.3f}")
        print(f"      {doc}...")
    print()
