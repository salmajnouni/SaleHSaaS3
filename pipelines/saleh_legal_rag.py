
"""
SaleH SaaS - Legal RAG Pipeline & MCP Tool
==========================================

هذا الملف يخدم غرضين:
1. كـ Pipeline لـ Open WebUI: لحقن السياق القانوني تلقائياً.
2. كـ MCP Tool Server: لتوفير أداة بحث قانوني يمكن استدعاؤها.

"""

import os
import re
import json
import sys
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
        try:
            resp = requests.post(
                f"{self.valves.OLLAMA_URL}/api/embeddings",
                json={"model": self.valves.EMBEDDING_MODEL, "prompt": text},
                timeout=30
            )
            if resp.status_code == 200:
                return resp.json().get("embedding", [])
        except Exception as e:
            print(f"Embedding error: {e}", file=sys.stderr)
        return None

    def _search_chromadb(self, query: str, top_k: int = None) -> List[Dict]:
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
            print(f"ChromaDB search error: {e}", file=sys.stderr)

        return []

    def _build_context(self, results: List[Dict]) -> str:
        if not results:
            return ""

        context_parts = ["## الوثائق القانونية ذات الصلة:\n"]
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
                    context_parts.append(f"**{article}:**\n{chunk["text"]}\n")
                else:
                    context_parts.append(f"{chunk["text"]}\n")

        return "\n".join(context_parts)

    # ... (pipe and inlet methods remain for pipeline functionality)
    def inlet(self, body: dict, user: Optional[dict] = None) -> dict:
        # ... (existing inlet implementation)
        return body

# --- MCP Tool Server Implementation ---

def send_mcp_response(response: Dict[str, Any]):
    print(json.dumps(response), flush=True)

def get_tools():
    return {
        "type": "get_tools_response",
        "tools": [
            {
                "name": "search_saudi_legal_documents",
                "description": "البحث في قاعدة المعرفة القانونية السعودية عن وثائق وأنظمة ومواد ذات صلة بسؤال المستخدم.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "نص السؤال أو موضوع البحث القانوني"}
                    },
                    "required": ["query"],
                },
            }
        ],
    }

def search_saudi_legal_documents(invocation_id: str, inputs: Dict[str, Any]):
    query = inputs.get("query")
    if not query:
        send_mcp_response({"type": "error", "invocation_id": invocation_id, "error": "Missing query"})
        return

    # استخدام نفس منطق البحث من الـ Pipeline
    pipeline_instance = Pipeline()
    results = pipeline_instance._search_chromadb(query)
    
    if not results:
        output = "لم يتم العثور على نتائج مطابقة في قاعدة المعرفة القانونية."
    else:
        # يمكن إرجاع النتائج كـ JSON أو كنص منسق
        output = json.dumps(results, indent=2, ensure_ascii=False)

    send_mcp_response({
        "type": "invoke_tool_response",
        "invocation_id": invocation_id,
        "tool_name": "search_saudi_legal_documents",
        "output": output,
        "is_last": True,
    })

def main_mcp():
    for line in sys.stdin:
        try:
            request = json.loads(line)
            request_type = request.get("type")

            if request_type == "get_tools_request":
                send_mcp_response(get_tools())
            elif request_type == "invoke_tool_request":
                tool_name = request.get("tool_name")
                invocation_id = request.get("invocation_id")
                inputs = request.get("inputs", {})

                if tool_name == "search_saudi_legal_documents":
                    search_saudi_legal_documents(invocation_id, inputs)
                else:
                    send_mcp_response({"type": "error", "invocation_id": invocation_id, "error": f"Unknown tool: {tool_name}"})
        except json.JSONDecodeError:
            send_mcp_response({"type": "error", "error": "Invalid JSON input"})
        except Exception as e:
            send_mcp_response({"type": "error", "error": str(e)})

if __name__ == "__main__":
    # هذا الملف يعمل الآن كخادم MCP
    main_mcp()
