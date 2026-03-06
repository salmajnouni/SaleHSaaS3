"""
title: SaleHSaaS AI Agent
author: SaleHSaaS
version: 1.0.0
description: الوكيل الذكي الرئيسي لنظام SaleHSaaS — يتصل مباشرة بـ n8n عبر Webhook
"""

from typing import Optional, Callable, Awaitable, Generator, Iterator
from pydantic import BaseModel, Field
import requests
import json
import time


class Pipe:
    class Valves(BaseModel):
        n8n_url: str = Field(
            default="http://n8n:5678/webhook/e5616171-e3b5-4c39-81d4-67409f9fa60a",
            description="Webhook URL للوكيل الذكي الرئيسي في n8n"
        )
        n8n_bearer_token: str = Field(
            default="salehsaas-bridge-key",
            description="Bearer token للمصادقة مع n8n"
        )
        timeout: int = Field(
            default=120,
            description="مهلة الانتظار بالثواني"
        )
        emit_interval: float = Field(
            default=2.0,
            description="فترة إرسال تحديثات الحالة بالثواني"
        )

    def __init__(self):
        self.type = "pipe"
        self.id = "salehsaas_ai_agent"
        self.name = "SaleHSaaS AI Agent"
        self.valves = self.Valves()
        self.last_emit_time = 0

    async def emit_status(
        self,
        __event_emitter__: Callable[[dict], Awaitable[None]],
        level: str,
        message: str,
        done: bool,
    ):
        current_time = time.time()
        if (
            __event_emitter__
            and (current_time - self.last_emit_time >= self.valves.emit_interval or done)
        ):
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "status": "complete" if done else "in_progress",
                        "level": level,
                        "description": message,
                        "done": done,
                    },
                }
            )
            self.last_emit_time = current_time

    def _get_session_id(self, __event_emitter__) -> str:
        """استخراج session ID من event emitter"""
        if not __event_emitter__ or not __event_emitter__.__closure__:
            return f"session_{int(time.time())}"
        for cell in __event_emitter__.__closure__:
            try:
                info = cell.cell_contents
                if isinstance(info, dict):
                    chat_id = info.get("chat_id", "")
                    if chat_id:
                        return chat_id
            except Exception:
                continue
        return f"session_{int(time.time())}"

    async def pipe(
        self,
        body: dict,
        __user__: Optional[dict] = None,
        __event_emitter__: Callable[[dict], Awaitable[None]] = None,
        __event_call__: Callable[[dict], Awaitable[dict]] = None,
    ) -> Optional[str]:

        await self.emit_status(__event_emitter__, "info", "جاري الاتصال بالوكيل الذكي...", False)

        messages = body.get("messages", [])
        if not messages:
            await self.emit_status(__event_emitter__, "error", "لا توجد رسائل", True)
            return "لا توجد رسائل في الطلب."

        # آخر رسالة من المستخدم
        user_message = messages[-1].get("content", "")
        session_id = self._get_session_id(__event_emitter__)

        # بناء السياق من المحادثة السابقة
        history = []
        for msg in messages[:-1]:
            role = msg.get("role", "")
            content = msg.get("content", "")
            if role in ("user", "assistant") and content:
                history.append({"role": role, "content": content})

        payload = {
            "chatInput": user_message,
            "sessionId": session_id,
            "history": history,
            "user": {
                "name": __user__.get("name", "مستخدم") if __user__ else "مستخدم",
                "email": __user__.get("email", "") if __user__ else "",
            }
        }

        headers = {
            "Authorization": f"Bearer {self.valves.n8n_bearer_token}",
            "Content-Type": "application/json",
        }

        try:
            await self.emit_status(__event_emitter__, "info", "يعالج الوكيل طلبك...", False)

            response = requests.post(
                self.valves.n8n_url,
                json=payload,
                headers=headers,
                timeout=self.valves.timeout,
            )

            if response.status_code == 200:
                data = response.json()
                # n8n يُرجع الإجابة في حقل "output" أو "text" أو "response"
                result = (
                    data.get("output")
                    or data.get("text")
                    or data.get("response")
                    or data.get("message")
                    or str(data)
                )
                await self.emit_status(__event_emitter__, "info", "اكتمل", True)
                return result
            else:
                error_msg = f"خطأ من n8n: {response.status_code} — {response.text[:200]}"
                await self.emit_status(__event_emitter__, "error", error_msg, True)
                return error_msg

        except requests.exceptions.Timeout:
            msg = f"انتهت مهلة الانتظار ({self.valves.timeout}s). تأكد من تفعيل الـ workflow في n8n."
            await self.emit_status(__event_emitter__, "error", msg, True)
            return msg
        except Exception as e:
            msg = f"خطأ في الاتصال: {str(e)}"
            await self.emit_status(__event_emitter__, "error", msg, True)
            return msg
