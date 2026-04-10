#!/usr/bin/env python3
"""
n8n Command Line Interface
متاح لجميع الـ agents والـ models

Usage:
    python n8n_cli.py list-workflows
    python n8n_cli.py run-workflow --id CwCounclWbhk001 --data '{"topic":"..."}'
    python n8n_cli.py get-execution --id abc123
    python n8n_cli.py create-webhook --workflow-id xyz --path council-intake
    python n8n_cli.py trigger-webhook --path council-intake --data '{...}'
"""

import json
import sys
import os
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import re

# Load environment
env_file = Path(__file__).parent.parent.parent / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            if "=" in line and not line.startswith("#"):
                key, value = line.strip().split("=", 1)
                os.environ.setdefault(key, value.strip('"').strip("'"))

# Configuration
N8N_URL = os.getenv("N8N_URL", "http://localhost:5678")
N8N_ADMIN_KEY = os.getenv("N8N_ADMIN_KEY", "")
COUNCIL_WEBHOOK_URL = os.getenv("COUNCIL_WEBHOOK_URL", f"{N8N_URL}/webhook/council-intake")

class N8nCLI:
    """n8n Command Line Interface"""
    
    def __init__(self):
        self.n8n_url = N8N_URL
        self.admin_key = N8N_ADMIN_KEY
        
    def _run_docker_cmd(self, cmd: str) -> Dict[str, Any]:
        """Execute command inside n8n container (safe: no shell=True)"""
        # Split into list to avoid shell injection; prepend docker exec
        cmd_list = ["docker", "exec", "salehsaas_n8n"] + cmd.split()
        try:
            result = subprocess.run(
                cmd_list, 
                shell=False, 
                capture_output=True, 
                text=True,
                timeout=30
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "code": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Command timeout"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def list_workflows(self, active_only: bool = False) -> Dict[str, Any]:
        """List all workflows"""
        print(f"📋 Listing workflows from {self.n8n_url}...")
        
        cmd = 'n8n list:workflows'
        if active_only:
            cmd += ' | grep -i "active\\|true"'
        
        result = self._run_docker_cmd(cmd)
        
        if result["success"]:
            output = result["stdout"]
            # Parse workflow list
            workflows = self._parse_workflow_list(output)
            return {
                "success": True,
                "count": len(workflows),
                "workflows": workflows,
                "raw": output
            }
        else:
            return {
                "success": False,
                "error": result["stderr"] or "Failed to list workflows"
            }
    
    def _parse_workflow_list(self, output: str) -> List[Dict]:
        """Parse workflow list output"""
        workflows = []
        
        for line in output.split("\n"):
            if line.strip() and not line.startswith("ID") and not line.startswith("---"):
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 3:
                    workflows.append({
                        "id": parts[0],
                        "name": parts[1],
                        "status": parts[2] if len(parts) > 2 else "unknown"
                    })
        
        return workflows
    
    @staticmethod
    def _validate_id(value: str) -> str:
        """Validate workflow/execution IDs to prevent injection."""
        clean = str(value).strip()
        if not re.match(r'^[A-Za-z0-9_-]{1,64}$', clean):
            raise ValueError(f"Invalid ID: {clean[:30]}")
        return clean

    def get_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Get workflow details"""
        workflow_id = self._validate_id(workflow_id)
        print(f"🔍 Getting workflow: {workflow_id}")
        
        cmd = f'n8n export:workflow --id {workflow_id}'
        result = self._run_docker_cmd(cmd)
        
        if result["success"]:
            try:
                workflow_data = json.loads(result["stdout"])
                return {
                    "success": True,
                    "id": workflow_id,
                    "data": workflow_data
                }
            except json.JSONDecodeError:
                return {
                    "success": False,
                    "error": "Invalid JSON response"
                }
        else:
            return {
                "success": False,
                "error": result["stderr"]
            }
    
    def activate_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Activate a workflow"""
        print(f"▶️  Activating workflow: {workflow_id}")
        
        cmd = f'n8n update:workflow --id {workflow_id} --active=true'
        result = self._run_docker_cmd(cmd)
        
        return {
            "success": result["success"],
            "workflow_id": workflow_id,
            "message": result["stdout"] if result["success"] else result["stderr"]
        }
    
    def deactivate_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Deactivate a workflow"""
        print(f"⏸️  Deactivating workflow: {workflow_id}")
        
        cmd = f'n8n update:workflow --id {workflow_id} --active=false'
        result = self._run_docker_cmd(cmd)
        
        return {
            "success": result["success"],
            "workflow_id": workflow_id,
            "message": result["stdout"] if result["success"] else result["stderr"]
        }
    
    def run_workflow(self, workflow_id: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Trigger workflow execution"""
        print(f"🚀 Running workflow: {workflow_id}")
        
        if data is None:
            data = {}
        
        # Use curl directly in container
        json_data = json.dumps(data)
        cmd = f'curl -X POST {self.n8n_url}/rest/workflows/{workflow_id}/execute -H "Content-Type: application/json" -d \'{json_data}\''
        
        result = self._run_docker_cmd(cmd)
        
        if result["success"]:
            try:
                exec_data = json.loads(result["stdout"])
                return {
                    "success": True,
                    "workflow_id": workflow_id,
                    "execution": exec_data
                }
            except:
                return {
                    "success": False,
                    "error": "Invalid execution response",
                    "raw": result["stdout"]
                }
        else:
            return {
                "success": False,
                "workflow_id": workflow_id,
                "error": result["stderr"]
            }
    
    def trigger_webhook(self, path: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Trigger webhook directly"""
        print(f"🔗 Triggering webhook: {path}")
        
        if data is None:
            data = {}
        
        webhook_url = f"{self.n8n_url}/webhook/{path}"
        json_data = json.dumps(data)
        cmd = f'curl -X POST {webhook_url} -H "Content-Type: application/json" -d \'{json_data}\''
        
        result = self._run_docker_cmd(cmd)
        
        if result["success"]:
            try:
                response = json.loads(result["stdout"])
                return {
                    "success": True,
                    "path": path,
                    "response": response
                }
            except:
                return {
                    "success": False,
                    "error": "Invalid webhook response",
                    "raw": result["stdout"]
                }
        else:
            return {
                "success": False,
                "path": path,
                "error": result["stderr"]
            }
    
    def council_request(self, topic: str, study_type: str, requester: str, source: str = "cli") -> Dict[str, Any]:
        """Submit a council study request (convenience function)"""
        print(f"📝 Submitting council request: {topic}")
        
        data = {
            "topic": topic,
            "study_type": study_type,
            "requested_by": requester,
            "source": source,
            "timestamp": datetime.now().isoformat()
        }
        
        return self.trigger_webhook("council-intake", data)
    
    def get_logs(self, lines: int = 50) -> Dict[str, Any]:
        """Get n8n container logs"""
        print(f"📄 Getting last {lines} lines of n8n logs...")
        
        cmd = f'docker logs salehsaas_n8n --tail {lines}'
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        return {
            "success": result.returncode == 0,
            "logs": result.stdout
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Check n8n health"""
        print("🏥 Checking n8n health...")
        
        cmd = f'curl -s {self.n8n_url}/rest/health'
        result = self._run_docker_cmd(cmd)
        
        if result["success"]:
            try:
                health = json.loads(result["stdout"])
                return {
                    "success": True,
                    "health": health
                }
            except:
                return {
                    "success": True,
                    "message": "n8n is responding",
                    "raw": result["stdout"]
                }
        else:
            return {
                "success": False,
                "error": result["stderr"]
            }


def main():
    parser = argparse.ArgumentParser(
        description="n8n Command Line Interface for all models and agents"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # List workflows
    subparsers.add_parser("list-workflows", help="List all workflows")
    
    # Get workflow details
    get_wf = subparsers.add_parser("get-workflow", help="Get workflow details")
    get_wf.add_argument("--id", required=True, help="Workflow ID")
    
    # Activate workflow
    activate_wf = subparsers.add_parser("activate", help="Activate a workflow")
    activate_wf.add_argument("--id", required=True, help="Workflow ID")
    
    # Deactivate workflow
    deactivate_wf = subparsers.add_parser("deactivate", help="Deactivate a workflow")
    deactivate_wf.add_argument("--id", required=True, help="Workflow ID")
    
    # Run workflow
    run_wf = subparsers.add_parser("run", help="Run a workflow")
    run_wf.add_argument("--id", required=True, help="Workflow ID")
    run_wf.add_argument("--data", default="{}", help="JSON input data")
    
    # Trigger webhook
    trigger_wh = subparsers.add_parser("webhook", help="Trigger a webhook")
    trigger_wh.add_argument("--path", required=True, help="Webhook path")
    trigger_wh.add_argument("--data", default="{}", help="JSON data")
    
    # Council request (convenience)
    council = subparsers.add_parser("council", help="Submit council request")
    council.add_argument("--topic", required=True, help="Topic for council study")
    council.add_argument("--type", required=True, help="Study type (legal/financial/technical/cyber)")
    council.add_argument("--requester", required=True, help="Requester name")
    
    # Logs
    subparsers.add_parser("logs", help="Get n8n logs")
    
    # Health
    subparsers.add_parser("health", help="Check n8n health")
    
    args = parser.parse_args()
    
    cli = N8nCLI()
    
    if not args.command:
        parser.print_help()
        return
    
    # Execute command
    if args.command == "list-workflows":
        result = cli.list_workflows()
    
    elif args.command == "get-workflow":
        result = cli.get_workflow(args.id)
    
    elif args.command == "activate":
        result = cli.activate_workflow(args.id)
    
    elif args.command == "deactivate":
        result = cli.deactivate_workflow(args.id)
    
    elif args.command == "run":
        data = json.loads(args.data)
        result = cli.run_workflow(args.id, data)
    
    elif args.command == "webhook":
        data = json.loads(args.data)
        result = cli.trigger_webhook(args.path, data)
    
    elif args.command == "council":
        result = cli.council_request(args.topic, args.type, args.requester)
    
    elif args.command == "logs":
        result = cli.get_logs()
    
    elif args.command == "health":
        result = cli.health_check()
    
    else:
        result = {"error": "Unknown command"}
    
    # Pretty print result
    print("\n" + "="*60)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print("="*60)
    
    return 0 if result.get("success", False) else 1


if __name__ == "__main__":
    sys.exit(main())
