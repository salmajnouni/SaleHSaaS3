"""
title: صائد الأخطاء V3
description: نظام تشخيص شامل - يفحص صحة جميع الخدمات، يراقب n8n، يحلل Ollama، يبحث عن حلول الأخطاء. يعمل من Open WebUI و Cline.
author: Saleh Almajnouni
version: 3.0
"""

import json
import asyncio
import logging
import time
from typing import Optional, Callable, Awaitable, Any, Dict, Union, Generator, Iterator, List
from pydantic import BaseModel, Field

try:
    import aiohttp
except ImportError:
    aiohttp = None


class Pipe:
    class Valves(BaseModel):
        n8n_url: str = Field(
            default="http://n8n:5678",
            description="n8n base URL (Docker internal)",
        )
        n8n_api_key: str = Field(
            default="",
            description="n8n API key (JWT) for workflow/execution monitoring",
        )
        ollama_url: str = Field(
            default="http://host.docker.internal:11434",
            description="Ollama API URL",
        )
        chromadb_url: str = Field(
            default="http://chromadb:8000",
            description="ChromaDB URL",
        )
        searxng_url: str = Field(
            default="http://searxng:8080",
            description="SearXNG search URL",
        )
        tika_url: str = Field(
            default="http://tika:9998",
            description="Apache Tika URL",
        )
        data_pipeline_url: str = Field(
            default="http://data_pipeline:8001",
            description="Data Pipeline URL",
        )
        pipelines_url: str = Field(
            default="http://pipelines:9099",
            description="Pipelines URL",
        )
        postgres_host: str = Field(
            default="postgres",
            description="PostgreSQL host",
        )
        timeout: int = Field(
            default=15,
            description="HTTP timeout per service check (seconds)",
        )

    def __init__(self):
        self.name = "صائد الأخطاء"
        self.valves = self.Valves()
        self.log = logging.getLogger("error_hunter_pipe")

    def pipes(self) -> List[Dict[str, str]]:
        return [
            {"id": "scan", "name": "صائد الأخطاء - فحص شامل"},
        ]

    # ─── Helpers ──────────────────────────────────────────────

    @staticmethod
    def _wrap_cline(text: str) -> str:
        """Wrap response in Cline's attempt_completion format so it stops retrying."""
        return f"<attempt_completion>\n<result>\n{text}\n</result>\n</attempt_completion>"

    async def _emit(self, emitter, level, message, done):
        if emitter:
            await emitter(
                {"type": "status", "data": {"description": message, "done": done, "level": level}}
            )

    async def _get(self, session, url, headers=None, timeout=None):
        t = timeout or self.valves.timeout
        try:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=t)) as r:
                body = await r.text()
                return r.status, body
        except Exception as e:
            return 0, str(e)

    async def _post(self, session, url, data=None, headers=None, timeout=None):
        t = timeout or self.valves.timeout
        try:
            async with session.post(url, json=data, headers=headers, timeout=aiohttp.ClientTimeout(total=t)) as r:
                body = await r.text()
                return r.status, body
        except Exception as e:
            return 0, str(e)

    # ─── Service Checks ──────────────────────────────────────

    async def _check_ollama(self, session):
        result = {"service": "Ollama", "status": "❌ غير متاح", "details": {}}
        # Health
        code, body = await self._get(session, f"{self.valves.ollama_url}/api/tags")
        if code == 200:
            try:
                data = json.loads(body)
                models = [m["name"] for m in data.get("models", [])]
                result["status"] = "✅ يعمل"
                result["details"]["models"] = models
                result["details"]["model_count"] = len(models)
            except:
                result["status"] = "⚠️ رد غير متوقع"
        else:
            result["details"]["error"] = body[:200]
            return result

        # Running models
        code2, body2 = await self._get(session, f"{self.valves.ollama_url}/api/ps")
        if code2 == 200:
            try:
                data2 = json.loads(body2)
                running = []
                for m in data2.get("models", []):
                    name = m.get("name", "?")
                    size_gb = round(m.get("size", 0) / (1024**3), 1)
                    vram_gb = round(m.get("size_vram", 0) / (1024**3), 1)
                    running.append(f"{name} ({size_gb}GB, VRAM: {vram_gb}GB)")
                result["details"]["running"] = running if running else ["لا يوجد نموذج محمّل"]
            except:
                pass
        return result

    async def _check_n8n(self, session):
        result = {"service": "n8n", "status": "❌ غير متاح", "details": {}}
        code, body = await self._get(session, f"{self.valves.n8n_url}/healthz")
        if code == 200:
            result["status"] = "✅ يعمل"
        else:
            result["details"]["error"] = body[:200]
            return result

        if not self.valves.n8n_api_key:
            result["details"]["warning"] = "مفتاح API غير مُعرّف - لا يمكن فحص سير العمل"
            return result

        headers = {"X-N8N-API-KEY": self.valves.n8n_api_key}

        # Workflows
        code, body = await self._get(session, f"{self.valves.n8n_url}/api/v1/workflows?limit=50", headers=headers)
        if code == 200:
            try:
                data = json.loads(body)
                workflows = data.get("data", [])
                active = [w for w in workflows if w.get("active")]
                inactive = [w for w in workflows if not w.get("active")]
                result["details"]["workflows_total"] = len(workflows)
                result["details"]["workflows_active"] = len(active)
                result["details"]["workflows_inactive"] = len(inactive)
                result["details"]["active_list"] = [f"{w.get('name','')} ({w.get('id','')})" for w in active]
            except:
                pass

        # Recent executions (last 20 to catch more failures)
        code, body = await self._get(session, f"{self.valves.n8n_url}/api/v1/executions?limit=20", headers=headers)
        if code == 200:
            try:
                data = json.loads(body)
                execs = data.get("data", [])
                failed = [e for e in execs if e.get("status") == "error"]
                result["details"]["recent_executions"] = len(execs)
                result["details"]["recent_failed"] = len(failed)
                if failed:
                    result["details"]["failed_errors"] = []
                    for e in failed[:5]:
                        entry = {
                            "id": e.get("id"),
                            "workflow": e.get("workflowData", {}).get("name", "?"),
                            "finished": e.get("stoppedAt", "?"),
                        }
                        # Fetch detailed error from execution data
                        eid = e.get("id")
                        if eid:
                            ec, eb = await self._get(session, f"{self.valves.n8n_url}/api/v1/executions/{eid}?includeData=true", headers=headers)
                            if ec == 200:
                                try:
                                    edata = json.loads(eb)
                                    rd = edata.get("data", {}).get("resultData", {}).get("runData", {})
                                    for node_name, runs in rd.items():
                                        for run in runs:
                                            if run.get("error"):
                                                err_msg = run["error"].get("message", "")[:200]
                                                entry["error_node"] = node_name
                                                entry["error_msg"] = err_msg
                                                break
                                        if "error_msg" in entry:
                                            break
                                except:
                                    pass
                        result["details"]["failed_errors"].append(entry)
            except:
                pass
        return result

    async def _check_chromadb(self, session):
        result = {"service": "ChromaDB", "status": "❌ غير متاح", "details": {}}
        code, body = await self._get(session, f"{self.valves.chromadb_url}/api/v1/heartbeat")
        if code == 200:
            result["status"] = "✅ يعمل"
        else:
            result["details"]["error"] = body[:200]
            return result

        code, body = await self._get(session, f"{self.valves.chromadb_url}/api/v1/collections")
        if code == 200:
            try:
                collections = json.loads(body)
                result["details"]["collections"] = []
                for c in collections:
                    name = c.get("name", "?")
                    cid = c.get("id", "?")
                    result["details"]["collections"].append(f"{name} ({cid})")
                result["details"]["collection_count"] = len(collections)
            except:
                pass

        # Get count for main collection
        code, body = await self._get(session, f"{self.valves.chromadb_url}/api/v1/collections")
        if code == 200:
            try:
                collections = json.loads(body)
                for c in collections:
                    cid = c.get("id")
                    if cid:
                        code3, body3 = await self._get(session, f"{self.valves.chromadb_url}/api/v1/collections/{cid}/count")
                        if code3 == 200:
                            try:
                                count = json.loads(body3)
                                result["details"][f"docs_{c.get('name',cid)}"] = count
                            except:
                                pass
            except:
                pass

        return result

    async def _check_searxng(self, session):
        result = {"service": "SearXNG", "status": "❌ غير متاح", "details": {}}
        code, body = await self._get(session, f"{self.valves.searxng_url}/search?q=test&format=json&engines=bing&language=en", timeout=10)
        if code == 200:
            try:
                data = json.loads(body)
                n_results = len(data.get("results", []))
                result["status"] = "✅ يعمل" if n_results > 0 else "⚠️ يعمل لكن 0 نتائج"
                result["details"]["test_results"] = n_results
                unresponsive = data.get("unresponsive_engines", [])
                if unresponsive:
                    result["details"]["unresponsive_engines"] = [e[0] if isinstance(e, list) else str(e) for e in unresponsive]
            except:
                result["status"] = "⚠️ رد غير متوقع"
        else:
            result["details"]["error"] = body[:200]
        return result

    async def _check_tika(self, session):
        result = {"service": "Tika", "status": "❌ غير متاح", "details": {}}
        code, body = await self._get(session, f"{self.valves.tika_url}/tika")
        if code == 200:
            result["status"] = "✅ يعمل"
            result["details"]["message"] = body[:100].strip()
        else:
            result["details"]["error"] = body[:200]
        return result

    async def _check_data_pipeline(self, session):
        result = {"service": "Data Pipeline", "status": "❌ غير متاح", "details": {}}
        code, body = await self._get(session, f"{self.valves.data_pipeline_url}/")
        if code == 200:
            result["status"] = "✅ يعمل"
            try:
                result["details"] = json.loads(body)
            except:
                result["details"]["response"] = body[:200]
        else:
            result["details"]["error"] = body[:200]
        return result

    async def _check_pipelines(self, session):
        result = {"service": "Pipelines", "status": "❌ غير متاح", "details": {}}
        code, body = await self._get(session, f"{self.valves.pipelines_url}/")
        if code == 200:
            result["status"] = "✅ يعمل"
        else:
            result["details"]["error"] = body[:200]
        return result

    async def _check_docker_logs(self, session):
        """Query recent errors/warnings from service_logs via data_pipeline API."""
        result = {"service": "Docker Logs", "status": "💤 لا بيانات", "details": {}}
        code, body = await self._get(
            session,
            f"{self.valves.data_pipeline_url}/logs/stats",
            timeout=10,
        )
        if code != 200:
            result["details"]["note"] = "جامع اللوقات غير متصل أو لم يبدأ بعد"
            return result

        try:
            data = json.loads(body)
            stats = data.get("stats", [])
            total = data.get("total_logs_in_db", 0)

            if not stats:
                result["status"] = "✅ لا أخطاء"
                result["details"]["total_in_db"] = total
                return result

            total_errors = sum(s.get("errors_1h", 0) for s in stats)
            total_warnings = sum(s.get("warnings_1h", 0) for s in stats)

            if total_errors > 0:
                result["status"] = f"🔴 {total_errors} أخطاء في آخر ساعة"
            elif total_warnings > 0:
                result["status"] = f"🟡 {total_warnings} تحذيرات في آخر ساعة"
            else:
                result["status"] = "✅ لا أخطاء"

            result["details"]["errors_1h"] = total_errors
            result["details"]["warnings_1h"] = total_warnings
            result["details"]["total_in_db"] = total

            # Fetch actual error messages for the report
            if total_errors > 0 or total_warnings > 0:
                ec, eb = await self._get(
                    session,
                    f"{self.valves.data_pipeline_url}/logs/recent?minutes=60&level=WARNING&limit=15",
                    timeout=10,
                )
                if ec == 200:
                    try:
                        log_data = json.loads(eb)
                        recent_logs = log_data.get("logs", [])
                        if recent_logs:
                            result["details"]["recent_issues"] = []
                            for lg in recent_logs[:10]:
                                result["details"]["recent_issues"].append({
                                    "container": lg.get("container", "?"),
                                    "level": lg.get("level", "?"),
                                    "message": lg.get("message", "")[:300],
                                    "time": lg.get("collected_at", "?"),
                                })
                    except Exception:
                        pass

        except Exception:
            result["details"]["error"] = "خطأ في تحليل بيانات اللوقات"

        return result

    # ─── Full Scan ────────────────────────────────────────────

    async def _full_scan(self, session, emitter):
        await self._emit(emitter, "in_progress", "🔍 جارٍ فحص جميع الخدمات...", False)

        checks = await asyncio.gather(
            self._check_ollama(session),
            self._check_n8n(session),
            self._check_chromadb(session),
            self._check_searxng(session),
            self._check_tika(session),
            self._check_data_pipeline(session),
            self._check_pipelines(session),
            self._check_docker_logs(session),
        )

        healthy = sum(1 for c in checks if "✅" in c["status"])
        warning = sum(1 for c in checks if "⚠️" in c["status"])
        down = sum(1 for c in checks if "❌" in c["status"])
        total = len(checks)

        # Check for n8n failures even if service is "up"
        n8n_failures = 0
        for c in checks:
            if c["service"] == "n8n":
                n8n_failures = c["details"].get("recent_failed", 0)

        # Build report
        lines = []
        lines.append("# 🏥 تقرير صحة النظام - SaleHSaaS")
        lines.append("")

        if down == 0 and warning == 0 and n8n_failures == 0:
            lines.append(f"## ✅ جميع الخدمات تعمل ({healthy}/{total})")
        elif down == 0 and n8n_failures > 0:
            lines.append(f"## ⚠️ الخدمات تعمل ({healthy}/{total}) لكن يوجد {n8n_failures} تنفيذات فاشلة في n8n")
        elif down == 0:
            lines.append(f"## ⚠️ {healthy} تعمل، {warning} تحذيرات من {total}")
        else:
            lines.append(f"## 🚨 {down} خدمات متوقفة، {warning} تحذيرات، {healthy} تعمل من {total}")

        lines.append("")
        lines.append("| الخدمة | الحالة |")
        lines.append("|--------|--------|")
        for c in checks:
            lines.append(f"| {c['service']} | {c['status']} |")

        lines.append("")

        # Detailed sections
        for c in checks:
            if c["details"]:
                lines.append(f"### {c['service']}")
                lines.append("")
                for key, val in c["details"].items():
                    if isinstance(val, list):
                        lines.append(f"**{key}:**")
                        for item in val:
                            lines.append(f"- {item}")
                    elif isinstance(val, dict):
                        lines.append(f"**{key}:** `{json.dumps(val, ensure_ascii=False)}`")
                    else:
                        lines.append(f"**{key}:** {val}")
                lines.append("")

        # Collect warnings from all checks
        warnings = []

        # n8n failed executions
        for c in checks:
            if c["service"] == "n8n" and c["details"].get("recent_failed", 0) > 0:
                n_failed = c["details"]["recent_failed"]
                warnings.append(f"🔴 **n8n**: {n_failed} تنفيذات فاشلة من آخر {c['details'].get('recent_executions', '?')}")
                for fe in c["details"].get("failed_errors", []):
                    wf = fe.get('workflow', '?')
                    err_node = fe.get('error_node', '')
                    err_msg = fe.get('error_msg', 'خطأ غير معروف')
                    eid = fe.get('id', '?')
                    if err_node:
                        warnings.append(f"  - `{wf}` (#{eid}): نود **{err_node}** → `{err_msg}`")
                    else:
                        warnings.append(f"  - `{wf}` (#{eid}): {err_msg}")

            # SearXNG unresponsive engines
            if c["service"] == "SearXNG" and c["details"].get("unresponsive_engines"):
                engines = ", ".join(c["details"]["unresponsive_engines"])
                warnings.append(f"⚠️ **SearXNG**: محركات لا تستجيب: {engines}")

            # Ollama no models loaded
            if c["service"] == "Ollama" and c["details"].get("running_models") == 0:
                warnings.append("💤 **Ollama**: لا يوجد نموذج محمّل في الذاكرة (طبيعي إذا ما في طلبات)")

            # Docker Logs errors from database
            if c["service"] == "Docker Logs" and c["details"].get("errors_1h", 0) > 0:
                warnings.append(f"🔴 **لوقات Docker**: {c['details']['errors_1h']} أخطاء في آخر ساعة")
                for issue in c["details"].get("recent_issues", [])[:5]:
                    container = issue.get("container", "?")
                    msg = issue.get("message", "")[:150]
                    warnings.append(f"  - **{container}**: `{msg}`")
            elif c["service"] == "Docker Logs" and c["details"].get("warnings_1h", 0) > 0:
                warnings.append(f"🟡 **لوقات Docker**: {c['details']['warnings_1h']} تحذيرات في آخر ساعة")

        # Services down or with warnings
        problems = [c for c in checks if "❌" in c["status"] or "⚠️" in c["status"]]
        if problems:
            for p in problems:
                svc = p["service"]
                if "❌" in p["status"]:
                    warnings.append(f"🚨 **{svc}**: الخدمة متوقفة! تحقق من `docker ps` و `docker logs salehsaas_{svc.lower()}`")
                elif "⚠️" in p["status"]:
                    warnings.append(f"⚠️ **{svc}**: تحتاج مراجعة")

        if warnings:
            lines.append("---")
            lines.append("## ⚠️ تنبيهات ومشاكل")
            lines.append("")
            for w in warnings:
                lines.append(w)
            lines.append("")
            lines.append("---")
            lines.append("## 🔧 توصيات")
            lines.append("")
            if any("فاشلة" in w for w in warnings):
                lines.append("- أرسل `n8n` لفحص تفصيلي للتنفيذات الفاشلة")
            if any("لوقات Docker" in w for w in warnings):
                lines.append("- راجع الأخطاء أعلاه — قد تحتاج إعادة تشغيل الخدمة المتأثرة")
            for p in problems:
                svc = p["service"]
                if "❌" in p["status"]:
                    lines.append(f"- افحص `docker logs salehsaas_{svc.lower()}` للتفاصيل")

        return "\n".join(lines)

    # ─── Error Search ─────────────────────────────────────────

    async def _search_error(self, session, error_text, emitter):
        await self._emit(emitter, "in_progress", "🔍 جارٍ البحث عن حلول...", False)

        # Search SearXNG with multiple engine sets for reliability
        import urllib.parse

        # Clean query: first meaningful line, max 150 chars
        clean_q = error_text.split("\n")[0].strip()[:150]
        query = urllib.parse.quote(clean_q)

        # Try primary engines first (stackoverflow + startpage + bing)
        engine_sets = [
            "stackoverflow,startpage,bing",
            "presearch,yandex,ask",
        ]

        results = []
        for engines in engine_sets:
            url = f"{self.valves.searxng_url}/search?q={query}&format=json&language=en&engines={engines}"
            code, body = await self._get(session, url, timeout=20)
            if code == 200:
                try:
                    data = json.loads(body)
                    new_results = data.get("results", [])
                    # Filter out obviously irrelevant results
                    for r in new_results:
                        title_lower = (r.get("title", "") + " " + r.get("content", "")).lower()
                        # Skip if it's clearly unrelated (translation, video editor, etc.)
                        junk_keywords = ["ترجم", "capcut", "translator", "translate.com", "video editor"]
                        if not any(jk in title_lower for jk in junk_keywords):
                            results.append(r)
                except:
                    pass
            if len(results) >= 5:
                break

        # Deduplicate by URL
        seen_urls = set()
        unique_results = []
        for r in results:
            u = r.get("url", "")
            if u not in seen_urls:
                seen_urls.add(u)
                unique_results.append(r)
        results = unique_results

        # Build report
        lines = []
        lines.append("# 🔍 نتائج البحث عن الخطأ")
        lines.append("")
        lines.append(f"**الخطأ:** `{error_text[:200]}`")
        lines.append("")

        if results:
            lines.append(f"**عدد النتائج:** {len(results)}")
            lines.append("")
            for i, r in enumerate(results[:8], 1):
                title = r.get("title", "بدون عنوان")
                url = r.get("url", "")
                content = r.get("content", "")[:200]
                lines.append(f"### {i}. {title}")
                lines.append(f"🔗 {url}")
                lines.append(f"> {content}")
                lines.append("")
        else:
            lines.append("⚠️ لم يتم العثور على نتائج.")
            lines.append("")
            lines.append("**اقتراحات:**")
            lines.append("- حاول نسخ رسالة الخطأ الأصلية بالإنجليزية")
            lines.append("- أزل المسارات والقيم الخاصة بمشروعك")
            lines.append("- استخدم الجزء الأهم من رسالة الخطأ فقط")

        return "\n".join(lines)

    # ─── N8N Execution Inspector ──────────────────────────────

    async def _inspect_n8n_failures(self, session, emitter):
        await self._emit(emitter, "in_progress", "🔍 جارٍ فحص تنفيذات n8n الفاشلة...", False)

        if not self.valves.n8n_api_key:
            return "⚠️ مفتاح n8n API غير مُعرّف في الإعدادات (Valves). لا يمكن فحص التنفيذات."

        headers = {"X-N8N-API-KEY": self.valves.n8n_api_key}
        code, body = await self._get(session, f"{self.valves.n8n_url}/api/v1/executions?limit=20&status=error", headers=headers)

        if code != 200:
            return f"❌ فشل الاتصال بـ n8n API: {code} - {body[:200]}"

        try:
            data = json.loads(body)
        except:
            return "❌ رد غير متوقع من n8n"

        execs = data.get("data", [])
        if not execs:
            return "## ✅ n8n التنفيذات\n\nلا توجد تنفيذات فاشلة في آخر 20 تنفيذ. النظام سليم!"

        lines = []
        lines.append(f"# 🚨 تنفيذات n8n الفاشلة ({len(execs)})")
        lines.append("")

        for e in execs[:5]:
            eid = e.get("id", "?")
            wf_name = e.get("workflowData", {}).get("name", "?")
            finished = e.get("stoppedAt", "?")
            lines.append(f"### Execution #{eid} - {wf_name}")
            lines.append(f"- **انتهى:** {finished}")

            # Try to get detailed error
            code2, body2 = await self._get(
                session,
                f"{self.valves.n8n_url}/api/v1/executions/{eid}?includeData=true",
                headers=headers,
                timeout=10,
            )
            if code2 == 200:
                try:
                    detail = json.loads(body2)
                    run_data = detail.get("data", {}).get("resultData", {}).get("runData", {})
                    for node_name, node_runs in run_data.items():
                        for run in node_runs:
                            if run.get("error"):
                                err_msg = run["error"].get("message", "")
                                lines.append(f"- **خطأ في `{node_name}`:** {err_msg[:300]}")
                except:
                    pass
            lines.append("")

        return "\n".join(lines)

    # ─── Main Pipe ────────────────────────────────────────────

    async def pipe(
        self,
        body: dict,
        __user__: Optional[dict] = None,
        __event_emitter__: Optional[Callable[[dict], Awaitable[None]]] = None,
        __event_call__: Optional[Callable[[dict], Awaitable[dict]]] = None,
        __metadata__: Optional[dict] = None,
    ) -> Union[str, Generator, Iterator, Dict[str, Any]]:

        messages = body.get("messages", [])
        if not messages:
            return "لم أستلم رسالة."

        raw_content = messages[-1].get("content", "")
        # Handle content as list (Cline/OpenAI format: [{"type":"text","text":"..."}])
        if isinstance(raw_content, list):
            parts = []
            for part in raw_content:
                if isinstance(part, dict):
                    parts.append(part.get("text", ""))
                elif isinstance(part, str):
                    parts.append(part)
            user_text = " ".join(parts).strip()
        else:
            user_text = str(raw_content).strip()

        # Detect if request is from Cline (before stripping tags)
        import re
        is_cline = bool(re.search(r"<task>|<attempt_completion>|# Reminder:.*Tool Use|tool_progress|You are Cline", user_text, re.IGNORECASE))
        if not is_cline:
            # Also check system message for Cline signature
            for msg in messages:
                if msg.get("role") == "system":
                    sys_content = msg.get("content", "")
                    if isinstance(sys_content, list):
                        sys_content = " ".join(p.get("text", "") if isinstance(p, dict) else str(p) for p in sys_content)
                    if re.search(r"You are Cline|<tool_name>|attempt_completion|execute_command", str(sys_content), re.IGNORECASE):
                        is_cline = True
                        break

        # Extract actual user message from Cline's <task> tags
        task_match = re.search(r"<task>(.*?)</task>", user_text, re.DOTALL)
        if task_match:
            user_text = task_match.group(1).strip()

        # Strip Cline boilerplate (tool-use reminders, task_progress, etc.)
        cline_noise = [
            r"#\s*task_progress.*",
            r"#\s*Reminder:.*?Tool Use.*",
            r"Tool uses are formatted using XML.*",
            r"When starting a new task.*?task_progress.*",
            r"\[ERROR\] You did not use a tool.*",
            r"Instructions for Tool Use.*",
        ]
        for pattern in cline_noise:
            user_text = re.sub(pattern, "", user_text, flags=re.DOTALL | re.IGNORECASE)
        user_text = user_text.strip()

        if not user_text:
            # Empty after stripping Cline noise → default to full scan
            user_text = "فحص"

        # Detect command type
        text_lower = user_text.lower()
        scan_commands = ["ابدأ", "فحص", "scan", "check", "health", "status", "diagnose",
                         "فحص شامل", "تشخيص", "حالة النظام", "صحة النظام", "افحص"]
        n8n_commands = ["n8n", "فشل", "تنفيذات", "executions", "workflows", "سير العمل"]
        error_keywords = ["error", "exception", "traceback", "failed", "خطأ", "مشكلة",
                          "crash", "bug", "timeout", "refused", "denied", "404", "500",
                          "null", "undefined", "cannot", "could not", "unable"]

        is_scan = any(cmd in text_lower for cmd in scan_commands) and len(user_text) < 30
        is_n8n_inspect = any(cmd in text_lower for cmd in n8n_commands) and len(user_text) < 50
        is_error = any(kw in text_lower for kw in error_keywords) or len(user_text) >= 30

        async with aiohttp.ClientSession() as session:
            if is_scan:
                await self._emit(__event_emitter__, "in_progress", "🏥 فحص شامل للنظام...", False)
                start = time.time()
                report = await self._full_scan(session, __event_emitter__)
                elapsed = round(time.time() - start, 1)
                await self._emit(__event_emitter__, "complete", f"✅ اكتمل الفحص ({elapsed}s)", True)
                result = report + f"\n\n---\n⏱️ زمن الفحص: {elapsed} ثانية"
                return self._wrap_cline(result) if is_cline else result

            elif is_n8n_inspect:
                start = time.time()
                report = await self._inspect_n8n_failures(session, __event_emitter__)
                elapsed = round(time.time() - start, 1)
                await self._emit(__event_emitter__, "complete", f"✅ فحص n8n ({elapsed}s)", True)
                return self._wrap_cline(report) if is_cline else report

            elif is_error:
                start = time.time()
                report = await self._search_error(session, user_text, __event_emitter__)
                elapsed = round(time.time() - start, 1)
                await self._emit(__event_emitter__, "complete", f"✅ بحث ({elapsed}s)", True)
                return self._wrap_cline(report) if is_cline else report

            else:
                await self._emit(__event_emitter__, "complete", "💡 أرسل أمراً", True)
                help_text = (
                    "## 🔍 صائد الأخطاء V3\n\n"
                    "**الأوامر المتاحة:**\n\n"
                    "| الأمر | الوظيفة |\n"
                    "|-------|--------|\n"
                    "| `ابدأ` / `فحص` / `scan` | فحص شامل لجميع الخدمات |\n"
                    "| `n8n` / `تنفيذات` | فحص تنفيذات n8n الفاشلة |\n"
                    "| رسالة خطأ (30+ حرف) | بحث عن حلول |\n\n"
                    "**أمثلة:**\n"
                    "- `فحص` → تقرير صحة كامل\n"
                    "- `ConnectionRefusedError: Connection refused on port 6379` → بحث عن حل\n"
                    "- `n8n فشل` → فحص التنفيذات الفاشلة\n"
                )
                return self._wrap_cline(help_text) if is_cline else help_text
