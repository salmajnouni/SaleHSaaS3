"""
SaleH SaaS - Legal Document Ingestion Pipeline
================================================
يستقبل ملفات PDF/Word/Excel ويقطّعها ذكياً حسب المواد
ويخزنها في ChromaDB جاهزة للبحث RAG

الاستخدام في Open WebUI:
  - اذهب إلى Admin > Pipelines
  - أضف Pipeline جديدة من URL: http://pipelines:9099
  - أو ارفع هذا الملف مباشرة
"""

import os
import re
import json
import hashlib
import requests
from typing import List, Dict, Any, Optional, Generator, Iterator
from pydantic import BaseModel


class Pipeline:
    class Valves(BaseModel):
        CHROMADB_URL: str = "http://chromadb:8000"
        TIKA_URL: str = "http://tika:9998"
        COLLECTION_NAME: str = "saleh_legal_docs"
        OLLAMA_URL: str = "http://host.docker.internal:11434"
        EMBEDDING_MODEL: str = "qwen3-embedding:0.6b"
        CHUNK_SIZE: int = 1000
        CHUNK_OVERLAP: int = 100
        MIN_CHUNK_LENGTH: int = 50

    def __init__(self):
        self.name = "SaleH Legal Ingest"
        self.valves = self.Valves()
        self._ensure_collection()

    def _ensure_collection(self):
        """إنشاء collection في ChromaDB إذا لم تكن موجودة"""
        try:
            resp = requests.get(
                f"{self.valves.CHROMADB_URL}/api/v1/collections",
                timeout=5
            )
            if resp.status_code == 200:
                collections = [c["name"] for c in resp.json().get("collections", [])]
                if self.valves.COLLECTION_NAME not in collections:
                    requests.post(
                        f"{self.valves.CHROMADB_URL}/api/v1/collections",
                        json={"name": self.valves.COLLECTION_NAME, "metadata": {"hnsw:space": "cosine"}},
                        timeout=5
                    )
        except Exception:
            pass

    def _extract_text_from_file(self, file_path: str) -> str:
        """استخراج النص من الملف عبر Apache Tika"""
        try:
            with open(file_path, "rb") as f:
                resp = requests.put(
                    f"{self.valves.TIKA_URL}/tika",
                    data=f,
                    headers={"Accept": "text/plain", "Accept-Language": "ar,en"},
                    timeout=60
                )
            if resp.status_code == 200:
                return resp.text
        except Exception as e:
            print(f"Tika error: {e}")
        return ""

    def _smart_chunk_legal_text(self, text: str, doc_name: str) -> List[Dict]:
        """
        تقطيع ذكي للنصوص القانونية السعودية
        يتعرف على: المادة، الفصل، الباب، البند
        """
        chunks = []

        # أنماط التعرف على هيكل القانون السعودي
        article_patterns = [
            r'(?:المادة\s+(?:الأولى|الثانية|الثالثة|الرابعة|الخامسة|السادسة|السابعة|الثامنة|التاسعة|العاشرة))',
            r'(?:المادة\s+\(?\d+\)?)',
            r'(?:مادة\s+\(?\d+\)?)',
            r'(?:الفصل\s+(?:الأول|الثاني|الثالث|الرابع|الخامس|\d+))',
            r'(?:الباب\s+(?:الأول|الثاني|الثالث|الرابع|الخامس|\d+))',
        ]

        combined_pattern = '|'.join(f'({p})' for p in article_patterns)

        # تقسيم النص حسب المواد
        splits = re.split(f'(?={combined_pattern})', text, flags=re.UNICODE)

        for i, split in enumerate(splits):
            split = split.strip()
            if len(split) < self.valves.MIN_CHUNK_LENGTH:
                continue

            # استخراج رقم المادة/الفصل
            article_match = re.match(combined_pattern, split, re.UNICODE)
            article_ref = article_match.group(0) if article_match else f"قسم {i+1}"

            # إذا كانت المادة طويلة جداً، قسّمها بالفقرات
            if len(split) > self.valves.CHUNK_SIZE * 2:
                sub_chunks = self._split_by_paragraphs(split)
                for j, sub in enumerate(sub_chunks):
                    if len(sub) >= self.valves.MIN_CHUNK_LENGTH:
                        chunks.append({
                            "text": sub,
                            "article_ref": f"{article_ref} (جزء {j+1})",
                            "doc_name": doc_name,
                            "chunk_index": len(chunks)
                        })
            else:
                chunks.append({
                    "text": split,
                    "article_ref": article_ref,
                    "doc_name": doc_name,
                    "chunk_index": len(chunks)
                })

        # إذا لم يُعثر على مواد، قسّم بالفقرات
        if not chunks:
            chunks = self._fallback_chunking(text, doc_name)

        return chunks

    def _split_by_paragraphs(self, text: str) -> List[str]:
        """تقسيم بالفقرات مع تداخل"""
        paragraphs = [p.strip() for p in re.split(r'\n{2,}', text) if p.strip()]
        result = []
        current = ""
        for para in paragraphs:
            if len(current) + len(para) < self.valves.CHUNK_SIZE:
                current += "\n\n" + para if current else para
            else:
                if current:
                    result.append(current)
                current = para
        if current:
            result.append(current)
        return result

    def _fallback_chunking(self, text: str, doc_name: str) -> List[Dict]:
        """تقطيع احتياطي بالحجم مع تداخل"""
        chunks = []
        size = self.valves.CHUNK_SIZE
        overlap = self.valves.CHUNK_OVERLAP
        words = text.split()

        i = 0
        chunk_idx = 0
        while i < len(words):
            chunk_words = words[i:i + size]
            chunk_text = " ".join(chunk_words)
            if len(chunk_text) >= self.valves.MIN_CHUNK_LENGTH:
                chunks.append({
                    "text": chunk_text,
                    "article_ref": f"قسم {chunk_idx + 1}",
                    "doc_name": doc_name,
                    "chunk_index": chunk_idx
                })
            i += size - overlap
            chunk_idx += 1

        return chunks

    def _get_embedding(self, text: str) -> Optional[List[float]]:
        """الحصول على Embedding من Ollama"""
        try:
            resp = requests.post(
                f"{self.valves.OLLAMA_URL}/api/embeddings",
                json={"model": self.valves.EMBEDDING_MODEL, "prompt": text},
                timeout=30
            )
            if resp.status_code == 200:
                return resp.json().get("embedding", [])
        except Exception as e:
            print(f"Embedding error: {e}")
        return None

    def _store_chunks(self, chunks: List[Dict], doc_id: str) -> int:
        """تخزين الـ chunks في ChromaDB"""
        stored = 0
        batch_size = 10

        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            ids, embeddings, documents, metadatas = [], [], [], []

            for chunk in batch:
                # توليد ID فريد
                chunk_id = hashlib.md5(
                    f"{doc_id}_{chunk['chunk_index']}".encode()
                ).hexdigest()

                embedding = self._get_embedding(chunk["text"])
                if not embedding:
                    continue

                ids.append(chunk_id)
                embeddings.append(embedding)
                documents.append(chunk["text"])
                metadatas.append({
                    "doc_name": chunk["doc_name"],
                    "article_ref": chunk["article_ref"],
                    "doc_id": doc_id,
                    "chunk_index": chunk["chunk_index"]
                })

            if ids:
                try:
                    # حذف chunks قديمة لنفس الوثيقة (منع التكرار)
                    requests.post(
                        f"{self.valves.CHROMADB_URL}/api/v1/collections/{self.valves.COLLECTION_NAME}/delete",
                        json={"where": {"doc_id": {"$eq": doc_id}}},
                        timeout=10
                    )
                    # إضافة chunks الجديدة
                    resp = requests.post(
                        f"{self.valves.CHROMADB_URL}/api/v1/collections/{self.valves.COLLECTION_NAME}/add",
                        json={
                            "ids": ids,
                            "embeddings": embeddings,
                            "documents": documents,
                            "metadatas": metadatas
                        },
                        timeout=30
                    )
                    if resp.status_code in (200, 201):
                        stored += len(ids)
                except Exception as e:
                    print(f"ChromaDB store error: {e}")

        return stored

    def pipe(
        self,
        user_message: str,
        model_id: str,
        messages: List[dict],
        body: dict
    ) -> Iterator[str]:
        """
        نقطة الدخول الرئيسية للـ Pipeline
        تُستدعى عند إرسال رسالة في Open WebUI
        """
        # البحث عن ملف مرفق في الرسالة
        files = body.get("files", [])

        if not files:
            yield "لم يتم إرفاق أي ملف. يرجى رفع ملف PDF أو Word للمعالجة."
            return

        results = []
        for file_info in files:
            file_path = file_info.get("path", "")
            file_name = file_info.get("name", "وثيقة")

            if not file_path or not os.path.exists(file_path):
                results.append(f"❌ لم يُعثر على الملف: {file_name}")
                continue

            yield f"⏳ جاري معالجة: **{file_name}**\n\n"

            # استخراج النص
            yield "📄 استخراج النص...\n"
            text = self._extract_text_from_file(file_path)

            if not text or len(text) < 100:
                results.append(f"❌ فشل استخراج النص من: {file_name}")
                continue

            yield f"✅ تم استخراج {len(text):,} حرف\n\n"

            # تقطيع ذكي
            yield "✂️ تقطيع النص حسب المواد...\n"
            doc_id = hashlib.md5(file_name.encode()).hexdigest()
            chunks = self._smart_chunk_legal_text(text, file_name)
            yield f"✅ تم إنشاء {len(chunks)} مقطع\n\n"

            # تخزين في ChromaDB
            yield f"💾 جاري التخزين في قاعدة المعرفة ({len(chunks)} مقطع)...\n"
            stored = self._store_chunks(chunks, doc_id)

            results.append(
                f"✅ **{file_name}**: تم تخزين {stored} مقطع من أصل {len(chunks)}"
            )

        yield "\n---\n## نتائج المعالجة\n\n"
        for r in results:
            yield f"{r}\n\n"

        yield "\n🎉 **اكتمل! يمكنك الآن السؤال عن محتوى هذه الوثائق.**"
