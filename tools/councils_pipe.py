"""
title: وكلاء n8n
description: استشارة المجالس والوكلاء عبر n8n webhooks (ابتكار، حوكمة تقنية، مراجعة قانونية، مساعد القوانين، صائد الأخطاء).
author: Saleh Almajnouni
version: 2.0
"""

import json
import aiohttp
import logging
from typing import Optional, Callable, Awaitable, Any, Dict, Union, Generator, Iterator, List
from pydantic import BaseModel, Field


class Pipe:
    class Valves(BaseModel):
        n8n_url: str = Field(
            default="http://n8n:5678",
            description="n8n base URL (Docker internal)",
        )
        timeout: int = Field(
            default=1500,
            description="Webhook timeout in seconds (councils take 15-20 min)",
        )

    def __init__(self):
        self.name = ""
        self.valves = self.Valves()
        self.log = logging.getLogger("councils_pipe")

    def pipes(self) -> List[Dict[str, str]]:
        return [
            {"id": "innovation", "name": "مجلس الابتكار"},
            {"id": "tech_governance", "name": "مجلس الحوكمة التقنية"},
            {"id": "legal_review", "name": "مجلس المراجعة القانونية"},
            {"id": "legal_chat", "name": "مساعد القوانين السعودية"},
            {"id": "error_hunter", "name": "صائد الأخطاء"},
        ]

    async def emit_status(self, emitter, level, message, done):
        if emitter:
            await emitter(
                {
                    "type": "status",
                    "data": {"description": message, "done": done, "level": level},
                }
            )

    async def pipe(
        self,
        body: dict,
        __user__: Optional[dict] = None,
        __event_emitter__: Optional[Callable[[dict], Awaitable[None]]] = None,
        __event_call__: Optional[Callable[[dict], Awaitable[dict]]] = None,
        __metadata__: Optional[dict] = None,
    ) -> Union[str, Generator, Iterator, Dict[str, Any]]:

        WEBHOOKS = {
            "innovation": "/webhook/council-innovation",
            "tech_governance": "/webhook/council-tech-governance",
            "legal_review": "/webhook/council-legal-review",
            "legal_chat": "/webhook/saleh-legal-chat-001",
            "error_hunter": "/webhook/error-hunt-v2",
        }
        NAMES = {
            "innovation": "مجلس الابتكار",
            "tech_governance": "مجلس الحوكمة التقنية",
            "legal_review": "مجلس المراجعة القانونية",
            "legal_chat": "مساعد القوانين السعودية",
            "error_hunter": "صائد الأخطاء",
        }

        # Extract council ID from model
        model_id = body.get("model", "")
        council_id = model_id.split(".")[-1] if "." in model_id else model_id

        if council_id not in WEBHOOKS:
            return f"مجلس غير معروف: {council_id}"

        council_name = NAMES[council_id]
        webhook_path = WEBHOOKS[council_id]
        url = f"{self.valves.n8n_url}{webhook_path}"

        # Extract question
        messages = body.get("messages", [])
        if not messages:
            return "لم أستلم سؤالاً."

        question = messages[-1].get("content", "")
        if not question:
            return "السؤال فارغ."

        # Estimated time varies by workflow type
        if council_id in ("innovation", "tech_governance", "legal_review"):
            time_hint = "~15-20 دقيقة"
        elif council_id == "legal_chat":
            time_hint = "~1-2 دقيقة"
        else:
            time_hint = "~30 ثانية"

        await self.emit_status(
            __event_emitter__,
            "in_progress",
            f"⏳ جارٍ استشارة {council_name}... يستغرق {time_hint}",
            False,
        )

        payload = {"question": question}

        # Error hunter expects 'error' field, not 'question'
        if council_id == "error_hunter":
            payload = {"error": question}

        try:
            timeout = aiohttp.ClientTimeout(total=self.valves.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    url,
                    json=payload,
                    headers={"Content-Type": "application/json; charset=utf-8"},
                ) as resp:
                    if resp.status != 200:
                        err = await resp.text()
                        await self.emit_status(
                            __event_emitter__, "error", f"خطأ {resp.status}", True
                        )
                        return f"❌ فشل الاستدعاء: HTTP {resp.status}\n{err[:300]}"

                    result = await resp.json()

        except TimeoutError:
            await self.emit_status(__event_emitter__, "error", "انتهى الوقت", True)
            return "❌ انتهى الوقت المحدد. يمكن Ollama متوقف أو مشغول."
        except Exception as e:
            await self.emit_status(__event_emitter__, "error", str(e), True)
            return f"❌ خطأ: {e}"

        # Format response based on workflow type
        # Councils: {decision, sessionId, sources, status}
        # Legal chat: {output}
        # Error hunter: {status, message, report, runId, refs}

        if council_id in ("innovation", "tech_governance", "legal_review"):
            decision = result.get("decision", "")
            session_id = result.get("sessionId", "")
            sources = result.get("sources", {})
            web = sources.get("web", 0)
            rag = sources.get("rag", 0)
            status = result.get("status", "")

            if not decision:
                await self.emit_status(
                    __event_emitter__, "warning", "لم يصدر قرار", True
                )
                return f"⚠️ {council_name} لم يصدر قراراً. الحالة: {status}"

            await self.emit_status(
                __event_emitter__, "complete", f"✅ {council_name} أصدر قراره", True
            )
            return (
                f"## قرار {council_name}\n\n"
                f"{decision}\n\n"
                f"---\n"
                f"📋 جلسة: `{session_id}`\n"
                f"🌐 مصادر ويب: {web} | 📚 مصادر RAG: {rag}"
            )

        elif council_id == "legal_chat":
            output = result.get("output", "")
            if not output:
                await self.emit_status(
                    __event_emitter__, "warning", "لا توجد إجابة", True
                )
                return "⚠️ لم يتم توليد إجابة قانونية."

            await self.emit_status(
                __event_emitter__, "complete", "✅ تم الرد", True
            )
            return f"## مساعد القوانين السعودية\n\n{output}"

        elif council_id == "error_hunter":
            report = result.get("report", "")
            status = result.get("status", "")
            refs = result.get("refs", 0)
            run_id = result.get("runId", "")

            if not report:
                await self.emit_status(
                    __event_emitter__, "warning", "لا يوجد تقرير", True
                )
                return f"⚠️ لم يتم إنشاء تقرير. الحالة: {status}"

            await self.emit_status(
                __event_emitter__, "complete", f"✅ تقرير جاهز ({refs} مراجع)", True
            )
            return (
                f"{report}\n\n"
                f"---\n"
                f"🔧 Run: `{run_id}` | 📎 مراجع: {refs}"
            )

        else:
            # Generic fallback
            await self.emit_status(
                __event_emitter__, "complete", "✅ تم", True
            )
            import json as _json
            return f"```json\n{_json.dumps(result, indent=2, ensure_ascii=False)}\n```"
