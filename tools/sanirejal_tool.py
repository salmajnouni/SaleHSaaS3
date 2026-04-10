"""
title: صانع الرجال - Training Operations
description: أداة إدارة التدريب | Training management tool for الرئيس (Open WebUI).
             Connects to صانع الرجال API running on WSL2 to monitor, control,
             and optimize LLM training operations.
author: Saleh Almajnouni
version: 1.0
"""

import json
import urllib.request
import urllib.error
from typing import Any
from pydantic import BaseModel, Field


class Valves(BaseModel):
    sanirejal_url: str = Field(
        default="http://host.docker.internal:8500",
        description="URL for صانع الرجال API (WSL2). Use host.docker.internal from Docker.",
    )
    timeout: int = Field(
        default=30,
        description="Request timeout in seconds",
    )


class Tools:
    """
    صانع الرجال - Training Operations Tool
    أداة صانع الرجال لإدارة عمليات التدريب

    This tool allows الرئيس to monitor, control, and optimize
    the LLM training process running on AMD Radeon 8060S via ROCm in WSL2.
    """

    def __init__(self):
        self.valves = Valves()

    def _api_call(self, endpoint: str, method: str = "GET", data: dict = None) -> dict:
        """Internal: Make API call to صانع الرجال."""
        url = f"{self.valves.sanirejal_url}{endpoint}"
        try:
            if method == "POST" and data:
                body = json.dumps(data).encode("utf-8")
                req = urllib.request.Request(
                    url, data=body,
                    headers={"Content-Type": "application/json"},
                    method="POST"
                )
            else:
                req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=self.valves.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as e:
            return {"error": f"Cannot reach صانع الرجال API: {e}. Is the API running?"}
        except Exception as e:
            return {"error": f"API call failed: {e}"}

    async def training_status(self) -> str:
        """
        Get current training status — حالة التدريب الحالية.
        Shows if training is running, current step, loss, speed.
        استخدم هذه الدالة لمعرفة هل التدريب شغال ووين وصل.
        """
        result = self._api_call("/api/status")
        if "error" in result:
            return f"❌ {result['error']}"
        running = "✅ شغال" if result.get("process_running") else "❌ متوقف"
        return f"حالة التدريب: {running}\n\n{result.get('monitor', 'No data')}\n\n{result.get('process_info', '')}"

    async def training_logs(self, last_n: int = 20) -> str:
        """
        Get recent training log lines — آخر سطور سجل التدريب.
        Shows the last N steps with loss and speed values.
        :param last_n: Number of recent log lines to retrieve (default: 20)
        """
        result = self._api_call(f"/api/logs?n={last_n}")
        if "error" in result:
            return f"❌ {result['error']}"
        return f"آخر {result.get('count', 0)} خطوة:\n\n```\n{result.get('logs', 'No logs')}\n```"

    async def loss_history(self) -> str:
        """
        Get loss history at key milestones — تاريخ الـ loss عند النقاط المهمة.
        Shows loss at steps: 1K, 5K, 10K, 25K, 50K, 75K, 100K+
        """
        result = self._api_call("/api/loss_history")
        if "error" in result:
            return f"❌ {result['error']}"
        return f"تاريخ الخسارة (Loss History):\n\n```\n{result.get('history', 'No data')}\n```"

    async def gpu_status(self) -> str:
        """
        Get GPU status — حالة كرت الشاشة AMD Radeon 8060S.
        Shows PyTorch version, GPU detection, memory usage.
        """
        result = self._api_call("/api/gpu")
        if "error" in result:
            return f"❌ {result['error']}"
        return f"حالة GPU:\n\n```\n{result.get('gpu', 'No data')}\n```"

    async def training_config(self) -> str:
        """
        Get current training configuration — إعدادات التدريب الحالية.
        Shows DEPTH, BATCH sizes, TIME_BUDGET, etc.
        """
        result = self._api_call("/api/config")
        if "error" in result:
            return f"❌ {result['error']}"
        return (
            f"إعدادات التدريب:\n\n"
            f"```\n{result.get('train_config', 'N/A')}\n```\n\n"
            f"```\n{result.get('prepare_config', 'N/A')}\n```"
        )

    async def change_config(self, param: str, value: str) -> str:
        """
        Change a training parameter — تغيير إعداد تدريب.
        Allowed params: DEPTH (4,6,8,10,12), TIME_BUDGET (seconds).
        :param param: Parameter name (DEPTH or TIME_BUDGET)
        :param value: New value
        """
        result = self._api_call("/api/config", method="POST", data={"param": param, "value": value})
        if "error" in result:
            return f"❌ {result['error']}"
        return f"✅ {result.get('result', 'Done')}\nVerify: {result.get('verify', '')}"

    async def stop_training(self) -> str:
        """
        Stop the current training process — إيقاف التدريب الحالي.
        Sends kill signal to the training process.
        ⚠️ تحذير: هذا يوقف التدريب فوراً!
        """
        result = self._api_call("/api/train/stop", method="POST")
        if "error" in result:
            return f"❌ {result['error']}"
        stopped = "✅ توقف" if result.get("stopped") else "⚠️ ممكن لسا شغال"
        return f"{result.get('result', '')}\nالحالة: {stopped}"

    async def start_training(self, time_budget: int = 300) -> str:
        """
        Start a new training run — بدء جولة تدريب جديدة.
        :param time_budget: Training duration in seconds (default: 300 = 5 minutes)
        """
        result = self._api_call("/api/train/start", method="POST", data={"time_budget": time_budget})
        if "error" in result:
            return f"❌ {result['error']}"
        running = "✅ شغال" if result.get("running") else "❌ ما اشتغل"
        return f"{result.get('result', '')}\nالحالة: {running}"

    async def suggestions(self) -> str:
        """
        Get AI suggestions for training — اقتراحات ذكية لتحسين التدريب.
        Analyzes current state and suggests improvements.
        """
        result = self._api_call("/api/suggestions")
        if "error" in result:
            return f"❌ {result['error']}"
        sugs = result.get("suggestions", [])
        metrics = result.get("metrics", {})
        text = "اقتراحات صانع الرجال:\n\n"
        for s in sugs:
            text += f"• {s}\n"
        if metrics.get("recent_avg_loss") is not None:
            text += f"\nمتوسط الخسارة الأخير: {metrics['recent_avg_loss']}"
        return text

    async def full_report(self) -> str:
        """
        Generate a comprehensive training report — تقرير شامل عن التدريب.
        Combines status, config, GPU, recent logs, and suggestions.
        استخدم هذه الدالة عندما يطلب المستخدم تقرير كامل.
        """
        sections = []

        status = self._api_call("/api/status")
        if "error" not in status:
            running = "✅ شغال" if status.get("process_running") else "❌ متوقف"
            sections.append(f"## حالة التدريب: {running}\n{status.get('monitor', '')}")

        config = self._api_call("/api/config")
        if "error" not in config:
            sections.append(f"## الإعدادات\n```\n{config.get('train_config', '')}\n{config.get('prepare_config', '')}\n```")

        gpu = self._api_call("/api/gpu")
        if "error" not in gpu:
            sections.append(f"## GPU\n```\n{gpu.get('gpu', '')}\n```")

        logs = self._api_call("/api/logs?n=10")
        if "error" not in logs:
            sections.append(f"## آخر 10 خطوات\n```\n{logs.get('logs', '')}\n```")

        sugs = self._api_call("/api/suggestions")
        if "error" not in sugs:
            sug_text = "\n".join(f"• {s}" for s in sugs.get("suggestions", []))
            sections.append(f"## اقتراحات\n{sug_text}")

        return "# 📊 تقرير صانع الرجال\n\n" + "\n\n".join(sections)
