"""
SaleH SaaS - Legal RAG Pipeline & MCP Tool
==========================================

هذا الملف يخدم غرضين:
1. كـ Pipeline لـ Open WebUI: لحقن السياق القانوني تلقائياً في كل محادثة.
2. كـ MCP Tool Server: لتوفير أداة بحث قانوني يمكن استدعاؤها.

التغييرات:
- استخدام ChromaDB v1 API المتوافق مع النسخة الحالية
- توحيد اسم الـ collection مع المسار الحي: saleh_knowledge
- إضافة pipe() method كاملة للـ streaming
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
        pipelines: List[str] = ["*"]
        CHROMADB_URL: str = "http://host.docker.internal:8010"
        OLLAMA_URL: str = "http://host.docker.internal:11434"
        EMBEDDING_MODEL: str = "qwen3-embedding:0.6b"
        COLLECTION_NAME: str = "saleh_knowledge_qwen3"
        CHROMADB_TENANT: str = "default_tenant"
        CHROMADB_DATABASE: str = "default_database"
        TOP_K: int = 15
        MIN_RELEVANCE_SCORE: float = 0.35
        ENABLE_RAG: bool = True
        SYSTEM_PROMPT: str = """أنت 'صالح'، المساعد القانوني السيادي المتقدم للمملكة العربية السعودية.
مهمتك هي تقديم استشارات قانونية دقيقة بناءً على الأنظمة واللوائح السعودية حصراً.

قواعد الإجابة الصارمة:
1. السيادة والبيانات: جميع إجاباتك يجب أن تعكس الأنظمة المعتمدة في المملكة العربية السعودية (مثل نظام المحاكم التجارية، نظام العمل، نظام الإجراءات الجزائية، إلخ).
2. الاستشهاد الدقيق: عند ذكر أي معلومة قانونية، يجب أن تذكر (رقم المادة، اسم النظام، وتاريخه إن وجد) بناءً على السياق المزود لك.
3. الأمانة العلمية: إذا لم تجد نصاً صريحاً في 'الوثائق القانونية ذات الصلة' المزودة لك، قل: 'بناءً على الوثائق المتاحة في النظام حالياً، لا يوجد نص مباشر يتناول هذا السؤال، ولكن وبشكل عام في الأنظمة السعودية...'
4. الدقة اللغوية: استخدم المصطلحات القانونية السعودية المعتمدة (مثل: 'المنظم' بدلاً من 'المشرع').
5. الهيكل: رتب إجابتك في نقاط واضحة مع تبويب المواد القانونية."""

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

    def _get_collection_id(self) -> Optional[str]:
        """الحصول على collection ID من ChromaDB v1"""
        try:
            url = f"{self.valves.CHROMADB_URL}/api/v1/collections/{self.valves.COLLECTION_NAME}"
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                return resp.json().get("id")
        except Exception as e:
            print(f"ChromaDB collection lookup error: {e}", file=sys.stderr)
        return None

    def _search_chromadb(self, query: str, top_k: int = None) -> List[Dict]:
        if top_k is None:
            top_k = self.valves.TOP_K

        embedding = self._get_embedding(query)
        if not embedding:
            return []

        collection_id = self._get_collection_id()
        if not collection_id:
            print("ChromaDB: collection not found", file=sys.stderr)
            return []

        try:
            url = f"{self.valves.CHROMADB_URL}/api/v1/collections/{collection_id}/query"
            resp = requests.post(
                url,
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
                            "doc_name": meta.get("doc_name", meta.get("law_name", "وثيقة")),
                            "article_ref": meta.get("article_ref", meta.get("source", "")),
                            "similarity": round(similarity, 3)
                        })
                return results
            else:
                print(f"ChromaDB query error {resp.status_code}: {resp.text[:200]}", file=sys.stderr)
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
                    context_parts.append(f"**{article}:**\n{chunk.get('text', '')}\n")
                else:
                    context_parts.append(f"{chunk.get('text', '')}\n")

        return "\n".join(context_parts)

    def inlet(self, body: dict, user: Optional[dict] = None) -> dict:
        """حقن السياق القانوني في الرسائل قبل إرسالها للنموذج"""
        if not self.valves.ENABLE_RAG:
            return body

        messages = body.get("messages", [])
        if not messages:
            return body

        # استخراج آخر رسالة من المستخدم
        last_user_msg = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                last_user_msg = msg.get("content", "")
                break

        if not last_user_msg:
            return body

        # البحث في ChromaDB
        results = self._search_chromadb(last_user_msg)
        if not results:
            return body

        # بناء السياق
        context = self._build_context(results)

        # إضافة system message مع السياق
        system_msg = {
            "role": "system",
            "content": f"{self.valves.SYSTEM_PROMPT}\n\n{context}"
        }

        # إضافة أو تحديث system message
        if messages and messages[0].get("role") == "system":
            messages[0]["content"] = f"{self.valves.SYSTEM_PROMPT}\n\n{context}"
        else:
            messages.insert(0, system_msg)

        body["messages"] = messages
        return body

    def pipe(self, user_message: str, model_id: str, messages: List[dict], body: dict) -> Iterator[str]:
        """تمرير الطلب مع السياق القانوني إلى Ollama GPU"""
        # inlet يتولى حقن السياق تلقائياً في messages
        
        # اختيار النموذج الافتراضي (يمكن تغييره من Valves)
        model = body.get("model", "qwen2.5:14b")
        
        try:
            resp = requests.post(
                f"{self.valves.OLLAMA_URL}/api/chat",
                json={
                    "model": model,
                    "messages": body.get("messages", messages),
                    "stream": True,
                    "options": {
                        "temperature": 0.3,
                        "num_ctx": 8192
                    }
                },
                stream=True,
                timeout=120
            )
            
            if resp.status_code == 200:
                for line in resp.iter_lines():
                    if line:
                        chunk = json.loads(line)
                        if "message" in chunk and "content" in chunk["message"]:
                            yield chunk["message"]["content"]
                        if chunk.get("done"):
                            break
            else:
                yield f"❌ خطأ في الاتصال بـ Ollama: {resp.status_code} - {resp.text[:200]}"
                
        except Exception as e:
            yield f"❌ خطأ في معالجة الطلب: {str(e)}"


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

    pipeline_instance = Pipeline()
    results = pipeline_instance._search_chromadb(query)

    if not results:
        output = "لم يتم العثور على نتائج مطابقة في قاعدة المعرفة القانونية."
    else:
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
    main_mcp()
