#!/usr/bin/env python3
"""
n8n Workflow Builder - MCP Tool
Allows the AI model to create, update, run, and manage n8n workflows via API.
"""

import json
import os
import sys
import requests
from typing import Any

N8N_BASE_URL = os.getenv("N8N_BASE_URL", "http://localhost:5678")
N8N_API_KEY  = os.getenv("N8N_API_KEY", "salehsaas-n8n-api-key")

HEADERS = {
    "X-N8N-API-KEY": N8N_API_KEY,
    "Content-Type": "application/json",
    "Accept": "application/json",
}

# ─── MCP Protocol Helpers ────────────────────────────────────────────────────

def send(obj: dict):
    sys.stdout.write(json.dumps(obj) + "\n")
    sys.stdout.flush()

def error_response(req_id, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32000, "message": message}}

def ok_response(req_id, content: str) -> dict:
    return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": content}]}}

# ─── n8n API Helpers ─────────────────────────────────────────────────────────

def n8n_get(path: str):
    r = requests.get(f"{N8N_BASE_URL}/api/v1{path}", headers=HEADERS, timeout=15)
    r.raise_for_status()
    return r.json()

def n8n_post(path: str, body: dict):
    r = requests.post(f"{N8N_BASE_URL}/api/v1{path}", headers=HEADERS, json=body, timeout=15)
    r.raise_for_status()
    return r.json()

def n8n_patch(path: str, body: dict):
    r = requests.patch(f"{N8N_BASE_URL}/api/v1{path}", headers=HEADERS, json=body, timeout=15)
    r.raise_for_status()
    return r.json()

def n8n_delete(path: str):
    r = requests.delete(f"{N8N_BASE_URL}/api/v1{path}", headers=HEADERS, timeout=15)
    r.raise_for_status()
    return r.json() if r.content else {"status": "deleted"}

# ─── Tool Implementations ─────────────────────────────────────────────────────

def list_workflows() -> str:
    """List all workflows with their id, name, and active status."""
    data = n8n_get("/workflows")
    workflows = data.get("data", data) if isinstance(data, dict) else data
    if not workflows:
        return "No workflows found."
    lines = ["ID | Active | Name"]
    lines.append("-" * 50)
    for w in workflows:
        lines.append(f"{w['id']} | {'✅' if w.get('active') else '❌'} | {w['name']}")
    return "\n".join(lines)


def get_workflow(workflow_id: str) -> str:
    """Get full details of a workflow by ID."""
    data = n8n_get(f"/workflows/{workflow_id}")
    return json.dumps(data, indent=2, ensure_ascii=False)


def create_workflow(name: str, nodes: list, connections: dict, active: bool = False) -> str:
    """
    Create a new workflow.
    nodes: list of n8n node objects
    connections: n8n connections dict
    """
    body = {
        "name": name,
        "nodes": nodes,
        "connections": connections,
        "settings": {"executionOrder": "v1"},
        "active": active,
    }
    result = n8n_post("/workflows", body)
    wf_id = result.get("id", "unknown")
    return f"Workflow created successfully. ID: {wf_id}, Name: {name}"


def update_workflow(workflow_id: str, name: str = None, nodes: list = None,
                    connections: dict = None, active: bool = None) -> str:
    """Update an existing workflow by ID."""
    body = {}
    if name is not None:
        body["name"] = name
    if nodes is not None:
        body["nodes"] = nodes
    if connections is not None:
        body["connections"] = connections
    if active is not None:
        body["active"] = active
    result = n8n_patch(f"/workflows/{workflow_id}", body)
    return f"Workflow {workflow_id} updated successfully."


def activate_workflow(workflow_id: str) -> str:
    """Activate a workflow so it responds to triggers."""
    n8n_patch(f"/workflows/{workflow_id}/activate", {})
    return f"Workflow {workflow_id} activated."


def deactivate_workflow(workflow_id: str) -> str:
    """Deactivate a workflow."""
    n8n_patch(f"/workflows/{workflow_id}/deactivate", {})
    return f"Workflow {workflow_id} deactivated."


def execute_workflow(workflow_id: str, data: dict = None) -> str:
    """Manually trigger a workflow execution."""
    body = {"workflowData": {"id": workflow_id}}
    if data:
        body["inputData"] = data
    result = n8n_post(f"/workflows/{workflow_id}/run", body)
    exec_id = result.get("data", {}).get("executionId", result.get("executionId", "unknown"))
    return f"Workflow execution started. Execution ID: {exec_id}"


def get_execution(execution_id: str) -> str:
    """Get the result of a workflow execution."""
    data = n8n_get(f"/executions/{execution_id}")
    status = data.get("status", "unknown")
    finished = data.get("finished", False)
    return f"Execution {execution_id}: status={status}, finished={finished}\n\n{json.dumps(data, indent=2, ensure_ascii=False)}"


def list_executions(workflow_id: str = None, limit: int = 10) -> str:
    """List recent executions, optionally filtered by workflow."""
    path = f"/executions?limit={limit}"
    if workflow_id:
        path += f"&workflowId={workflow_id}"
    data = n8n_get(path)
    executions = data.get("data", data) if isinstance(data, dict) else data
    if not executions:
        return "No executions found."
    lines = ["ID | Status | Workflow | Started"]
    lines.append("-" * 60)
    for e in executions:
        lines.append(f"{e.get('id')} | {e.get('status')} | {e.get('workflowId')} | {e.get('startedAt', '')[:19]}")
    return "\n".join(lines)


def delete_workflow(workflow_id: str) -> str:
    """Delete a workflow by ID."""
    n8n_delete(f"/workflows/{workflow_id}")
    return f"Workflow {workflow_id} deleted."


# ─── MCP Dispatch ─────────────────────────────────────────────────────────────

TOOLS = {
    "list_workflows": {
        "description": "List all n8n workflows with their ID, name, and active status.",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    "get_workflow": {
        "description": "Get the full JSON definition of a workflow by its ID.",
        "inputSchema": {
            "type": "object",
            "properties": {"workflow_id": {"type": "string", "description": "Workflow ID"}},
            "required": ["workflow_id"],
        },
    },
    "create_workflow": {
        "description": "Create a new n8n workflow with nodes and connections.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Workflow name"},
                "nodes": {"type": "array", "description": "List of n8n node objects"},
                "connections": {"type": "object", "description": "n8n connections object"},
                "active": {"type": "boolean", "description": "Activate immediately? Default false"},
            },
            "required": ["name", "nodes", "connections"],
        },
    },
    "update_workflow": {
        "description": "Update an existing workflow by ID.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "workflow_id": {"type": "string"},
                "name": {"type": "string"},
                "nodes": {"type": "array"},
                "connections": {"type": "object"},
                "active": {"type": "boolean"},
            },
            "required": ["workflow_id"],
        },
    },
    "activate_workflow": {
        "description": "Activate a workflow so it listens to triggers.",
        "inputSchema": {
            "type": "object",
            "properties": {"workflow_id": {"type": "string"}},
            "required": ["workflow_id"],
        },
    },
    "deactivate_workflow": {
        "description": "Deactivate a workflow.",
        "inputSchema": {
            "type": "object",
            "properties": {"workflow_id": {"type": "string"}},
            "required": ["workflow_id"],
        },
    },
    "execute_workflow": {
        "description": "Manually trigger a workflow execution.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "workflow_id": {"type": "string"},
                "data": {"type": "object", "description": "Optional input data"},
            },
            "required": ["workflow_id"],
        },
    },
    "get_execution": {
        "description": "Get the result and status of a workflow execution by execution ID.",
        "inputSchema": {
            "type": "object",
            "properties": {"execution_id": {"type": "string"}},
            "required": ["execution_id"],
        },
    },
    "list_executions": {
        "description": "List recent workflow executions.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "workflow_id": {"type": "string", "description": "Filter by workflow ID (optional)"},
                "limit": {"type": "integer", "description": "Max results (default 10)"},
            },
            "required": [],
        },
    },
    "delete_workflow": {
        "description": "Delete a workflow by ID.",
        "inputSchema": {
            "type": "object",
            "properties": {"workflow_id": {"type": "string"}},
            "required": ["workflow_id"],
        },
    },
}

TOOL_FUNCS = {
    "list_workflows": lambda a: list_workflows(),
    "get_workflow": lambda a: get_workflow(a["workflow_id"]),
    "create_workflow": lambda a: create_workflow(a["name"], a["nodes"], a["connections"], a.get("active", False)),
    "update_workflow": lambda a: update_workflow(a["workflow_id"], a.get("name"), a.get("nodes"), a.get("connections"), a.get("active")),
    "activate_workflow": lambda a: activate_workflow(a["workflow_id"]),
    "deactivate_workflow": lambda a: deactivate_workflow(a["workflow_id"]),
    "execute_workflow": lambda a: execute_workflow(a["workflow_id"], a.get("data")),
    "get_execution": lambda a: get_execution(a["execution_id"]),
    "list_executions": lambda a: list_executions(a.get("workflow_id"), a.get("limit", 10)),
    "delete_workflow": lambda a: delete_workflow(a["workflow_id"]),
}


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue

        req_id = req.get("id")
        method = req.get("method", "")
        params = req.get("params", {})

        if method == "initialize":
            send({"jsonrpc": "2.0", "id": req_id, "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "n8n_builder", "version": "1.0.0"},
            }})

        elif method == "tools/list":
            tools_list = [{"name": k, "description": v["description"], "inputSchema": v["inputSchema"]}
                          for k, v in TOOLS.items()]
            send({"jsonrpc": "2.0", "id": req_id, "result": {"tools": tools_list}})

        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            if tool_name not in TOOL_FUNCS:
                send(error_response(req_id, f"Unknown tool: {tool_name}"))
                continue
            try:
                result_text = TOOL_FUNCS[tool_name](arguments)
                send(ok_response(req_id, result_text))
            except Exception as e:
                send(error_response(req_id, str(e)))

        elif method == "notifications/initialized":
            pass  # no response needed

        else:
            send({"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Method not found: {method}"}})


if __name__ == "__main__":
    main()
