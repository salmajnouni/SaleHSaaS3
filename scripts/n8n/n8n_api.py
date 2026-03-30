"""
n8n Workflow API - Simple Interface
متاح لجميع Python scripts والـ agents

Usage:
    from scripts.n8n.n8n_api import trigger_webhook, CouncilWorkflow
    
    # استخدام webhook مباشرة
    result = trigger_webhook("council-intake", {"topic": "..."})
    
    # أو استخدم Council helper
    result = CouncilWorkflow.submit_request(...)
"""

import os
import json
import requests
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

# Load environment
env_file = Path(__file__).parent.parent.parent / ".env"
n8n_url = "http://localhost:5678"

if env_file.exists():
    with open(env_file) as f:
        for line in f:
            if "=" in line and not line.startswith("#"):
                key, value = line.strip().split("=", 1)
                if key == "N8N_URL":
                    n8n_url = value.strip('"').strip("'")

def trigger_webhook(path: str, data: Optional[Dict] = None, timeout: int = 30) -> Dict[str, Any]:
    """
    Trigger n8n webhook
    
    Args:
        path: Webhook path (e.g., "council-intake")
        data: Payload to send
        timeout: Request timeout in seconds
        
    Returns:
        Response dictionary
        
    Example:
        result = trigger_webhook("council-intake", {
            "topic": "Legal review",
            "study_type": "legal",
            "requested_by": "أحمد"
        })
    """
    if data is None:
        data = {}
    
    webhook_url = f"{n8n_url}/webhook/{path}"
    data["_timestamp"] = datetime.now().isoformat()
    
    try:
        response = requests.post(
            webhook_url,
            json=data,
            timeout=timeout
        )
        
        return {
            "success": response.status_code < 400,
            "path": path,
            "status_code": response.status_code,
            "response": response.json() if response.text else response.text
        }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "path": path,
            "error": str(e),
            "url": webhook_url
        }


class CouncilWorkflow:
    """Helper class for Advisory Council workflow"""
    
    # Webhook path for council requests
    WEBHOOK_PATH = "council-intake"
    
    @classmethod
    def submit_request(
        cls,
        topic: str,
        study_type: str,
        requester: str,
        source: str = "api",
        priority: str = "normal"
    ) -> Dict[str, Any]:
        """
        Submit a council study request
        
        Args:
            topic: Topic for study
            study_type: Type (legal, financial, technical, cyber)
            requester: Requester name
            source: Source (api, dashboard, script, etc)
            priority: Priority (low, normal, high)
            
        Returns:
            Webhook response
            
        Example:
            result = CouncilWorkflow.submit_request(
                topic="Should we implement new security policy?",
                study_type="cyber",
                requester="صالح",
                priority="high"
            )
        """
        data = {
            "topic": topic,
            "study_type": study_type,
            "requested_by": requester,
            "source": source,
            "priority": priority
        }
        
        return trigger_webhook(cls.WEBHOOK_PATH, data)


def check_n8n():
    """Check if n8n is running"""
    try:
        response = requests.get(f"{n8n_url}/", timeout=5)
        return {"healthy": response.status_code < 500, "url": n8n_url}
    except Exception as e:
        return {"healthy": False, "error": str(e), "url": n8n_url}


if __name__ == "__main__":
    print(f"n8n Public API loaded")
    print(f"n8n URL: {n8n_url}")
    print(f"Status: {check_n8n()}")

