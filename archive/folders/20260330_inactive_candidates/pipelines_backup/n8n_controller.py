"""
title: n8n Controller
author: Saleh Custom (بناءً على أفضل ممارسات المجتمع)
version: 1.0
description: وكيل يستخدم n8n كأداة طبيعية - يصمم وينفذ workflows تلقائيًا
"""

from typing import Dict, Any
import json
import requests
from pydantic import BaseModel

class Valves(BaseModel):
    n8n_url: str = "http://localhost:5678"
    n8n_api_key: str = ""  # اتركه فاضي لو ما عندكش API key

class Pipeline:
    class Valves(BaseModel):
        n8n_url: str = "http://localhost:5678"
        n8n_api_key: str = ""

    def __init__(self):
        self.type = "filter"
        self.valves = self.Valves()

    async def inlet(self, body: Dict[str, Any], __user__: Dict = None) -> Dict[str, Any]:
        messages = body.get("messages", [])
        if not messages:
            return body

        last_message = messages[-1]
        if last_message.get("role") != "user":
            return body

        content = last_message.get("content", "").strip().lower()

        if any(keyword in content for keyword in ["n8n", "workflow in n8n", "n8n workflow", "n8n agent"]):
            system_prompt = """أنت وكيل متخصص في n8n.
أنت تستخدم n8n كأداة طبيعية.
عندما يطلب منك تصميم workflow:
- صمم الـ workflow
- أعطي الـ JSON كامل وصحيح 100% جاهز للاستيراد
- أعطي curl command جاهز للاستيراد والتشغيل
- حدد أي credentials محتاج تعديلها

كن دقيقًا جدًا ولا تترك أي حقل ناقص."""

            # أضف الـ system prompt
            has_system = any(m["role"] == "system" for m in messages)
            if not has_system:
                messages.insert(0, {"role": "system", "content": system_prompt})
            else:
                for msg in messages:
                    if msg["role"] == "system":
                        msg["content"] = system_prompt + "\n\n" + msg["content"]
                        break

            # تنظيف الكلمة المفتاحية
            last_message["content"] = content.replace("n8n ", "").replace("n8n workflow", "").replace("n8n agent", "").strip()

            body["messages"] = messages

        return body