#!/usr/bin/env python3
"""
SaleH Brain Agent - العقل الذكي لمنصة SaleHSaaS 3.0
يراقب الأداء، يُحلّل عبر Ollama، ويتخذ قرارات تلقائية

ملاحظة تشغيلية:
هذا الوكيل يعكس تكوينًا تاريخيًا أقدم (يتضمن خدمات مثل AnythingLLM/Redis)
ولا يُستخدم كمرجع حاكم لخدمات التشغيل الحالية.
"""

import os
import json
import time
import logging
import requests
import subprocess
from datetime import datetime
from typing import Dict, List, Optional

# ── إعداد السجلات ──────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/saleh_brain.log'),
        logging.StreamHandler()
    ]
)
log = logging.getLogger("SaleHBrain")

# ── الإعدادات ──────────────────────────────────────────────────────────────
PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://prometheus:9090")
OLLAMA_URL     = os.getenv("OLLAMA_URL",     "http://ollama:11434")
N8N_URL        = os.getenv("N8N_URL",        "http://n8n:5678")
N8N_API_KEY    = os.getenv("N8N_API_KEY",    "")
OLLAMA_MODEL   = os.getenv("OLLAMA_MODEL",   "llama3:latest")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "300"))  # 5 دقائق

# عتبات التنبيه
CPU_HIGH_THRESHOLD    = float(os.getenv("CPU_HIGH_THRESHOLD",    "80"))  # %
CPU_LOW_THRESHOLD     = float(os.getenv("CPU_LOW_THRESHOLD",     "20"))  # %
MEMORY_HIGH_THRESHOLD = float(os.getenv("MEMORY_HIGH_THRESHOLD", "85"))  # %
MEMORY_LOW_THRESHOLD  = float(os.getenv("MEMORY_LOW_THRESHOLD",  "30"))  # %

# الخدمات الأساسية التي يجب مراقبتها
# يمكن تخصيصها عبر متغير البيئة CRITICAL_SERVICES بصيغة CSV.
CRITICAL_SERVICES = [
    svc.strip() for svc in os.getenv(
        "CRITICAL_SERVICES",
        "salehsaas_postgres,salehsaas_chromadb,salehsaas_n8n,salehsaas_data_pipeline,salehsaas_open-terminal",
    ).split(",") if svc.strip()
]

# المهام القابلة للتأجيل في n8n (أسماء workflows)
DEFERRABLE_WORKFLOWS = [
    "backup",
    "report",
    "cleanup",
    "sync",
    "index",
]


# ── قراءة مقاييس Prometheus ────────────────────────────────────────────────
def query_prometheus(query: str) -> Optional[float]:
    """تنفيذ استعلام Prometheus وإرجاع القيمة"""
    try:
        r = requests.get(
            f"{PROMETHEUS_URL}/api/v1/query",
            params={"query": query},
            timeout=10
        )
        data = r.json()
        if data["status"] == "success" and data["data"]["result"]:
            return float(data["data"]["result"][0]["value"][1])
    except Exception as e:
        log.warning(f"Prometheus query failed: {e}")
    return None


def get_container_metrics() -> Dict:
    """جمع مقاييس جميع الحاويات"""
    metrics = {}

    # CPU لكل حاوية
    cpu_query = 'sum(rate(container_cpu_usage_seconds_total{name=~"salehsaas_.*"}[5m])) by (name) * 100'
    try:
        r = requests.get(
            f"{PROMETHEUS_URL}/api/v1/query",
            params={"query": cpu_query},
            timeout=10
        )
        data = r.json()
        if data["status"] == "success":
            for item in data["data"]["result"]:
                name = item["metric"].get("name", "unknown")
                cpu  = float(item["value"][1])
                metrics[name] = {"cpu": round(cpu, 2)}
    except Exception as e:
        log.warning(f"CPU metrics failed: {e}")

    # الذاكرة لكل حاوية
    mem_query = 'container_memory_usage_bytes{name=~"salehsaas_.*"}'
    try:
        r = requests.get(
            f"{PROMETHEUS_URL}/api/v1/query",
            params={"query": mem_query},
            timeout=10
        )
        data = r.json()
        if data["status"] == "success":
            for item in data["data"]["result"]:
                name = item["metric"].get("name", "unknown")
                mem  = float(item["value"][1]) / (1024 * 1024)  # MB
                if name in metrics:
                    metrics[name]["memory_mb"] = round(mem, 1)
                else:
                    metrics[name] = {"memory_mb": round(mem, 1)}
    except Exception as e:
        log.warning(f"Memory metrics failed: {e}")

    return metrics


def get_system_summary(metrics: Dict) -> Dict:
    """تلخيص حالة النظام"""
    total_cpu    = sum(v.get("cpu", 0) for v in metrics.values())
    total_memory = sum(v.get("memory_mb", 0) for v in metrics.values())
    top_cpu      = sorted(metrics.items(), key=lambda x: x[1].get("cpu", 0), reverse=True)[:3]
    top_mem      = sorted(metrics.items(), key=lambda x: x[1].get("memory_mb", 0), reverse=True)[:3]

    return {
        "timestamp":     datetime.now().isoformat(),
        "total_cpu":     round(total_cpu, 2),
        "total_memory_mb": round(total_memory, 1),
        "top_cpu_containers":    [(n, v.get("cpu", 0)) for n, v in top_cpu],
        "top_memory_containers": [(n, v.get("memory_mb", 0)) for n, v in top_mem],
        "container_count": len(metrics),
        "metrics": metrics,
    }


# ── التحليل عبر Ollama ─────────────────────────────────────────────────────
def analyze_with_ollama(summary: Dict) -> Dict:
    """إرسال ملخص النظام إلى Ollama للتحليل واتخاذ القرار"""

    prompt = f"""أنت نظام مراقبة ذكي لمنصة SaleHSaaS 3.0. حلّل البيانات التالية واتخذ القرار المناسب.

## بيانات النظام الحالية:
- إجمالي CPU: {summary['total_cpu']}%
- إجمالي الذاكرة المستخدمة: {summary['total_memory_mb']} MB
- عدد الحاويات: {summary['container_count']}
- أعلى استهلاك CPU: {summary['top_cpu_containers']}
- أعلى استهلاك ذاكرة: {summary['top_memory_containers']}

## العتبات:
- CPU عالٍ: > {CPU_HIGH_THRESHOLD}%
- CPU منخفض: < {CPU_LOW_THRESHOLD}%
- ذاكرة عالية: > {MEMORY_HIGH_THRESHOLD}%

## مطلوب منك:
أجب بـ JSON فقط بهذا الشكل:
{{
  "status": "normal|warning|critical",
  "analysis": "تحليل مختصر بالعربية",
  "actions": [
    {{
      "type": "restart_container|pause_workflows|resume_workflows|scale_down|alert_only",
      "target": "اسم الحاوية أو المهمة",
      "reason": "السبب"
    }}
  ],
  "defer_heavy_tasks": true/false,
  "advance_pending_tasks": true/false
}}"""

    try:
        r = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model":  OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.1, "num_predict": 500}
            },
            timeout=60
        )
        response_text = r.json().get("response", "")

        # استخراج JSON من الرد
        start = response_text.find("{")
        end   = response_text.rfind("}") + 1
        if start >= 0 and end > start:
            decision = json.loads(response_text[start:end])
            log.info(f"Ollama decision: {decision['status']} - {decision['analysis']}")
            return decision

    except Exception as e:
        log.error(f"Ollama analysis failed: {e}")

    # قرار افتراضي عند فشل Ollama
    return {
        "status": "normal",
        "analysis": "تعذّر الاتصال بـ Ollama، النظام يعمل بالقواعد الافتراضية",
        "actions": [],
        "defer_heavy_tasks": summary["total_cpu"] > CPU_HIGH_THRESHOLD,
        "advance_pending_tasks": summary["total_cpu"] < CPU_LOW_THRESHOLD,
    }


# ── تنفيذ القرارات ─────────────────────────────────────────────────────────
def restart_container(container_name: str):
    """إعادة تشغيل حاوية Docker"""
    try:
        result = subprocess.run(
            ["docker", "restart", container_name],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            log.info(f"✅ Restarted container: {container_name}")
        else:
            log.error(f"❌ Failed to restart {container_name}: {result.stderr}")
    except Exception as e:
        log.error(f"Restart failed: {e}")


def get_n8n_workflows() -> List[Dict]:
    """جلب قائمة workflows من n8n"""
    if not N8N_API_KEY:
        return []
    try:
        r = requests.get(
            f"{N8N_URL}/api/v1/workflows",
            headers={"X-N8N-API-KEY": N8N_API_KEY},
            timeout=10
        )
        return r.json().get("data", [])
    except Exception as e:
        log.warning(f"n8n API failed: {e}")
        return []


def pause_workflow(workflow_id: str, workflow_name: str):
    """تعطيل workflow في n8n (تأجيل)"""
    if not N8N_API_KEY:
        log.info(f"[SIMULATION] Would pause workflow: {workflow_name}")
        return
    try:
        r = requests.patch(
            f"{N8N_URL}/api/v1/workflows/{workflow_id}",
            headers={"X-N8N-API-KEY": N8N_API_KEY, "Content-Type": "application/json"},
            json={"active": False},
            timeout=10
        )
        if r.status_code == 200:
            log.info(f"⏸️  Paused workflow: {workflow_name}")
    except Exception as e:
        log.error(f"Pause workflow failed: {e}")


def resume_workflow(workflow_id: str, workflow_name: str):
    """تفعيل workflow في n8n (تقديم)"""
    if not N8N_API_KEY:
        log.info(f"[SIMULATION] Would resume workflow: {workflow_name}")
        return
    try:
        r = requests.patch(
            f"{N8N_URL}/api/v1/workflows/{workflow_id}",
            headers={"X-N8N-API-KEY": N8N_API_KEY, "Content-Type": "application/json"},
            json={"active": True},
            timeout=10
        )
        if r.status_code == 200:
            log.info(f"▶️  Resumed workflow: {workflow_name}")
    except Exception as e:
        log.error(f"Resume workflow failed: {e}")


def manage_workflows(defer: bool, advance: bool):
    """إدارة workflows بناءً على قرار Ollama"""
    workflows = get_n8n_workflows()
    if not workflows:
        log.info("No workflows found or n8n API not configured")
        return

    for wf in workflows:
        wf_name   = wf.get("name", "").lower()
        wf_id     = wf.get("id")
        wf_active = wf.get("active", False)

        is_deferrable = any(kw in wf_name for kw in DEFERRABLE_WORKFLOWS)

        if defer and is_deferrable and wf_active:
            pause_workflow(wf_id, wf["name"])

        elif advance and is_deferrable and not wf_active:
            resume_workflow(wf_id, wf["name"])


def execute_actions(actions: List[Dict]):
    """تنفيذ قائمة الإجراءات المقررة"""
    for action in actions:
        action_type = action.get("type", "")
        target      = action.get("target", "")
        reason      = action.get("reason", "")

        log.info(f"🔧 Action: {action_type} | Target: {target} | Reason: {reason}")

        if action_type == "restart_container":
            if target in CRITICAL_SERVICES:
                restart_container(target)
            else:
                log.warning(f"Container {target} not in critical services list, skipping restart")

        elif action_type == "alert_only":
            log.warning(f"⚠️  ALERT: {reason}")

        elif action_type == "pause_workflows":
            manage_workflows(defer=True, advance=False)

        elif action_type == "resume_workflows":
            manage_workflows(defer=False, advance=True)


def save_decision_log(summary: Dict, decision: Dict):
    """حفظ سجل القرارات"""
    log_entry = {
        "timestamp": summary["timestamp"],
        "total_cpu":    summary["total_cpu"],
        "total_memory": summary["total_memory_mb"],
        "status":       decision["status"],
        "analysis":     decision["analysis"],
        "actions":      decision.get("actions", []),
    }
    try:
        log_file = "/app/logs/decisions.jsonl"
        with open(log_file, "a") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    except Exception:
        pass


# ── الحلقة الرئيسية ────────────────────────────────────────────────────────
def run_agent():
    """تشغيل Agent المراقبة الذكي"""
    log.info("🕋 SaleH Brain Agent starting...")
    log.info(f"   Prometheus: {PROMETHEUS_URL}")
    log.info(f"   Ollama:     {OLLAMA_URL}")
    log.info(f"   n8n:        {N8N_URL}")
    log.info(f"   Interval:   {CHECK_INTERVAL}s")

    while True:
        try:
            log.info("─── Starting monitoring cycle ───")

            # 1. جمع المقاييس
            metrics = get_container_metrics()
            if not metrics:
                log.warning("No metrics collected, skipping cycle")
                time.sleep(CHECK_INTERVAL)
                continue

            summary = get_system_summary(metrics)
            log.info(f"📊 CPU: {summary['total_cpu']}% | Memory: {summary['total_memory_mb']}MB | Containers: {summary['container_count']}")

            # 2. تحليل Ollama
            decision = analyze_with_ollama(summary)

            # 3. تنفيذ القرارات
            if decision.get("actions"):
                execute_actions(decision["actions"])

            # 4. إدارة المهام
            manage_workflows(
                defer=decision.get("defer_heavy_tasks", False),
                advance=decision.get("advance_pending_tasks", False)
            )

            # 5. حفظ السجل
            save_decision_log(summary, decision)

            log.info(f"✅ Cycle complete | Status: {decision['status']}")

        except Exception as e:
            log.error(f"Agent cycle error: {e}")

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    run_agent()
