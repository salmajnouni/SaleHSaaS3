#!/usr/bin/env python3
"""
SaleH Legal RAG - MCP Tool Server
أداة البحث القانوني في الأنظمة السعودية عبر بروتوكول MCP
"""

import asyncio
import requests
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

# إعدادات الخدمات
CHROMADB_URL = "http://chromadb:8000"
OLLAMA_URL = "http://host.docker.internal:11434"
EMBEDDING_MODEL = "nomic-embed-text:latest"
COLLECTION_NAME = "saleh_legal_docs"

app = Server("saleh-legal-rag")


def get_embedding(text: str):
    """الحصول على embedding من Ollama"""
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
    """البحث في ChromaDB"""
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


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="search_saudi_legal_documents",
            description="البحث في قاعدة المعرفة القانونية السعودية (نظام العمل، نظام الشركات، نظام التجارة، وغيرها)",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "السؤال أو الموضوع القانوني للبحث عنه",
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "عدد النتائج المطلوبة (الافتراضي: 5)",
                        "default": 5,
                    },
                },
                "required": ["query"],
            },
        ),
        types.Tool(
            name="list_legal_collections",
            description="عرض قائمة المجموعات القانونية المتاحة في قاعدة البيانات",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:

    if name == "search_saudi_legal_documents":
        query = arguments.get("query", "")
        top_k = arguments.get("top_k", 5)

        if not query:
            return [types.TextContent(type="text", text="يرجى تحديد موضوع البحث.")]

        results = search_chromadb(query, top_k)

        if not results:
            return [types.TextContent(
                type="text",
                text=f"لم يتم العثور على نتائج لـ: '{query}'\n\nتأكد من رفع الوثائق القانونية إلى قاعدة البيانات أولاً."
            )]

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

        return [types.TextContent(type="text", text="\n".join(lines))]

    elif name == "list_legal_collections":
        try:
            resp = requests.get(f"{CHROMADB_URL}/api/v1/collections", timeout=10)
            if resp.status_code == 200:
                collections = resp.json()
                if not collections:
                    return [types.TextContent(type="text", text="لا توجد مجموعات في قاعدة البيانات بعد.")]
                lines = ["**المجموعات القانونية المتاحة:**\n"]
                for c in collections:
                    lines.append(f"- **{c.get('name', 'غير محدد')}**")
                return [types.TextContent(type="text", text="\n".join(lines))]
        except Exception as e:
            return [types.TextContent(type="text", text=f"خطأ في الاتصال بـ ChromaDB: {str(e)}")]

    return [types.TextContent(type="text", text=f"أداة غير معروفة: {name}")]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
