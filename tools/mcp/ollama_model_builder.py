#!/usr/bin/env python3
"""
Ollama Model Builder - MCP Tool Server
أداة إدارة نماذج Ollama عبر بروتوكول MCP
"""

import requests
from mcp.server.fastmcp import FastMCP

OLLAMA_API_URL = "http://ollama:11434/api"

mcp = FastMCP("ollama-model-builder")


@mcp.tool()
def list_local_models() -> str:
    """عرض قائمة بجميع النماذج المحلية المتاحة في Ollama مع أحجامها"""
    try:
        resp = requests.get(f"{OLLAMA_API_URL}/tags", timeout=10)
        resp.raise_for_status()
        models = resp.json().get("models", [])
        if not models:
            return "لا توجد نماذج محلية في Ollama حالياً."
        lines = ["**النماذج المتاحة في Ollama:**\n"]
        for m in models:
            size_gb = m.get("size", 0) / (1024 ** 3)
            lines.append(f"- **{m['name']}** ({size_gb:.1f} GB)")
        return "\n".join(lines)
    except Exception as e:
        return f"خطأ في الاتصال بـ Ollama: {str(e)}"


@mcp.tool()
def get_model_info(model_name: str) -> str:
    """الحصول على معلومات تفصيلية حول نموذج معين في Ollama

    Args:
        model_name: اسم النموذج مثل llama3.1 أو qwen2:7b
    """
    try:
        resp = requests.post(
            f"{OLLAMA_API_URL}/show",
            json={"name": model_name},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        family = data.get("details", {}).get("family", "غير محدد")
        params = data.get("details", {}).get("parameter_size", "غير محدد")
        quant = data.get("details", {}).get("quantization_level", "غير محدد")
        return f"**نموذج:** {model_name}\n**العائلة:** {family}\n**الحجم:** {params}\n**الضغط:** {quant}"
    except Exception as e:
        return f"خطأ: {str(e)}"


@mcp.tool()
def pull_model(model_name: str) -> str:
    """تحميل نموذج جديد من Ollama Hub

    Args:
        model_name: اسم النموذج للتحميل مثل mistral أو llama3.2
    """
    try:
        resp = requests.post(
            f"{OLLAMA_API_URL}/pull",
            json={"name": model_name, "stream": False},
            timeout=300,
        )
        resp.raise_for_status()
        return f"تم تحميل نموذج **{model_name}** بنجاح!"
    except Exception as e:
        return f"خطأ في تحميل النموذج: {str(e)}"


if __name__ == "__main__":
    mcp.run()
    mcp.run()
