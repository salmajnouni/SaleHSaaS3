#!/usr/bin/env python3
"""
RAG comparison test: nomic-embed-text vs qwen3-embedding:0.6b
"""
import requests, json

CHROMADB = "http://localhost:8010/api/v1"
OLLAMA = "http://localhost:11434"
OLD_CID = "8c394725-8a25-4c26-a0d3-4711f554aab8"  # nomic 768-dim
NEW_CID = "86fce70f-0753-4989-9e4c-54d1ded405cd"  # qwen3 1024-dim

QUERIES = [
    ("ما هي حقوق العامل في نظام العمل السعودي؟", "نظام العمل"),
    ("عقوبة الجرائم المعلوماتية في السعودية", "نظام مكافحة جرائم المعلوماتية"),
    ("شروط التسجيل في السجل التجاري", "نظام السجل التجاري"),
    ("صلاحيات مجلس الشورى", "نظام مجلس الشورى"),
    ("مخالفات المرور والغرامات", "نظام المرور"),
    ("نظام ضريبة الدخل ومعدلاتها", "نظام ضريبة الدخل"),
    ("إجراءات التحكيم في المنازعات التجارية", "نظام التحكيم"),
    ("حماية حقوق الملكية الفكرية", "نظام حماية حقوق المؤلف"),
    ("أحكام الإفلاس والتصفية", "نظام الإفلاس"),
    ("تنظيم الهيئة العامة للزكاة والدخل", "الزكاة"),
]

def search(query, model, cid, n=3):
    emb = requests.post(f"{OLLAMA}/api/embeddings", json={"model": model, "prompt": query}).json()["embedding"]
    r = requests.post(f"{CHROMADB}/collections/{cid}/query", json={
        "query_embeddings": [emb], "n_results": n, "include": ["metadatas", "distances"]
    }).json()
    return r

def test_model(name, model, cid):
    print(f"\n{'='*70}")
    print(f"  {name}")
    print(f"{'='*70}")
    correct = 0
    total = len(QUERIES)
    
    for i, (query, expected) in enumerate(QUERIES, 1):
        r = search(query, model, cid)
        top_law = r["metadatas"][0][0].get("law_name", "?") if r["metadatas"][0] else "?"
        top_dist = r["distances"][0][0] if r["distances"][0] else 999
        
        # Check if expected keyword appears in top-3 results
        found = False
        for j in range(min(3, len(r["metadatas"][0]))):
            law = r["metadatas"][0][j].get("law_name", "")
            if expected in law or law in expected:
                found = True
                break
        
        status = "✅" if found else "❌"
        if found:
            correct += 1
        
        print(f"  {status} Q{i}: {query[:50]}")
        print(f"      Top: {top_law} (dist={top_dist:.4f})")
        
        # Show all 3 results
        for j in range(min(3, len(r["metadatas"][0]))):
            law = r["metadatas"][0][j].get("law_name", "?")
            dist = r["distances"][0][j]
            cat = r["metadatas"][0][j].get("category", "?")
            print(f"      [{j+1}] {law} | {cat} | {dist:.4f}")
    
    accuracy = correct / total * 100
    print(f"\n  📊 الدقة: {correct}/{total} = {accuracy:.0f}%")
    return correct, total

print("=" * 70)
print("  مقارنة دقة RAG: nomic-embed-text vs qwen3-embedding:0.6b")
print("=" * 70)

old_correct, old_total = test_model("nomic-embed-text (768-dim) — القديم", "nomic-embed-text", OLD_CID)
new_correct, new_total = test_model("qwen3-embedding:0.6b (1024-dim) — الجديد", "qwen3-embedding:0.6b", NEW_CID)

print(f"\n{'='*70}")
print(f"  النتيجة النهائية")
print(f"{'='*70}")
print(f"  nomic-embed-text:   {old_correct}/{old_total} = {old_correct/old_total*100:.0f}%")
print(f"  qwen3-embedding:    {new_correct}/{new_total} = {new_correct/new_total*100:.0f}%")
improvement = new_correct - old_correct
print(f"  التحسن: +{improvement} أسئلة ({improvement/old_total*100:+.0f}%)")
print(f"{'='*70}")
