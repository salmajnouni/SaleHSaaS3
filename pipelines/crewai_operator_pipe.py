"""
title: CrewAI Assistant - SaleHSaaS
description: وكيل CrewAI داخل SaleHSaaS مع دعم RAG من ChromaDB وبحث ويب عبر SearXNG.
author: Saleh Almajnouni
version: 3.0
"""

import re
import requests
import logging
from typing import Optional, Dict, List, Union, Generator, Iterator
from pydantic import BaseModel, Field

# كلمات مفتاحية تشير لطلب البحث (عربي + إنجليزي)
SEARCH_TRIGGERS = re.compile(
    r"(ابحث|بحث|اعثر|اوجد|ابحث في الانترنت|ابحث في النت|search|find online|look up|google|web search)",
    re.IGNORECASE,
)


class Pipeline:
    class Valves(BaseModel):
        pipelines: List[str] = ["*"]
        target_models: List[str] = ["crewai_operator_pipe", "crewai_operator"]
        enable_rag: bool = False
        enable_web_search: bool = True
        searxng_url: str = Field(
            default="http://salehsaas_searxng:8080",
            description="عنوان SearXNG داخل Docker network",
        )
        searxng_results: int = Field(default=3, description="عدد نتائج البحث")
        chromadb_url: str = Field(
            default="http://salehsaas_chromadb:8010",
            description="عنوان ChromaDB داخل Docker network",
        )
        ollama_url: str = Field(
            default="http://192.168.1.13:11434",
            description="عنوان Ollama للتضمين",
        )
        collection_name: str = Field(
            default="saleh_knowledge_qwen3",
            description="اسم مجموعة ChromaDB",
        )
        embedding_model: str = Field(
            default="qwen3-embedding:0.6b",
            description="نموذج التضمين",
        )
        top_k: int = Field(default=5, description="عدد نتائج RAG")
        min_score: float = Field(default=0.40, description="أدنى درجة تشابه")
        timeout: int = Field(default=20, description="مهلة استدعاءات RAG")
        system_prompt_addition: str = Field(
            default=(
                "أنت وكيل CrewAI داخل SaleHSaaS. "
                "أجب كخبير عملي في بناء Agents, Tasks, Crews, Tools, Memory وFlows. "
                "إذا كان السؤال يتطلب تنفيذ مهام ثقيلة أو تشغيل backend workflows، "
                "اشرح الخطوات بصيغة تنفيذية واضحة. "
                "لا تذكر تفاصيل داخلية عن البنية التحتية إلا عند الطلب."
            ),
            description="تعليمات الوكيل الخاصة",
        )

    def __init__(self):
        self.name = "CrewAI Assistant - SaleHSaaS"
        self.valves = self.Valves()
        self.log = logging.getLogger("crewai_operator_pipe")

    def _is_target_model(self, model_id: str, body: dict) -> bool:
        current_model = (body or {}).get("model", model_id or "")
        return current_model in self.valves.target_models

    def _normalize_content(self, content) -> str:
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts: List[str] = []
            for block in content:
                if isinstance(block, str):
                    parts.append(block)
                    continue
                if not isinstance(block, dict):
                    continue
                block_type = (block.get("type") or "").lower()
                if block_type in {"text", "input_text"}:
                    text_value = block.get("text") or block.get("input_text")
                    if isinstance(text_value, str) and text_value.strip():
                        parts.append(text_value)
            return "\n".join(parts).strip()
        if isinstance(content, dict):
            for key in ("text", "content", "value"):
                value = content.get(key)
                if isinstance(value, str):
                    return value
        return ""

    def _normalize_messages(self, messages: List[dict]) -> List[dict]:
        normalized: List[dict] = []
        for msg in messages or []:
            if not isinstance(msg, dict):
                continue
            role = msg.get("role", "user")
            normalized.append(
                {
                    "role": role,
                    "content": self._normalize_content(msg.get("content", "")),
                }
            )
        return normalized

    # ── SearXNG ──────────────────────────────────────────────────────────────

    def _search_web(self, query: str) -> List[Dict]:
        """استعلم SearXNG وأعد قائمة نتائج مبسطة."""
        if not self.valves.enable_web_search:
            return []
        try:
            resp = requests.get(
                f"{self.valves.searxng_url}/search",
                params={
                    "q": query,
                    "format": "json",
                    "language": "auto",
                    "safesearch": "0",
                    "categories": "general",
                },
                timeout=10,
                headers={"Accept": "application/json"},
            )
            if resp.status_code != 200:
                self.log.warning(f"SearXNG returned {resp.status_code}")
                return []
            data = resp.json()
            results = []
            for item in data.get("results", [])[: self.valves.searxng_results]:
                results.append(
                    {
                        "title": item.get("title", ""),
                        "url": item.get("url", ""),
                        "content": item.get("content", ""),
                    }
                )
            return results
        except Exception as e:
            self.log.warning(f"SearXNG error: {e}")
            return []

    def _build_web_context(self, results: List[Dict]) -> str:
        if not results:
            return ""
        lines = ["\n\n[نتائج بحث من الإنترنت]"]
        for i, item in enumerate(results, 1):
            lines.append(
                f"\n{i}. {item['title']}\n   {item['url']}\n   {item['content']}"
            )
        lines.append("\n[نهاية نتائج البحث]\n")
        return "\n".join(lines)

    # ── RAG (ChromaDB) ───────────────────────────────────────────────────────

    def _get_embedding(self, text: str) -> Optional[List[float]]:
        try:
            resp = requests.post(
                f"{self.valves.ollama_url}/api/embeddings",
                json={"model": self.valves.embedding_model, "prompt": text},
                timeout=10,
            )
            if resp.status_code == 200:
                return resp.json().get("embedding", [])
        except Exception as e:
            self.log.warning(f"Embedding error: {e}")
        return None

    def _get_collection_id(self) -> Optional[str]:
        try:
            resp = requests.get(
                f"{self.valves.chromadb_url}/api/v1/collections/{self.valves.collection_name}",
                timeout=self.valves.timeout,
            )
            if resp.status_code == 200:
                return resp.json().get("id")
        except Exception as e:
            self.log.warning(f"ChromaDB lookup error: {e}")
        return None

    def _search_chromadb(self, query: str) -> List[Dict]:
        embedding = self._get_embedding(query)
        if not embedding:
            return []
        collection_id = self._get_collection_id()
        if not collection_id:
            return []
        try:
            resp = requests.post(
                f"{self.valves.chromadb_url}/api/v1/collections/{collection_id}/query",
                json={
                    "query_embeddings": [embedding],
                    "n_results": self.valves.top_k,
                    "include": ["documents", "metadatas", "distances"],
                },
                timeout=self.valves.timeout,
            )
            if resp.status_code != 200:
                return []
            data = resp.json()
            docs = data.get("documents", [[]])[0]
            metas = data.get("metadatas", [[]])[0]
            distances = data.get("distances", [[]])[0]
            results = []
            for doc, meta, dist in zip(docs, metas, distances):
                similarity = 1 - dist
                if similarity >= self.valves.min_score:
                    results.append(
                        {
                            "text": doc,
                            "source": (meta or {}).get("doc_name", (meta or {}).get("source", "وثيقة")),
                            "similarity": round(similarity, 3),
                        }
                    )
            return results
        except Exception as e:
            self.log.warning(f"ChromaDB search error: {e}")
            return []

    def _build_rag_context(self, results: List[Dict]) -> str:
        if not results:
            return ""
        lines = ["\n\n[سياق معرفي داعم من قاعدة المعرفة]"]
        for i, item in enumerate(results, 1):
            lines.append(
                f"\n- مرجع {i} | المصدر: {item['source']} | التشابه: {item['similarity']}\n{item['text']}"
            )
        lines.append("\n[نهاية السياق]\n")
        return "\n".join(lines)

    # ── pipe ─────────────────────────────────────────────────────────────────

    def pipe(
        self,
        user_message: str,
        model_id: str,
        messages: List[dict],
        body: dict,
    ) -> Union[dict, str, Generator, Iterator]:

        if not self._is_target_model(model_id, body):
            return body

        if not isinstance(messages, list) or not messages:
            return body

        messages = self._normalize_messages(messages)

        prompt_text = (user_message or "").strip()
        if not prompt_text:
            for msg in reversed(messages):
                if msg.get("role") == "user":
                    prompt_text = (msg.get("content") or "").strip()
                    if prompt_text:
                        break

        if not prompt_text:
            return body

        # ── web search ───────────────────────────────────────────────────────
        extra_context = ""

        if self.valves.enable_web_search and SEARCH_TRIGGERS.search(prompt_text):
            web_results = self._search_web(prompt_text)
            extra_context += self._build_web_context(web_results)

        # ── RAG ──────────────────────────────────────────────────────────────
        if self.valves.enable_rag:
            rag_results = self._search_chromadb(prompt_text)
            extra_context += self._build_rag_context(rag_results)

        enhanced_user_message = prompt_text + extra_context if extra_context else prompt_text

        modified_messages = []
        has_system = False

        for msg in messages:
            role = msg.get("role")
            if role == "system":
                existing_system = self._normalize_content(msg.get("content", ""))
                modified_messages.append(
                    {
                        "role": "system",
                        "content": f"{existing_system}\n\n{self.valves.system_prompt_addition}",
                    }
                )
                has_system = True
            elif role == "user" and msg is messages[-1]:
                modified_messages.append({"role": "user", "content": enhanced_user_message})
            else:
                modified_messages.append(msg)

        if not has_system:
            modified_messages.insert(
                0,
                {
                    "role": "system",
                    "content": self.valves.system_prompt_addition,
                },
            )

        body["messages"] = modified_messages
        return body
