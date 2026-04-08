"""
title: n8n Automation Tool
author: Saleh Custom
version: 4.0
description: أداة أتمتة n8n ذكية - فلتر يعمل مع أي موديل. يستخدم RAG وبحث الويب لتصميم سير عمل أفضل وحل المشاكل تلقائياً
"""

from typing import Dict, Any, List, Optional
import json
import time
import re
import sys
import os
import requests
from pydantic import BaseModel


class Pipeline:
    _RESERVED_WORKFLOW_REFS = {
        "run_workflow", "list_workflows", "get_workflow", "activate_workflow",
        "deactivate_workflow", "list_executions", "diagnose_workflow",
        "auto_fix_workflow", "delete_workflow", "trigger_workflow",
        "workflow", "workflows", "run", "trigger", "action", "args",
    }

    class Valves(BaseModel):
        pipelines: List[str] = ["*"]
        n8n_url: str = os.getenv("N8N_BASE_URL", "http://n8n:5678")
        n8n_api_key: str = os.getenv("N8N_API_KEY", "")
        n8n_basic_user: str = os.getenv("N8N_BASIC_AUTH_USER", "")
        n8n_basic_password: str = os.getenv("N8N_BASIC_AUTH_PASSWORD", "")
        n8n_login_email: str = os.getenv("N8N_LOGIN_EMAIL", "salmajnouni@gmail.com")
        n8n_login_password: str = os.getenv("N8N_LOGIN_PASSWORD", "SalehSaaS2026!")
        # RAG - ChromaDB
        chromadb_url: str = "http://chromadb:8000"
        chromadb_tenant: str = "default_tenant"
        chromadb_database: str = "default_database"
        chromadb_collection: str = "saleh_knowledge_qwen3"
        ollama_url: str = "http://host.docker.internal:11434"
        embedding_model: str = "qwen3-embedding:0.6b"
        rag_top_k: int = 10
        rag_min_score: float = 0.40
        # Web Search - SearXNG
        searxng_url: str = "http://searxng:8080"
        searxng_max_results: int = 3
        # Features toggle
        enable_rag: bool = True
        enable_web_search: bool = False  # DuckDuckGo engine broken in SearXNG - disable until fixed

    def __init__(self):
        self.type = "filter"
        self.name = "n8n Automation Tool"
        self.valves = self.Valves()
        self._workflow_cache: List[dict] = []
        self._login_cookies: Optional[dict] = None
        self._login_ts: float = 0.0

    # ─────────────────────────────────────────
    # n8n API Methods
    # ─────────────────────────────────────────

    def _n8n_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.valves.n8n_api_key:
            headers["X-N8N-API-KEY"] = self.valves.n8n_api_key
        return headers

    def _n8n_api(self, method: str, endpoint: str, data: dict = None) -> dict:
        api_url = f"{self.valves.n8n_url}/api/v1{endpoint}"
        auth = None
        if self.valves.n8n_basic_user and self.valves.n8n_basic_password:
            auth = (self.valves.n8n_basic_user, self.valves.n8n_basic_password)
        try:
            resp = requests.request(method, api_url, headers=self._n8n_headers(), json=data, auth=auth, timeout=30)
            if resp.status_code < 400:
                return resp.json() if resp.text else {}

            if resp.status_code not in (401, 403):
                return {"error": f"n8n API {resp.status_code}: {resp.text[:300]}"}

            cookies = self._n8n_login()
            if not cookies:
                return {"error": f"n8n API {resp.status_code}: {resp.text[:300]}"}

            rest_url = f"{self.valves.n8n_url}/rest{endpoint}"
            rest_resp = requests.request(method, rest_url, json=data, cookies=cookies, auth=auth, timeout=30)
            if rest_resp.status_code >= 400:
                return {"error": f"n8n REST {rest_resp.status_code}: {rest_resp.text[:300]}"}
            return rest_resp.json() if rest_resp.text else {}
        except Exception as e:
            return {"error": str(e)}

    def _n8n_login(self, force: bool = False) -> Optional[dict]:
        if not force and self._login_cookies and (time.time() - self._login_ts) < 600:
            return self._login_cookies

        try:
            resp = requests.post(
                f"{self.valves.n8n_url}/rest/login",
                json={
                    "emailOrLdapLoginId": self.valves.n8n_login_email,
                    "password": self.valves.n8n_login_password,
                },
                timeout=15,
            )
            if resp.status_code == 429 and self._login_cookies:
                return self._login_cookies
            if resp.status_code != 200:
                return None
            cookie = resp.cookies.get("n8n-auth")
            if not cookie:
                sc = resp.headers.get("set-cookie", "")
                if "n8n-auth=" in sc:
                    cookie = sc.split("n8n-auth=")[1].split(";")[0]
            if not cookie:
                return None
            self._login_cookies = {"n8n-auth": cookie}
            self._login_ts = time.time()
            return self._login_cookies
        except Exception:
            return None

    def _list_workflows(self) -> str:
        result = self._n8n_api("GET", "/workflows")
        if "error" in result:
            return f"خطأ في جلب سير العمل: {result['error']}"
        workflows = result.get("data", [])
        if not workflows:
            return "لا توجد سير عمل حالياً على n8n."
        lines = []
        for wf in workflows:
            status = "🟢 نشط" if wf.get("active") else "⚪ متوقف"
            lines.append(f"- **{wf['name']}** (ID: `{wf['id']}`) — {status}")
        return "\n".join(lines)

    def _all_workflows(self) -> List[dict]:
        for _ in range(3):
            result = self._n8n_api("GET", "/workflows")
            if "error" not in result:
                data = result.get("data", [])
                if isinstance(data, list) and data:
                    self._workflow_cache = data
                    return data
            time.sleep(0.5)

        cookies = self._n8n_login()
        if cookies:
            try:
                resp = requests.get(f"{self.valves.n8n_url}/rest/workflows", cookies=cookies, timeout=20)
                if resp.status_code == 200:
                    payload = resp.json()
                    data = payload.get("data", payload)
                    if isinstance(data, dict):
                        data = data.get("data", data.get("results", []))
                    if isinstance(data, list) and data:
                        self._workflow_cache = data
                        return data
            except Exception:
                pass

        return self._workflow_cache

    def _resolve_workflow_id(self, workflow_ref: str) -> Optional[str]:
        if not workflow_ref:
            return None
        if workflow_ref.strip().lower() in self._RESERVED_WORKFLOW_REFS:
            return None
        workflows = self._all_workflows()
        if not workflows:
            ref = workflow_ref.strip()
            if re.match(r"^[A-Za-z0-9_-]{4,}$", ref) and ref.lower() not in self._RESERVED_WORKFLOW_REFS:
                return ref
            return None

        ref = workflow_ref.strip().lower()
        for wf in workflows:
            if str(wf.get("id", "")).lower() == ref:
                return wf.get("id")

        exact_name = [wf for wf in workflows if str(wf.get("name", "")).strip().lower() == ref]
        if exact_name:
            return exact_name[0].get("id")

        partial = [wf for wf in workflows if ref in str(wf.get("name", "")).lower()]
        if len(partial) == 1:
            return partial[0].get("id")

        # Fallback: accept direct workflow IDs even if list matching fails
        raw_ref = workflow_ref.strip()
        if re.match(r"^[A-Za-z0-9_-]{4,}$", raw_ref) and raw_ref.lower() not in self._RESERVED_WORKFLOW_REFS:
            return raw_ref

        return None

    def _execution_error_text(self, execution_data: dict) -> str:
        if not isinstance(execution_data, dict):
            return ""

        error_obj = execution_data.get("error", {})
        if isinstance(error_obj, dict):
            msg = error_obj.get("message")
            if msg:
                return str(msg)

        data = execution_data.get("data", execution_data)
        if isinstance(data, dict):
            result_data = data.get("resultData", {})
            if isinstance(result_data, dict):
                err = result_data.get("error", {})
                if isinstance(err, dict) and err.get("message"):
                    return str(err.get("message"))
                if isinstance(err, str):
                    return err
        return ""

    def _run_workflow_by_id(self, wf_id: str) -> dict:
        run_res = self._n8n_api("POST", f"/workflows/{wf_id}/run", {"workflowData": {"id": wf_id}})
        if "error" not in run_res:
            return run_res

        cookies = self._n8n_login()
        if not cookies:
            return run_res

        try:
            wf_resp = requests.get(f"{self.valves.n8n_url}/rest/workflows/{wf_id}", cookies=cookies, timeout=15)
            wf_data = wf_resp.json().get("data", wf_resp.json()) if wf_resp.status_code == 200 else None
            auth = None
            if self.valves.n8n_basic_user and self.valves.n8n_basic_password:
                auth = (self.valves.n8n_basic_user, self.valves.n8n_basic_password)

            attempts = [
                (f"{self.valves.n8n_url}/rest/workflows/{wf_id}/execute", {}),
                (f"{self.valves.n8n_url}/rest/workflows/{wf_id}/execute", {"workflowData": {"id": wf_id}}),
                (f"{self.valves.n8n_url}/rest/workflows/{wf_id}/run", {"workflowData": {"id": wf_id}}),
            ]

            if isinstance(wf_data, dict):
                trigger_name = "Manual Trigger"
                for node in wf_data.get("nodes", []):
                    if "trigger" in node.get("type", "").lower():
                        trigger_name = node.get("name", "Manual Trigger")
                        break
                attempts.append(
                    (
                        f"{self.valves.n8n_url}/rest/workflows/{wf_id}/run",
                        {"workflowData": wf_data, "triggerToStartFrom": {"name": trigger_name, "data": {}}},
                    )
                )

            last_error = ""
            for url, payload in attempts:
                rest_run = requests.post(url, json=payload, cookies=cookies, auth=auth, timeout=120)
                if rest_run.status_code < 400:
                    return rest_run.json() if rest_run.text else {}
                last_error = f"{rest_run.status_code}: {rest_run.text[:200]}"

            if last_error:
                return {"error": f"REST run failed: {last_error}"}
        except Exception:
            pass

        return run_res

    def _archive_and_delete_workflow(self, wf_id: str) -> str:
        cookies = self._n8n_login()
        if not cookies:
            return "❌ لا يمكن حذف سير العمل: فشل تسجيل الدخول إلى n8n."

        try:
            arch = requests.post(f"{self.valves.n8n_url}/rest/workflows/{wf_id}/archive", cookies=cookies, timeout=20)
            if arch.status_code >= 400:
                return f"❌ فشل أرشفة سير العمل قبل الحذف: {arch.status_code}"
            delete = requests.delete(f"{self.valves.n8n_url}/rest/workflows/{wf_id}", cookies=cookies, timeout=20)
            if delete.status_code >= 400:
                return f"❌ فشل حذف سير العمل: {delete.status_code} {delete.text[:200]}"
            return f"✅ تم حذف سير العمل بنجاح (ID: `{wf_id}`)."
        except Exception as e:
            return f"❌ فشل حذف سير العمل: {e}"

    def _diagnose_workflow(self, workflow_ref: str) -> str:
        wf_id = self._resolve_workflow_id(workflow_ref)
        if not wf_id:
            return "❌ لم أستطع تحديد سير العمل المطلوب للتشخيص."

        wf = self._n8n_api("GET", f"/workflows/{wf_id}")
        if "error" in wf:
            return f"❌ فشل جلب سير العمل: {wf['error']}"

        wf_data = wf.get("data", wf)
        name = wf_data.get("name", wf_id)
        active = wf_data.get("active", False)
        nodes = wf_data.get("nodes", [])
        lines = [
            f"🩺 تشخيص سير العمل: **{name}** (ID: `{wf_id}`)",
            f"- الحالة: {'🟢 نشط' if active else '⚪ متوقف'}",
            f"- عدد العقد: {len(nodes)}",
        ]

        cred_issues = []
        for node in nodes:
            creds = node.get("credentials", {})
            if isinstance(creds, dict):
                for _, c in creds.items():
                    if isinstance(c, dict) and not c.get("id"):
                        cred_issues.append(node.get("name", "Unknown Node"))
        if cred_issues:
            lines.append("- ⚠️ عقد بلا credential id: " + ", ".join(sorted(set(cred_issues))))

        execs = self._n8n_api("GET", f"/executions?limit=5&workflowId={wf_id}")
        if "error" in execs:
            lines.append(f"- ⚠️ تعذر جلب آخر التنفيذات: {execs['error']}")
            return "\n".join(lines)

        raw = execs.get("data", [])
        if isinstance(raw, dict):
            data = raw.get("data", raw.get("results", []))
            if isinstance(data, dict):
                data = data.get("results", data.get("data", []))
        elif isinstance(raw, list):
            data = raw
        else:
            data = []

        data = [e for e in data if isinstance(e, dict)]
        data = [e for e in data if str(e.get("workflowId", "")) == str(wf_id)]
        if not data:
            lines.append("- لا توجد تنفيذات حديثة.")
            return "\n".join(lines)

        failed = [e for e in data if str(e.get("status", "")).lower() in ("error", "failed", "crashed")]
        lines.append(f"- آخر التنفيذات: {len(data)} (الفاشلة: {len(failed)})")
        if failed:
            latest_failed_id = failed[0].get("id")
            details = self._n8n_api("GET", f"/executions/{latest_failed_id}")
            err_txt = self._execution_error_text(details)
            if err_txt:
                lines.append(f"- ❌ آخر خطأ: {err_txt[:500]}")
                if "Bad request - please check your parameters" in err_txt:
                    lines.append("- 💡 اقتراح: تحقق من مدخلات العقدة (chat_id/webhook/credentials) ثم أعد التفعيل.")
        return "\n".join(lines)

    def _auto_fix_workflow(self, workflow_ref: str) -> str:
        wf_id = self._resolve_workflow_id(workflow_ref)
        if not wf_id:
            return "❌ لم أستطع تحديد سير العمل للإصلاح التلقائي."

        wf = self._n8n_api("GET", f"/workflows/{wf_id}")
        if "error" in wf:
            return f"❌ فشل جلب سير العمل: {wf['error']}"
        wf_data = wf.get("data", wf)
        lines = [f"🔧 بدء إصلاح سير العمل: **{wf_data.get('name', wf_id)}** (ID: `{wf_id}`)"]

        if not wf_data.get("active"):
            act = self._n8n_api("PATCH", f"/workflows/{wf_id}/activate", {})
            if "error" in act:
                lines.append(f"- ⚠️ تعذر التفعيل: {act['error']}")
            else:
                lines.append("- ✅ تم تفعيل سير العمل.")

        run_res = self._run_workflow_by_id(wf_id)
        if "error" in run_res:
            lines.append(f"- ⚠️ تعذر التشغيل التجريبي: {run_res['error']}")
            return "\n".join(lines)

        exec_id = run_res.get("data", {}).get("executionId", run_res.get("executionId"))
        if not exec_id:
            lines.append("- ⚠️ لم يتم إرجاع رقم تنفيذ للتشغيل التجريبي.")
            return "\n".join(lines)

        time.sleep(2)
        details = self._n8n_api("GET", f"/executions/{exec_id}")
        if "error" in details:
            lines.append(f"- ⚠️ تعذر فحص نتيجة التنفيذ: {details['error']}")
            return "\n".join(lines)

        status = details.get("status", details.get("data", {}).get("status", "unknown"))
        if str(status).lower() in ("success", "finished", "done"):
            lines.append(f"- ✅ الإصلاح ناجح. Execution ID: `{exec_id}`")
        else:
            err_txt = self._execution_error_text(details)
            lines.append(f"- ❌ ما زالت المشكلة قائمة. Execution ID: `{exec_id}`")
            if err_txt:
                lines.append(f"- سبب الفشل: {err_txt[:500]}")

        return "\n".join(lines)

    def _execute_action(self, action_payload: dict) -> str:
        if not isinstance(action_payload, dict):
            return "❌ n8n-action يجب أن يكون JSON object."

        action = str(action_payload.get("action", "")).strip().lower()
        args = action_payload.get("args", {}) or {}

        try:
            if action == "list_workflows":
                return self._list_workflows()

            if action == "get_workflow":
                wf_id = self._resolve_workflow_id(str(args.get("workflow", args.get("workflow_id", ""))))
                if not wf_id:
                    return "❌ لم أستطع تحديد سير العمل."
                data = self._n8n_api("GET", f"/workflows/{wf_id}")
                return json.dumps(data, ensure_ascii=False, indent=2)

            if action == "run_workflow":
                wf_id = self._resolve_workflow_id(str(args.get("workflow", args.get("workflow_id", ""))))
                if not wf_id:
                    return "❌ لم أستطع تحديد سير العمل للتشغيل."
                run_res = self._run_workflow_by_id(wf_id)
                if "error" in run_res:
                    return f"❌ فشل التشغيل: {run_res['error']}"
                exec_id = run_res.get("data", {}).get("executionId", run_res.get("executionId", "unknown"))
                return f"✅ تم تشغيل سير العمل. Execution ID: `{exec_id}`"

            if action == "activate_workflow":
                wf_id = self._resolve_workflow_id(str(args.get("workflow", args.get("workflow_id", ""))))
                if not wf_id:
                    return "❌ لم أستطع تحديد سير العمل للتفعيل."
                # n8n deployments differ here: some accept POST, others PATCH.
                res = self._n8n_api("POST", f"/workflows/{wf_id}/activate", {})
                if "error" in res and ("405" in str(res.get("error", "")) or "method not allowed" in str(res.get("error", "")).lower()):
                    res = self._n8n_api("PATCH", f"/workflows/{wf_id}/activate", {})
                if "error" in res:
                    return f"❌ فشل التفعيل: {res['error']}"
                return f"✅ تم تفعيل سير العمل (ID: `{wf_id}`)."

            if action == "deactivate_workflow":
                wf_id = self._resolve_workflow_id(str(args.get("workflow", args.get("workflow_id", ""))))
                if not wf_id:
                    return "❌ لم أستطع تحديد سير العمل للإيقاف."
                # n8n deployments differ here: some accept POST, others PATCH.
                res = self._n8n_api("POST", f"/workflows/{wf_id}/deactivate", {})
                if "error" in res and ("405" in str(res.get("error", "")) or "method not allowed" in str(res.get("error", "")).lower()):
                    res = self._n8n_api("PATCH", f"/workflows/{wf_id}/deactivate", {})
                if "error" in res:
                    return f"❌ فشل الإيقاف: {res['error']}"
                return f"✅ تم إيقاف سير العمل (ID: `{wf_id}`)."

            if action == "list_executions":
                wf_id = None
                if args.get("workflow") or args.get("workflow_id"):
                    wf_id = self._resolve_workflow_id(str(args.get("workflow", args.get("workflow_id", ""))))
                    if not wf_id:
                        return "❌ لم أستطع تحديد سير العمل لتصفية التنفيذات."
                limit = int(args.get("limit", 10))
                endpoint = f"/executions?limit={limit}"
                if wf_id:
                    endpoint += f"&workflowId={wf_id}"
                data = self._n8n_api("GET", endpoint)
                if "error" in data:
                    return f"❌ فشل جلب التنفيذات: {data['error']}"
                raw_rows = data.get("data", [])
                if isinstance(raw_rows, dict):
                    rows = raw_rows.get("data", raw_rows.get("results", []))
                    if isinstance(rows, dict):
                        rows = rows.get("results", rows.get("data", []))
                elif isinstance(raw_rows, list):
                    rows = raw_rows
                else:
                    rows = []
                rows = [r for r in rows if isinstance(r, dict)]
                if wf_id:
                    rows = [r for r in rows if str(r.get("workflowId", "")) == str(wf_id)]
                if not rows:
                    return "لا توجد تنفيذات."
                lines = ["ID | Status | Workflow | Started"]
                for e in rows:
                    lines.append(f"{e.get('id')} | {e.get('status')} | {e.get('workflowId')} | {str(e.get('startedAt', ''))[:19]}")
                return "\n".join(lines)

            if action == "diagnose_workflow":
                wf_ref = str(args.get("workflow", args.get("workflow_id", "")))
                return self._diagnose_workflow(wf_ref)

            if action == "auto_fix_workflow":
                wf_ref = str(args.get("workflow", args.get("workflow_id", "")))
                return self._auto_fix_workflow(wf_ref)

            if action == "delete_workflow":
                wf_id = self._resolve_workflow_id(str(args.get("workflow", args.get("workflow_id", ""))))
                if not wf_id:
                    return "❌ لم أستطع تحديد سير العمل للحذف."
                return self._archive_and_delete_workflow(wf_id)

            return f"❌ إجراء غير معروف: `{action}`"
        except Exception as e:
            return f"❌ فشل تنفيذ n8n-action: {e}"

    def _extract_action_payloads(self, text: str) -> List[dict]:
        payloads: List[dict] = []
        if not text:
            return payloads

        # 1) Preferred explicit fenced block
        action_pattern = r"```n8n-action\s*(.*?)\s*```"
        for block in re.findall(action_pattern, text, re.DOTALL):
            try:
                obj = json.loads(block)
                if isinstance(obj, dict) and obj.get("action"):
                    payloads.append(obj)
            except Exception:
                pass

        if payloads:
            return payloads

        # 2) Plain JSON object fallback with nested-brace support
        decoder = json.JSONDecoder()
        idx = 0
        while idx < len(text):
            brace = text.find("{", idx)
            if brace == -1:
                break
            try:
                obj, end = decoder.raw_decode(text[brace:])
                if isinstance(obj, dict) and obj.get("action"):
                    payloads.append(obj)
                idx = brace + end
            except Exception:
                idx = brace + 1

        return payloads

    def _infer_action_from_user_text(self, text: str) -> Optional[dict]:
        if not text:
            return None

        raw = text.strip()
        lowered = raw.lower()

        # List executions intent
        if (
            "list_executions" in lowered
            or "list executions" in lowered
            or "اعرض التنفيذات" in raw
            or "شوف التنفيذات" in raw
            or "آخر التنفيذات" in raw
            or "سجل التنفيذات" in raw
            or ("executions" in lowered and "list" in lowered)
        ):
            wf_ref = self._extract_workflow_ref(raw)
            args = {"limit": 10}
            if wf_ref:
                args["workflow_id"] = wf_ref
            return {"action": "list_executions", "args": args}

        # List workflows intent
        if (
            "list_workflows" in lowered
            or "show workflows" in lowered
            or "list workflows" in lowered
            or ("اعرض" in raw and ("workflow" in lowered or "ورك" in raw or "سير" in raw))
        ):
            return {"action": "list_workflows"}

        # Diagnose intent
        if "diagnose_workflow" in lowered or "شخص" in raw or "تشخيص" in raw:
            wf_ref = self._extract_workflow_ref(raw)
            if wf_ref:
                return {"action": "diagnose_workflow", "args": {"workflow": wf_ref}}

        # Auto-fix intent
        if "auto_fix_workflow" in lowered or "اصلح" in raw or "إصلاح" in raw:
            wf_ref = self._extract_workflow_ref(raw)
            if wf_ref:
                return {"action": "auto_fix_workflow", "args": {"workflow": wf_ref}}

        # Run workflow intent
        if (
            "run_workflow" in lowered
            or "trigger_workflow" in lowered
            or "run workflow" in lowered
            or "شغل" in raw
            or "شغّل" in raw
            or "نفذ" in raw
            or "تشغيل" in raw
        ):
            wf_ref = self._extract_workflow_ref(raw)
            if wf_ref:
                return {"action": "run_workflow", "args": {"workflow_id": wf_ref}}

        return None

    def _extract_workflow_ref(self, text: str) -> Optional[str]:
        if not text:
            return None

        # Try JSON-first extraction to avoid misreading action names as workflow ids
        decoder = json.JSONDecoder()
        idx = 0
        while idx < len(text):
            brace = text.find("{", idx)
            if brace == -1:
                break
            try:
                obj, end = decoder.raw_decode(text[brace:])
                idx = brace + end
            except Exception:
                idx = brace + 1
                continue

            if not isinstance(obj, dict):
                continue

            args = obj.get("args", {}) if isinstance(obj.get("args", {}), dict) else {}
            for key in ("workflow_id", "workflow"):
                v = args.get(key, obj.get(key))
                if isinstance(v, str):
                    candidate = v.strip()
                    if candidate and candidate.lower() not in self._RESERVED_WORKFLOW_REFS:
                        return candidate

        # Prefer explicit workflow_id patterns first
        patterns = [
            r'workflow_id\s*[=:]\s*["\']?([A-Za-z0-9_-]{4,})["\']?',
            r'id\s*[=:]\s*["\']?([A-Za-z0-9_-]{4,})["\']?',
            r'workflow\s*[=:]\s*["\']?([A-Za-z0-9_-]{4,})["\']?',
        ]
        for p in patterns:
            m = re.search(p, text, re.IGNORECASE)
            if m:
                candidate = m.group(1)
                if (
                    candidate
                    and candidate.lower() not in self._RESERVED_WORKFLOW_REFS
                    and not ("workflow" in candidate.lower() and not re.search(r"\d", candidate))
                ):
                    return candidate

        # Prefer id-like tokens that contain at least one digit (common in n8n workflow IDs)
        id_like_tokens = re.findall(r"\b[A-Za-z][A-Za-z0-9_-]*\d+[A-Za-z0-9_-]*\b", text)
        for tok in id_like_tokens:
            low = tok.lower()
            if low in self._RESERVED_WORKFLOW_REFS:
                continue
            if low in {"n8n-action", "n8n_action", "nn8n-action", "nn8n_action"}:
                continue
            if low.endswith("run_workflow") or low.endswith("trigger_workflow"):
                continue
                return tok

        # Fallback: any token that looks like an n8n id/name reference (e.g., CwCounclTele001)
        tokens = re.findall(r"\b[A-Za-z][A-Za-z0-9_-]{3,}\b", text)
        ignore = {
            "workflow", "workflows", "trigger", "run", "json", "create", "file",
            "manual", "request", "arguments", "action", "python", "http",
            "list", "show", "execute", "code", "function", "functions",
            "n8n-action", "n8n_action",
            "run_workflow", "list_workflows", "get_workflow", "activate_workflow",
            "deactivate_workflow", "list_executions", "diagnose_workflow",
            "auto_fix_workflow", "delete_workflow", "trigger_workflow"
        }
        for tok in tokens:
            low = tok.lower()
            if low in ignore:
                continue
            if low in self._RESERVED_WORKFLOW_REFS:
                continue
            if "workflow" in low and not re.search(r"\d", tok):
                continue
            if re.match(r"^[a-z]+_workflow$", low):
                continue
            if low.startswith("un_workflow") or low.startswith("n_workflow"):
                continue
            if low.endswith("run_workflow") or low.endswith("trigger_workflow"):
                continue
            if tok:
                return tok

        return None

    def _create_and_run_workflow(self, workflow_json: dict) -> str:
        result = self._n8n_api("POST", "/workflows", workflow_json)
        if "error" in result:
            return f"❌ خطأ في إنشاء سير العمل: {result['error']}"

        created = result.get("data", result)
        wf_id = created.get("id")
        wf_name = created.get("name", "سير عمل جديد")
        output = f"✅ تم إنشاء **{wf_name}** على n8n (ID: `{wf_id}`)\n"

        exec_result = self._run_workflow_by_id(wf_id)
        if "error" in exec_result:
            output += f"⚠️ فشل التشغيل التلقائي عبر API. شغّله من: http://localhost:5678/workflow/{wf_id}\n"
            return output

        exec_id = exec_result.get("data", {}).get("executionId", exec_result.get("executionId"))

        if exec_id:
            start = time.time()
            while time.time() - start < 60:
                exec_result = self._n8n_api("GET", f"/executions/{exec_id}")
                if "error" not in exec_result:
                    status = exec_result.get("status", exec_result.get("finished"))
                    if status in ("success", True):
                        output += "✅ تم التنفيذ بنجاح!\n"
                        break
                    if status in ("error", "crashed"):
                        output += "❌ فشل التنفيذ. تحقق من التفاصيل في n8n.\n"
                        break
                time.sleep(3)

        output += f"🔗 http://localhost:5678/workflow/{wf_id}"
        return output

    # ─────────────────────────────────────────
    # RAG - ChromaDB Search
    # ─────────────────────────────────────────

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
            print(f"[n8n-tool] Embedding error: {e}", file=sys.stderr)
        return None

    def _get_collection_id(self) -> Optional[str]:
        try:
            url = f"{self.valves.chromadb_url}/api/v1/collections/{self.valves.chromadb_collection}"
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                return resp.json().get("id")
        except Exception as e:
            print(f"[n8n-tool] ChromaDB collection error: {e}", file=sys.stderr)
        return None

    def _search_rag(self, query: str) -> str:
        """Search ChromaDB for relevant knowledge about the user's request"""
        if not self.valves.enable_rag:
            return ""

        embedding = self._get_embedding(query)
        if not embedding:
            return ""

        collection_id = self._get_collection_id()
        if not collection_id:
            return ""

        try:
            url = f"{self.valves.chromadb_url}/api/v1/collections/{collection_id}/query"
            resp = requests.post(
                url,
                json={
                    "query_embeddings": [embedding],
                    "n_results": self.valves.rag_top_k,
                    "include": ["documents", "metadatas", "distances"],
                },
                timeout=15,
            )
            if resp.status_code != 200:
                return ""

            data = resp.json()
            docs = data.get("documents", [[]])[0]
            metas = data.get("metadatas", [[]])[0]
            distances = data.get("distances", [[]])[0]

            results = []
            for doc, meta, dist in zip(docs, metas, distances):
                similarity = 1 - dist
                if similarity >= self.valves.rag_min_score:
                    source = meta.get("doc_name", meta.get("law_name", meta.get("source", "وثيقة")))
                    results.append(f"**[{source}]** (تطابق: {similarity:.0%})\n{doc[:500]}")

            if results:
                return "📚 **معلومات من قاعدة المعرفة:**\n" + "\n---\n".join(results)
        except Exception as e:
            print(f"[n8n-tool] RAG search error: {e}", file=sys.stderr)

        return ""

    # ─────────────────────────────────────────
    # Web Search - SearXNG
    # ─────────────────────────────────────────

    def _search_web(self, query: str) -> str:
        """Search the web via local SearXNG for relevant information"""
        if not self.valves.enable_web_search:
            return ""

        try:
            resp = requests.get(
                f"{self.valves.searxng_url}/search",
                params={"q": query, "format": "json", "language": "ar"},
                timeout=15,
            )
            if resp.status_code != 200:
                return ""

            data = resp.json()
            results_list = data.get("results", [])[:self.valves.searxng_max_results]

            if not results_list:
                return ""

            results = []
            for r in results_list:
                title = r.get("title", "")
                snippet = r.get("content", "")[:300]
                url = r.get("url", "")
                results.append(f"- **{title}**\n  {snippet}\n  🔗 {url}")

            return "🌐 **نتائج بحث الويب:**\n" + "\n".join(results)
        except Exception as e:
            print(f"[n8n-tool] Web search error: {e}", file=sys.stderr)

        return ""

    # ─────────────────────────────────────────
    # Intent Detection
    # ─────────────────────────────────────────

    def _is_automation_request(self, content: str) -> bool:
        """Detect if the user is asking for automation/workflow tasks"""
        automation_keywords = [
            "سير عمل", "ورك فلو", "workflow", "أتمتة", "اتمتة", "automate",
            "جدولة", "schedule", "كل يوم", "كل ساعة", "بشكل دوري",
            "اسحب بيانات", "اجلب بيانات", "fetch data", "pull data",
            "أرسل إشعار", "ارسل اشعار", "send notification",
            "راقب", "monitor", "تنبيه", "alert",
            "ربط", "integrate", "تكامل", "webhook",
            "n8n", "إن 8 إن",
            "صمم لي", "أنشئ لي", "اعمل لي",
            "اعرض سير", "قائمة سير", "list workflows", "show workflows",
            "شخص", "شخّص", "شخصه", "تشخيص", "diagnose", "diagnosis",
            "اصلح", "إصلاح", "auto fix", "auto_fix_workflow",
            # Run/execute keywords (Arabic)
            "شغل", "شغّل", "نفذ", "تشغيل", "تنفيذ", "شغّله", "شغّلي",
            "run workflow", "execute workflow", "trigger workflow",
            "list_executions", "list executions", "اعرض التنفيذات", "شوف التنفيذات",
            "آخر التنفيذات", "سجل التنفيذات", "execution", "executions",
        ]
        content_lower = content.lower()
        return any(kw in content_lower for kw in automation_keywords)

    def _is_data_request(self, content: str) -> bool:
        """Detect if user is asking about data, clients, or information that RAG can help with"""
        data_keywords = [
            "بيانات", "عملاء", "عميل", "معلومات", "سجل", "سجلات",
            "قاعدة بيانات", "database", "data", "clients", "customers",
            "تقرير", "تقارير", "report", "إحصائيات", "احصائيات",
            "ملف", "ملفات", "وثيقة", "وثائق", "مستند",
            "نظام", "قانون", "لائحة", "مادة", "حكم",
            "موظف", "موظفين", "عقد", "عقود", "فاتورة", "فواتير",
            "ابحث", "جد لي", "اعطني", "وش عندنا", "كم عدد",
        ]
        content_lower = content.lower()
        return any(kw in content_lower for kw in data_keywords)

    # ─────────────────────────────────────────
    # Filter: Inlet (Before Model)
    # ─────────────────────────────────────────

    async def inlet(self, body: Dict[str, Any], __user__: Dict = None) -> Dict[str, Any]:
        """Inject n8n + RAG + web search context based on user intent"""
        messages = body.get("messages", [])
        if not messages:
            return body

        last_msg = messages[-1]
        if last_msg.get("role") != "user":
            return body

        content = last_msg.get("content", "").strip()
        if not content:
            return body

        is_automation = self._is_automation_request(content)
        is_data = self._is_data_request(content)

        # Normal conversation — pass through untouched
        if not is_automation and not is_data:
            return body

        extra_context_parts = []

        # ── RAG: Search knowledge base ──
        if is_data or is_automation:
            rag_results = self._search_rag(content)
            if rag_results:
                extra_context_parts.append(rag_results)

        # ── Web Search: Find solutions online ──
        if is_automation:
            search_query = f"n8n workflow {content}"
            web_results = self._search_web(search_query)
            if web_results:
                extra_context_parts.append(web_results)

        # ── n8n Context: Workflow capabilities ──
        if is_automation:
            wf_list = ""
            wf_list = self._list_workflows()

            n8n_context = f"""⚠️ قواعد صارمة يجب اتباعها:
1. ممنوع استخدام Python أو كود برمجي أو pyodide أو code_interpreter.
2. ممنوع قراءة ملفات أو كتابتها أو البحث في الويب لطلبات n8n.
3. للتحكم في n8n، استخدم فقط بلوك n8n-action كما موضح أدناه.
4. أجب دائماً باللغة العربية ما لم يطلب المستخدم غير ذلك.

لديك أداة أتمتة n8n متصلة محلياً.
يمكنك تصميم سير عمل كـ JSON وإرساله للإنشاء، وتشغيل سير عمل موجودة، وإدارة التنفيذات.

⛔ حدود حاكمة لا تتجاهلها:
- "نجح التنفيذ" في n8n يعني فقط أن العُقد أكملت تشغيلها — لا يعني إنشاء ملفات أو نجاح عمليات خارجية.
- لا تدّعي نجاح نسخة احتياطية إلا بعد رؤية نتيجة executeCommand وعدد [OK] فيها.
- لا تستطيع تعديل ملفات النظام (.py، .ps1، .json) مباشرة من المحادثة — هذا من مسؤولية المستخدم.
- executeCommand غير موجود في قائمة العُقد المسموح بها للإنشاء التلقائي عبر بلوك n8n-workflow.
- لا تُبلّغ بنتيجة إلا إذا جاءت فعلاً من output أداة n8n — لا تخمّن.

سير العمل الحالية:
{wf_list}

عندما يطلب المستخدم أتمتة أو سير عمل:
1. صمم سير العمل كـ JSON صالح
2. ضعه داخل بلوك ```n8n-workflow ... ``` حتى ينفذ تلقائياً
3. اشرح للمستخدم ماذا سيفعل سير العمل

للتحكم المباشر (إدارة/تشخيص/إصلاح)، استخدم بلوك:
```n8n-action
{{
    "action": "list_workflows"
}}
```

أمثلة إجراءات مدعومة:
- list_workflows
- get_workflow
- run_workflow
- activate_workflow
- deactivate_workflow
- list_executions
- diagnose_workflow
- auto_fix_workflow
- delete_workflow

سياسة إلزامية أثناء طلبات n8n:
- لا تستخدم أي أدوات بحث عامة أو أدوات خارج n8n-action.
- ممنوع التحويل إلى حلول بديلة قبل تنفيذ n8n-action المطلوب.
- إذا قال المستخدم "شغل" أو "نفّذ" فالإجراء الصحيح هو run_workflow وليس activate_workflow.
- إذا فشل الإجراء، أعد المحاولة مرة واحدة فقط ثم أرجع سبب الفشل من n8n.
- عند طلب المستخدم execution logs أو errors، يجب إرجاع IDs وحالات فعلية من التنفيذات.

مثال تشخيص:
```n8n-action
{{
    "action": "diagnose_workflow",
    "args": {{ "workflow": "Advisory Council Telegram Decisions" }}
}}
```

مثال إصلاح تلقائي:
```n8n-action
{{
    "action": "auto_fix_workflow",
    "args": {{ "workflow_id": "CwCounclTele001" }}
}}
```

الـ nodes المتاحة:
- n8n-nodes-base.manualTrigger (typeVersion: 1) - تشغيل يدوي
- n8n-nodes-base.scheduleTrigger (typeVersion: 1.2) - جدولة
- n8n-nodes-base.httpRequest (typeVersion: 4.2) - طلبات HTTP
- n8n-nodes-base.set (typeVersion: 3.4) - تعيين قيم
- n8n-nodes-base.if (typeVersion: 2.2) - شروط
- n8n-nodes-base.code (typeVersion: 2) - كود JavaScript
- n8n-nodes-base.noOp (typeVersion: 1) - بدون عملية
- n8n-nodes-base.merge (typeVersion: 3) - دمج بيانات
- n8n-nodes-base.splitInBatches (typeVersion: 3) - تقسيم دفعات
- n8n-nodes-base.wait (typeVersion: 1.1) - انتظار

لا تستخدم أي node غير موجودة في القائمة.
أول node يجب أن يكون trigger.
أضف settings: {{"executionOrder": "v1"}}

مثال:
```n8n-workflow
{{
  "name": "جلب بيانات API",
  "nodes": [
    {{"name": "Manual Trigger", "type": "n8n-nodes-base.manualTrigger", "typeVersion": 1, "position": [240, 300], "parameters": {{}}}},
    {{"name": "HTTP Request", "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2, "position": [460, 300], "parameters": {{"url": "https://api.example.com/data", "method": "GET"}}}}
  ],
  "connections": {{"Manual Trigger": {{"main": [[{{"node": "HTTP Request", "type": "main", "index": 0}}]]}}}},
  "settings": {{"executionOrder": "v1"}}
}}
```

إذا طلب المستخدم عرض سير العمل الحالية فقط، اعرضها بدون إنشاء واحد جديد."""
            extra_context_parts.append(n8n_context)

        # ── Data query context (non-automation) ──
        if is_data and not is_automation:
            data_context = """لديك قاعدة معرفة محلية تحتوي على بيانات العملاء والوثائق القانونية والسجلات.
استخدم المعلومات المتوفرة من قاعدة المعرفة (أعلاه) للإجابة بدقة.
إذا لم تجد المعلومة المطلوبة، أخبر المستخدم بذلك واقترح طريقة للحصول عليها."""
            extra_context_parts.append(data_context)

        # Build and inject the combined system context
        if not extra_context_parts:
            return body

        combined_context = "\n\n".join(extra_context_parts)

        has_system = False
        for msg in messages:
            if msg.get("role") == "system":
                msg["content"] = msg["content"] + "\n\n" + combined_context
                has_system = True
                break
        if not has_system:
            messages.insert(0, {"role": "system", "content": combined_context})

        body["messages"] = messages
        return body

    # ─────────────────────────────────────────
    # Filter: Outlet (After Model)
    # ─────────────────────────────────────────

    async def outlet(self, body: Dict[str, Any], __user__: Dict = None) -> Dict[str, Any]:
        """Detect n8n workflow JSON in assistant response, auto-execute, and handle errors smartly"""
        messages = body.get("messages", [])
        if not messages:
            return body

        last_msg = messages[-1]
        if last_msg.get("role") != "assistant":
            return body

        content = last_msg.get("content", "")

        # Look for n8n-workflow and n8n-action code blocks
        wf_pattern = r"```n8n-workflow\s*(.*?)\s*```"
        action_pattern = r"```n8n-action\s*(.*?)\s*```"
        wf_matches = re.findall(wf_pattern, content, re.DOTALL)
        action_matches = re.findall(action_pattern, content, re.DOTALL)

        # Fallback: allow direct user action JSON execution when assistant doesn't cooperate
        latest_user_content = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                latest_user_content = msg.get("content", "")
                break

        user_action_payloads = self._extract_action_payloads(latest_user_content)
        if not action_matches and user_action_payloads:
            action_matches = [json.dumps(p, ensure_ascii=False) for p in user_action_payloads]

        # Natural-language fallback: infer action from latest user text
        if not action_matches:
            inferred = self._infer_action_from_user_text(latest_user_content)
            if inferred:
                action_matches = [json.dumps(inferred, ensure_ascii=False)]

        if not wf_matches and not action_matches:
            return body

        execution_results = []

        for action_raw in action_matches:
            try:
                action_payload = json.loads(action_raw)
            except json.JSONDecodeError:
                execution_results.append("❌ JSON غير صالح في n8n-action")
                continue
            execution_results.append(self._execute_action(action_payload))

        for match in wf_matches:
            try:
                wf_json = json.loads(match)
            except json.JSONDecodeError:
                execution_results.append("❌ JSON غير صالح في سير العمل")
                continue

            # Validate nodes
            allowed_types = {
                "n8n-nodes-base.manualTrigger", "n8n-nodes-base.scheduleTrigger",
                "n8n-nodes-base.httpRequest", "n8n-nodes-base.set",
                "n8n-nodes-base.if", "n8n-nodes-base.code",
                "n8n-nodes-base.noOp", "n8n-nodes-base.merge",
                "n8n-nodes-base.splitInBatches", "n8n-nodes-base.wait",
            }
            if "nodes" in wf_json:
                clean = [n for n in wf_json["nodes"] if n.get("type") in allowed_types]
                removed = [n.get("name") for n in wf_json["nodes"] if n.get("type") not in allowed_types]
                wf_json["nodes"] = clean
                if removed and "connections" in wf_json:
                    for name in removed:
                        wf_json["connections"].pop(name, None)

            result = self._create_and_run_workflow(wf_json)
            execution_results.append(result)

            # If execution failed, search for a solution
            if "❌" in result and self.valves.enable_web_search:
                error_search = self._search_web(f"n8n workflow error {result[:100]}")
                if error_search:
                    execution_results.append("\n💡 **حلول مقترحة من الويب:**\n" + error_search)

        if execution_results:
            content += "\n\n---\n**نتيجة التنفيذ على n8n:**\n" + "\n".join(execution_results)
            last_msg["content"] = content

        body["messages"] = messages
        return body
