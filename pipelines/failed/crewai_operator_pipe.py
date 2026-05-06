"""
title: مشغّل CrewAI
description: وكيل يتصل بـ crewai_server على ويندوز هوست ويدعم استرجاع المعرفة من ChromaDB. يكتشف الوضع تلقائياً (عام / مراجعة كود / بناء تطبيق). أضف /web في بداية رسالتك لتفعيل البحث على الإنترنت.
author: Saleh Almajnouni
version: 1.0
"""

import sys
import requests
import logging
from typing import Optional, Callable, Awaitable, Any, Dict, Union, Generator, Iterator, List
from pydantic import BaseModel, Field


class Pipe:
    class Valves(BaseModel):
        crewai_url: str = Field(
            default="http://host.docker.internal:8099",
            description="عنوان crewai_server على ويندوز هوست",
        )
        chromadb_url: str = Field(
            default="http://host.docker.internal:8010",
            description="عنوان ChromaDB (لاسترجاع معرفة CrewAI)",
        )
        ollama_url: str = Field(
            default="http://host.docker.internal:11434",
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
        top_k: int = Field(
            default=5,
            description="عدد نتائج ChromaDB",
        )
        min_score: float = Field(
            default=0.40,
            description="أدنى درجة تشابه لقبول النتيجة",
        )
        timeout: int = Field(
            default=1800,
            description="مهلة الطلب بالثواني (CrewAI قد يأخذ وقتاً)",
        )

    def __init__(self):
        self.valves = self.Valves()
        self.log = logging.getLogger("crewai_operator_pipe")

    def pipes(self) -> List[Dict[str, str]]:
        return [
            {"id": "crewai_operator", "name": "🤖 مشغّل CrewAI"},
        ]

    # ------------------------------------------------------------------ #
    #  ChromaDB helpers                                                     #
    # ------------------------------------------------------------------ #

    def _get_embedding(self, text: str) -> Optional[List[float]]:
        try:
            resp = requests.post(
                f"{self.valves.ollama_url}/api/embeddings",
                json={"model": self.valves.embedding_model, "prompt": text},
                timeout=30,
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
                timeout=10,
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
                timeout=15,
            )
            if resp.status_code == 200:
                data = resp.json()
                results = []
                docs = data.get("documents", [[]])[0]
                metas = data.get("metadatas", [[]])[0]
                distances = data.get("distances", [[]])[0]
                for doc, meta, dist in zip(docs, metas, distances):
                    similarity = 1 - dist
                    if similarity >= self.valves.min_score:
                        results.append(
                            {
                                "text": doc,
                                "source": meta.get(
                                    "doc_name",
                                    meta.get("source", "وثيقة"),
                                ),
                                "similarity": round(similarity, 3),
                            }
                        )
                return results
        except Exception as e:
            self.log.warning(f"ChromaDB search error: {e}")
        return []

    def _build_rag_prefix(self, results: List[Dict]) -> str:
        if not results:
            return ""
        lines = ["[معلومات من قاعدة المعرفة]"]
        for i, r in enumerate(results, 1):
            lines.append(
                f"\n--- مرجع {i} (تشابه: {r['similarity']}) من: {r['source']} ---\n{r['text']}"
            )
        lines.append("\n[نهاية المعلومات]\n")
        return "\n".join(lines)

    # ------------------------------------------------------------------ #
    #  Main pipe                                                            #
    # ------------------------------------------------------------------ #

    async def pipe(
        self,
        body: dict,
        __user__: Optional[dict] = None,
        __event_emitter__: Optional[Callable[[dict], Awaitable[None]]] = None,
        __event_call__: Optional[Callable[[dict], Awaitable[dict]]] = None,
        __metadata__: Optional[dict] = None,
    ) -> Union[str, Generator, Iterator]:

        async def emit(level: str, message: str, done: bool):
            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": message,
                            "done": done,
                            "level": level,
                        },
                    }
                )

        # ── استخراج الرسالة ──────────────────────────────────────────── #
        messages = body.get("messages", [])
        if not messages:
            return "❌ لم أستلم رسالة."

        user_message = messages[-1].get("content", "").strip()
        if not user_message:
            return "❌ الرسالة فارغة."

        # ── فحص /web ──────────────────────────────────────────────────── #
        force_web = False
        if user_message.lower().startswith("/web"):
            force_web = True
            user_message = user_message[4:].strip()
            if not user_message:
                return "❌ أضف سؤالك بعد /web"

        # ── فحص حالة crewai_server ────────────────────────────────────── #
        await emit("in_progress", "⏳ فحص اتصال crewai_server...", False)
        try:
            health = requests.get(
                f"{self.valves.crewai_url}/health", timeout=5
            )
            if health.status_code != 200:
                await emit("error", "❌ crewai_server لا يستجيب", True)
                return (
                    "## ❌ crewai_server غير متاح\n\n"
                    f"الخادم على `{self.valves.crewai_url}` أعاد: HTTP {health.status_code}\n\n"
                    "**لتشغيله:**\n"
                    "```\n"
                    "cd c:\\saleh26\\p26\\bigagents\n"
                    ".venv\\Scripts\\python.exe crewai_server.py\n"
                    "```"
                )
        except Exception as e:
            await emit("error", "❌ تعذر الاتصال بـ crewai_server", True)
            return (
                "## ❌ crewai_server غير متاح\n\n"
                f"تعذر الوصول إلى `{self.valves.crewai_url}`\n"
                f"الخطأ: `{e}`\n\n"
                "**لتشغيله على ويندوز:**\n"
                "```\n"
                "cd c:\\saleh26\\p26\\bigagents\n"
                ".venv\\Scripts\\python.exe crewai_server.py\n"
                "```"
            )

        # ── استرجاع المعرفة من ChromaDB ──────────────────────────────── #
        await emit("in_progress", "🔍 البحث في قاعدة المعرفة...", False)
        rag_results = self._search_chromadb(user_message)
        rag_prefix = self._build_rag_prefix(rag_results)

        if rag_results:
            await emit(
                "in_progress",
                f"📚 وجدت {len(rag_results)} نتيجة في قاعدة المعرفة",
                False,
            )

        # ── تجميع الرسالة النهائية ───────────────────────────────────── #
        final_message = (rag_prefix + user_message) if rag_prefix else user_message

        # ── تحديد الوضع المتوقع ──────────────────────────────────────── #
        if force_web:
            mode_hint = "🌐 بحث على الإنترنت"
        elif "```" in user_message or any(
            kw in user_message.lower()
            for kw in ["code review", "راجع الكود", "فحص الكود", "مراجعة الكود"]
        ):
            mode_hint = "🔍 مراجعة الكود"
        elif any(
            kw in user_message.lower()
            for kw in ["بناء تطبيق", "build app", "انشاء تطبيق", "mvp", "تطبيق"]
        ):
            mode_hint = "🏗️ بناء تطبيق"
        else:
            mode_hint = "🤖 وضع عام"

        await emit("in_progress", f"⚙️ {mode_hint} — جارٍ التشغيل (قد يأخذ دقائق)...", False)

        # ── استدعاء crewai_server ────────────────────────────────────── #
        try:
            resp = requests.post(
                f"{self.valves.crewai_url}/chat",
                json={"message": final_message, "force_web": force_web},
                timeout=self.valves.timeout,
            )

            if resp.status_code != 200:
                await emit("error", f"❌ خطأ {resp.status_code}", True)
                return f"❌ خطأ من crewai_server: HTTP {resp.status_code}\n{resp.text[:500]}"

            data = resp.json()
            answer = data.get("answer", "").strip()
            used_web = data.get("used_web_search", False)
            debug = data.get("debug", {})
            current_mode = debug.get("mode", "")

        except requests.exceptions.Timeout:
            await emit("error", "❌ انتهى الوقت المحدد", True)
            return (
                "## ❌ انتهى الوقت\n\n"
                f"لم يرد crewai_server خلال {self.valves.timeout // 60} دقيقة.\n"
                "جرب مهمة أبسط أو تحقق من Ollama."
            )
        except Exception as e:
            await emit("error", f"❌ {e}", True)
            return f"❌ خطأ في الاتصال: {e}"

        if not answer:
            await emit("warning", "⚠️ الخادم لم يُرجع إجابة", True)
            return "⚠️ لم يتم توليد إجابة."

        # ── بناء الرد النهائي ────────────────────────────────────────── #
        footer_parts = []
        if current_mode:
            mode_labels = {
                "general": "عام",
                "code_review": "مراجعة كود",
                "app_build": "بناء تطبيق",
                "local_fs": "نظام الملفات",
            }
            footer_parts.append(f"⚙️ الوضع: {mode_labels.get(current_mode, current_mode)}")
        if used_web:
            footer_parts.append("🌐 استُخدم البحث على الإنترنت")
        if rag_results:
            footer_parts.append(f"📚 مراجع ChromaDB: {len(rag_results)}")

        await emit("complete", "✅ اكتمل", True)

        if footer_parts:
            return f"{answer}\n\n---\n{' | '.join(footer_parts)}"
        return answer
