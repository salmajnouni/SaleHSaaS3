#!/usr/bin/env python3
"""
SaleHSaaS - Saudi Legal Scraper (Manual Run)
سحب القوانين السعودية من هيئة الخبراء وتخزينها في ChromaDB
Same logic as the n8n workflow but runs directly
"""
import requests
import re
import json
import time
import sys
import os
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

LAWS = [
    {"law_id": "08381293-6388-48e2-8ad2-a9a700f2aa94", "law_name": "نظام العمل", "category": "labor_law"},
    {"law_id": "25df73d6-0f49-4dc5-b010-a9a700f2ec1d", "law_name": "نظام مكافحة جرائم المعلوماتية", "category": "cyber_crimes"},
    {"law_id": "6f509360-2c39-4358-ae2a-a9a700f2ed16", "law_name": "نظام التعاملات الإلكترونية", "category": "ecommerce"},
    {"law_id": "c2c05ee1-201a-48de-91e7-a9a700f2d14f", "law_name": "نظام المنافسات والمشتريات الحكومية", "category": "procurement"},
    {"law_id": "23576008-1ce4-4685-ac3e-a9a700f2cb02", "law_name": "نظام ضريبة الدخل", "category": "tax"},
    {"law_id": "ae610645-e094-48ef-814e-aeb4009d244f", "law_name": "نظام الاتصالات وتقنية المعلومات", "category": "telecom"},
    {"law_id": "eda86cc3-3a00-4b90-900d-b1d000c8a863", "law_name": "نظام الاستثمار", "category": "investment"},
    {"law_id": "85364e57-c01e-41ba-8def-a9a700f183e9", "law_name": "نظام المرور", "category": "traffic"},
    {"law_id": "98ee4b51-d398-4323-ae69-b2b8009f3156", "law_name": "نظام السجل التجاري", "category": "commercial_registry"},
    {"law_id": "93e87aa7-f344-4711-b97c-a9a700f1662b", "law_name": "نظام مجلس الوزراء", "category": "government"},
    {"law_id": "b5cf540a-e6ac-426a-b348-a9a700f163de", "law_name": "نظام مجلس الشورى", "category": "shura"},
    {"law_id": "93f81644-fbbc-49ca-b33c-a9a700f16701", "law_name": "نظام المناطق", "category": "regions"},
]

CHROMADB_URL = "http://localhost:8010"
OLLAMA_URL = "http://localhost:11434"
COLLECTION_ID = "86fce70f-0753-4989-9e4c-54d1ded405cd"
EMBED_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text:latest")
BOE_URL = "https://laws.boe.gov.sa/BoeLaws/Laws/LawDetails/{law_id}/1"
CHUNK_SIZE = 800
OVERLAP = 100


def fetch_law(law):
    url = BOE_URL.format(law_id=law["law_id"])
    resp = requests.get(url, timeout=60, verify=False)
    resp.raise_for_status()
    return resp.text


def extract_text(html):
    text = re.sub(r'<script[^>]*>[\s\S]*?</script>', '', html, flags=re.I)
    text = re.sub(r'<style[^>]*>[\s\S]*?</style>', '', text, flags=re.I)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = text.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"')
    text = re.sub(r'\s+', ' ', text).strip()

    for marker in ['نـــص النظـــام', 'نص النظام', 'المادة الأولى']:
        idx = text.find(marker)
        if idx > -1:
            text = text[idx:]
            break

    for footer in ['جميع الحقوق محفوظة', 'go to top', 'Additional Links']:
        idx = text.find(footer)
        if idx > -1:
            text = text[:idx]

    return text.strip()


def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=OVERLAP):
    chunks = []
    start = 0
    idx = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end].strip()
        if len(chunk) > 50:
            chunks.append({"index": idx, "text": chunk})
            idx += 1
        if end >= len(text):
            break
        start += chunk_size - overlap
    return chunks


def get_embedding(text):
    resp = requests.post(f"{OLLAMA_URL}/api/embeddings",
                         json={"model": EMBED_MODEL, "prompt": text},
                         timeout=120)
    resp.raise_for_status()
    return resp.json()["embedding"]


def upsert_to_chromadb(ids, embeddings, documents, metadatas):
    resp = requests.post(
        f"{CHROMADB_URL}/api/v1/collections/{COLLECTION_ID}/upsert",
        json={"ids": ids, "embeddings": embeddings, "documents": documents, "metadatas": metadatas},
        timeout=30
    )
    resp.raise_for_status()
    return resp.json()


def main():
    print("=" * 60)
    print("  سحب القوانين السعودية من هيئة الخبراء")
    print("  Saudi Legal Scraper - Manual Run")
    print("=" * 60)
    print(f"  Embedding model: {EMBED_MODEL}")
    print("  (override via EMBEDDING_MODEL env var if needed)")
    print("=" * 60)

    # Get initial count
    count_before = requests.get(f"{CHROMADB_URL}/api/v1/collections/{COLLECTION_ID}/count").json()
    print(f"\nChromaDB before: {count_before} documents\n")

    total_chunks = 0
    total_errors = 0

    for i, law in enumerate(LAWS, 1):
        print(f"\n[{i}/{len(LAWS)}] {law['law_name']} ({law['category']})")
        try:
            # Fetch
            print("  📥 Fetching...", end=" ", flush=True)
            html = fetch_law(law)
            print(f"OK ({len(html):,} bytes)")

            # Extract
            print("  ✂️  Extracting...", end=" ", flush=True)
            text = extract_text(html)
            print(f"OK ({len(text):,} chars)")

            if len(text) < 100:
                print(f"  ⚠️  Text too short, skipping")
                total_errors += 1
                continue

            # Chunk
            chunks = chunk_text(text)
            print(f"  📦 Chunks: {len(chunks)}")

            # Process each chunk
            for j, chunk in enumerate(chunks):
                chunk_id = f"boe_{law['category']}_c{chunk['index']}"
                print(f"  🧠 [{j+1}/{len(chunks)}] Embedding + Saving {chunk_id}...", end=" ", flush=True)

                embedding = get_embedding(chunk["text"])
                upsert_to_chromadb(
                    ids=[chunk_id],
                    embeddings=[embedding],
                    documents=[chunk["text"]],
                    metadatas=[{
                        "law_name": law["law_name"],
                        "law_id": law["law_id"],
                        "source": "laws.boe.gov.sa",
                        "category": law["category"],
                        "chunk_index": chunk["index"],
                        "ingested_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")
                    }]
                )
                print("✅")
                total_chunks += 1

            print(f"  ✅ {law['law_name']}: {len(chunks)} chunks saved")
            time.sleep(1)  # Be respectful to the server

        except Exception as e:
            print(f"\n  ❌ Error: {e}")
            total_errors += 1

    # Final report
    count_after = requests.get(f"{CHROMADB_URL}/api/v1/collections/{COLLECTION_ID}/count").json()
    print("\n" + "=" * 60)
    print("  📊 التقرير النهائي")
    print("=" * 60)
    print(f"  قوانين معالجة: {len(LAWS)}")
    print(f"  chunks saved:  {total_chunks}")
    print(f"  errors:        {total_errors}")
    print(f"  ChromaDB قبل:  {count_before}")
    print(f"  ChromaDB بعد:  {count_after}")
    print(f"  جديد:          {count_after - count_before}")
    print("=" * 60)


if __name__ == "__main__":
    main()
