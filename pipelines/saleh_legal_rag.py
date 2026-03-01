"""
SaleH SaaS - Legal RAG Pipeline
=================================
يبحث في ChromaDB عن المقاطع ذات الصلة بسؤال المستخدم
ويحقنها كسياق قبل إرسال السؤال للنموذج

هذه هي Pipeline الرئيسية التي تعمل في كل محادثة
"""

import os
import re
import json
import requests
from typing import List, Dict, Any, Optional, Generator, Iterator
from pydantic import BaseModel


class Pipeline:
    class Valves(BaseModel):
        CHROMADB_URL: str = "http://chromadb:8000"
        OLLAMA_URL: str = "http://host.docker.internal:11434"
        EMBEDDING_MODEL: str = "nomic-embed-text:latest"
        COLLECTION_NAME: str = "saleh_legal_docs"
        TOP_K: int = 5
        MIN_RELEVANCE_SCORE: float = 0.3
        ENABLE_RAG: bool = True
        SYSTEM_PROMPT: str = """أنت مساعد قانوني متخصص في الأنظمة والتشريعات السعودية.
عند الإجابة:
1. استند دائماً إلى النصوص القانونية المقدمة في السياق
2. اذكر رقم المادة والنظام المصدر لكل معلومة
3. إذا لم يكن السؤال في نطاق الوثائق المتاحة، وضّح ذلك بصراحة
4. استخدم لغة قانونية دقيقة وواضحة
5. رتّب إجابتك بشكل منظم عند الحاجة"""

    def __init__(self):
        self.name = "SaleH Legal RAG"
        self.valves = self.Valves()

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

    def _search_chromadb(self, query: str, top_k: int = None) -> List[Dict]:
        """البحث في ChromaDB عن أقرب المقاطع للسؤال"""
        if top_k is None:
            top_k = self.valves.TOP_K

        embedding = self._get_embedding(query)
        if not embedding:
            return []

        try:
            resp = requests.post(
                f"{self.valves.CHROMADB_URL}/api/v1/collections/{self.valves.COLLECTION_NAME}/query",
                json={
                    "query_embeddings": [embedding],
                    "n_results": top_k,
                    "include": ["documents", "metadatas", "distances"]
                },
                timeout=15
            )

            if resp.status_code == 200:
                data = resp.json()
                results = []
                docs = data.get("documents", [[]])[0]
                metas = data.get("metadatas", [[]])[0]
                distances = data.get("distances", [[]])[0]

                for doc, meta, dist in zip(docs, metas, distances):
                    # تحويل المسافة إلى نسبة تشابه (cosine)
                    similarity = 1 - dist
                    if similarity >= self.valves.MIN_RELEVANCE_SCORE:
                        results.append({
                            "text": doc,
                            "doc_name": meta.get("doc_name", "وثيقة"),
                            "article_ref": meta.get("article_ref", ""),
                            "similarity": round(similarity, 3)
                        })

                return results
        except Exception as e:
            print(f"ChromaDB search error: {e}")

        return []

    def _build_context(self, results: List[Dict]) -> str:
        """بناء نص السياق من نتائج البحث"""
        if not results:
            return ""

        context_parts = ["## الوثائق القانونية ذات الصلة:\n"]

        # تجميع حسب الوثيقة
        docs_map = {}
        for r in results:
            doc_name = r["doc_name"]
            if doc_name not in docs_map:
                docs_map[doc_name] = []
            docs_map[doc_name].append(r)

        for doc_name, chunks in docs_map.items():
            context_parts.append(f"\n### {doc_name}\n")
            for chunk in chunks:
                article = chunk.get("article_ref", "")
                if article:
                    context_parts.append(f"**{article}:**\n{chunk['text']}\n")
                else:
                    context_parts.append(f"{chunk['text']}\n")

        return "\n".join(context_parts)

    def _is_legal_query(self, message: str) -> bool:
        """تحديد إذا كان السؤال يحتاج بحثاً في القوانين"""
        # كلمات مفتاحية تشير لسؤال قانوني
        legal_keywords = [
            "نظام", "قانون", "لائحة", "مادة", "تشريع", "حكم", "عقوبة",
            "غرامة", "جزاء", "شرط", "اشتراط", "يُلزم", "يُحظر", "يُجيز",
            "حق", "واجب", "التزام", "مسؤولية", "تعريف", "ما هو", "ما هي",
            "كيف", "متى", "من يحق", "هل يجوز", "هل يُسمح", "ما حكم"
        ]
        message_lower = message.lower()
        return any(kw in message for kw in legal_keywords)

    def pipe(
        self,
        user_message: str,
        model_id: str,
        messages: List[dict],
        body: dict
    ) -> Iterator[str]:
        """
        نقطة الدخول - تعمل على كل رسالة في المحادثة
        """
        if not self.valves.ENABLE_RAG:
            # RAG معطّل - أرسل الرسالة مباشرة
            yield user_message
            return

        # البحث في ChromaDB
        results = self._search_chromadb(user_message)

        if not results:
            # لا توجد نتائج - أرسل الرسالة بدون سياق
            yield user_message
            return

        # بناء السياق
        context = self._build_context(results)

        # حقن السياق في الرسالة
        enriched_message = f"""{context}

---

## السؤال:
{user_message}

## التعليمات:
أجب على السؤال بناءً على الوثائق القانونية المذكورة أعلاه فقط.
اذكر المادة والنظام المصدر لكل معلومة تذكرها.
"""

        # تحديث system prompt
        if "messages" in body and body["messages"]:
            # إضافة system prompt إذا لم يكن موجوداً
            has_system = any(m.get("role") == "system" for m in body["messages"])
            if not has_system:
                body["messages"].insert(0, {
                    "role": "system",
                    "content": self.valves.SYSTEM_PROMPT
                })

        yield enriched_message

    def inlet(self, body: dict, user: Optional[dict] = None) -> dict:
        """
        معالجة الطلب قبل وصوله للنموذج
        يُضاف السياق القانوني هنا
        """
        messages = body.get("messages", [])
        if not messages:
            return body

        # آخر رسالة من المستخدم
        last_user_msg = None
        for msg in reversed(messages):
            if msg.get("role") == "user":
                last_user_msg = msg
                break

        if not last_user_msg:
            return body

        user_text = last_user_msg.get("content", "")
        if isinstance(user_text, list):
            # رسالة تحتوي على نص وصور
            for part in user_text:
                if isinstance(part, dict) and part.get("type") == "text":
                    user_text = part.get("text", "")
                    break

        if not user_text:
            return body

        # البحث في ChromaDB
        results = self._search_chromadb(user_text)

        if not results:
            return body

        # بناء السياق
        context = self._build_context(results)

        # إضافة system prompt قانوني
        has_system = any(m.get("role") == "system" for m in messages)
        if not has_system:
            messages.insert(0, {
                "role": "system",
                "content": self.valves.SYSTEM_PROMPT
            })

        # حقن السياق في رسالة المستخدم
        original_content = last_user_msg["content"]
        if isinstance(original_content, str):
            last_user_msg["content"] = f"{context}\n\n---\n\n**السؤال:** {original_content}"
        elif isinstance(original_content, list):
            for part in original_content:
                if isinstance(part, dict) and part.get("type") == "text":
                    part["text"] = f"{context}\n\n---\n\n**السؤال:** {part['text']}"
                    break

        body["messages"] = messages
        return body
