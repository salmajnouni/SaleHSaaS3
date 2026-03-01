#!/usr/bin/env python3
"""
SaleH Legal RAG - MCP Tool Server
أداة البحث القانوني في الأنظمة السعودية عبر بروتوكول MCP
"""

import requests
from mcp.server.fastmcp import FastMCP

CHROMADB_URL = "http://chromadb:8000"
OLLAMA_URL = "http://host.docker.internal:11434"
EMBEDDING_MODEL = "nomic-embed-text:latest"
COLLECTION_NAME = "saleh_legal_docs"

mcp = FastMCP("saleh-legal-rag")


def get_embedding(text: str):
    try:
        resp = requests.post(
            f"{OLLAMA_URL}/api/embeddings",
            json={"model": EMBEDDING_MODEL, "prompt": text},
            timeout=30,
        )
        if resp.status_code == 200:
            return resp.json().get("embedding", [])
    except Exception:
        pass
    return None


def search_chromadb(query: str, top_k: int = 5):
    embedding = get_embedding(query)
    if not embedding:
        return []
    try:
        resp = requests.post(
            f"{CHROMADB_URL}/api/v1/collections/{COLLECTION_NAME}/query",
            json={
                "query_embeddings": [embedding],
                "n_results": top_k,
                "include": ["documents", "metadatas", "distances"],
            },
            timeout=30,
        )
        if resp.status_code == 200:
            data = resp.json()
            results = []
            docs = data.get("documents", [[]])[0]
            metas = data.get("metadatas", [[]])[0]
            dists = data.get("distances", [[]])[0]
            for doc, meta, dist in zip(docs, metas, dists):
                score = 1 - dist
                if score >= 0.3:
                    results.append({"text": doc, "metadata": meta, "score": score})
            return results
    except Exception:
        pass
    return []


@mcp.tool()
def search_saudi_legal_documents(query: str, top_k: int = 5) -> str:
    """البحث في قاعدة المعرفة القانونية السعودية (نظام العمل، نظام الشركات، نظام التجارة، وغيرها)

    Args:
        query: السؤال أو الموضوع القانوني للبحث عنه
        top_k: عدد النتائج المطلوبة (الافتراضي 5)
    """
    if not query:
        return "يرجى تحديد موضوع البحث."

    results = search_chromadb(query, top_k)

    if not results:
        return f"لم يتم العثور على نتائج لـ: '{query}'\n\nتأكد من رفع الوثائق القانونية إلى قاعدة البيانات أولاً."

    lines = [f"**نتائج البحث القانوني عن: '{query}'**\n"]
    for i, r in enumerate(results, 1):
        meta = r.get("metadata", {})
        source = meta.get("source", "مصدر غير محدد")
        article = meta.get("article", "")
        score = r.get("score", 0)
        text = r.get("text", "")[:500]
        lines.append(f"### النتيجة {i} (درجة التطابق: {score:.0%})")
        lines.append(f"**المصدر:** {source}" + (f" - المادة {article}" if article else ""))
        lines.append(f"\n{text}\n")

    return "\n".join(lines)


@mcp.tool()
def list_legal_collections() -> str:
    """عرض قائمة المجموعات القانونية المتاحة في قاعدة البيانات"""
    try:
        resp = requests.get(f"{CHROMADB_URL}/api/v1/collections", timeout=10)
        if resp.status_code == 200:
            collections = resp.json()
            if not collections:
                return "لا توجد مجموعات في قاعدة البيانات بعد."
            lines = ["**المجموعات القانونية المتاحة:**\n"]
            for c in collections:
                lines.append(f"- **{c.get('name', 'غير محدد')}**")
            return "\n".join(lines)
    except Exception as e:
        return f"خطأ في الاتصال بـ ChromaDB: {str(e)}"
    return "تعذر الاتصال بقاعدة البيانات."


if __name__ == "__main__":
    mcp.run()
