#!/usr/bin/env python3
"""
Ollama Model Builder - MCP Tool Server
أداة إدارة نماذج Ollama عبر بروتوكول MCP
"""

import asyncio
import json
import requests
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

# عنوان Ollama API
OLLAMA_API_URL = "http://host.docker.internal:11434/api"

app = Server("ollama-model-builder")


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_local_models",
            description="عرض قائمة بجميع النماذج المحلية المتاحة في Ollama مع أحجامها",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        types.Tool(
            name="get_model_info",
            description="الحصول على معلومات تفصيلية حول نموذج معين في Ollama",
            inputSchema={
                "type": "object",
                "properties": {
                    "model_name": {
                        "type": "string",
                        "description": "اسم النموذج مثل: llama3.1 أو qwen2:7b",
                    }
                },
                "required": ["model_name"],
            },
        ),
        types.Tool(
            name="pull_model",
            description="تحميل نموذج جديد من Ollama Hub",
            inputSchema={
                "type": "object",
                "properties": {
                    "model_name": {
                        "type": "string",
                        "description": "اسم النموذج للتحميل مثل: mistral أو llama3.2",
                    }
                },
                "required": ["model_name"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:

    if name == "list_local_models":
        try:
            resp = requests.get(f"{OLLAMA_API_URL}/tags", timeout=10)
            resp.raise_for_status()
            data = resp.json()
            models = data.get("models", [])
            if not models:
                return [types.TextContent(type="text", text="لا توجد نماذج محلية في Ollama حالياً.")]
            lines = ["**النماذج المتاحة في Ollama:**\n"]
            for m in models:
                size_gb = m.get("size", 0) / (1024 ** 3)
                lines.append(f"- **{m['name']}** ({size_gb:.1f} GB)")
            return [types.TextContent(type="text", text="\n".join(lines))]
        except Exception as e:
            return [types.TextContent(type="text", text=f"خطأ في الاتصال بـ Ollama: {str(e)}")]

    elif name == "get_model_info":
        model_name = arguments.get("model_name", "")
        try:
            resp = requests.post(
                f"{OLLAMA_API_URL}/show",
                json={"name": model_name},
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            info = json.dumps(data, ensure_ascii=False, indent=2)
            return [types.TextContent(type="text", text=f"**معلومات نموذج {model_name}:**\n```json\n{info}\n```")]
        except Exception as e:
            return [types.TextContent(type="text", text=f"خطأ: {str(e)}")]

    elif name == "pull_model":
        model_name = arguments.get("model_name", "")
        try:
            resp = requests.post(
                f"{OLLAMA_API_URL}/pull",
                json={"name": model_name, "stream": False},
                timeout=300,
            )
            resp.raise_for_status()
            return [types.TextContent(type="text", text=f"تم تحميل نموذج **{model_name}** بنجاح!")]
        except Exception as e:
            return [types.TextContent(type="text", text=f"خطأ في تحميل النموذج: {str(e)}")]

    return [types.TextContent(type="text", text=f"أداة غير معروفة: {name}")]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
