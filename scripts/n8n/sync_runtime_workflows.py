#!/usr/bin/env python3
"""Sync selected repository workflow JSON files into the live n8n runtime.

Behavior:
- Match existing workflows by exact name.
- If duplicates exist, prefer the active one; otherwise prefer the most recently updated.
- Dry-run by default. Use --apply to push changes.
"""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_N8N_URL = os.environ.get("N8N_URL", "http://localhost:5678")
DEFAULT_API_KEY = os.environ.get(
    "N8N_API_KEY",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJlOTJhNTYwYS1iOTBkLTRiY2YtODljNy0zODIyMWRiYTQ4YmQiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwianRpIjoiNjMxZDAzM2YtNzc1MC00YzdlLWE1OGMtYWMyN2JkNDA4ODdiIiwiaWF0IjoxNzc0NjIwOTEyLCJleHAiOjE4MDYxNTYwMDB9.hEVgXGIjcJtbYg8xxLV_eFNN3Q8SxeSwng_GeE3yYP8",
)

WORKFLOW_FILES = [
    {
        "path": "n8n/workflows/knowledge_ingestion.json",
        "activate_on_create": False,
    },
    {
        "path": "n8n/workflows/saudi_laws_sync.json",
        "activate_on_create": False,
    },
    {
        "path": "n8n/workflows/saudi_laws_chat.json",
        "activate_on_create": True,
    },
    {
        "path": "n8n_workflows/saudi_laws_auto_update.json",
        "activate_on_create": True,
    },
    {
        "path": "n8n_workflows/uqn_gazette_monitor.json",
        "activate_on_create": True,
    },
    {
        "path": "n8n_workflows/saudi_legal_scraper.json",
        "activate_on_create": True,
    },
]


@dataclass
class TargetWorkflow:
    workflow_id: str
    name: str
    active: bool
    updated_at: str


def n8n_headers(api_key: str) -> dict[str, str]:
    return {
        "X-N8N-API-KEY": api_key,
        "Content-Type": "application/json",
    }


def fetch_workflows(n8n_url: str, api_key: str) -> list[dict[str, Any]]:
    resp = requests.get(f"{n8n_url}/api/v1/workflows", headers=n8n_headers(api_key), timeout=30)
    resp.raise_for_status()
    return resp.json().get("data", [])


def choose_existing(workflows: list[dict[str, Any]], name: str) -> tuple[TargetWorkflow | None, list[TargetWorkflow]]:
    matches = [
        TargetWorkflow(
            workflow_id=str(w["id"]),
            name=str(w.get("name", "")),
            active=bool(w.get("active", False)),
            updated_at=str(w.get("updatedAt", "")),
        )
        for w in workflows
        if str(w.get("name", "")) == name
    ]
    if not matches:
        return None, []

    active_matches = [m for m in matches if m.active]
    if active_matches:
        chosen = sorted(active_matches, key=lambda x: x.updated_at, reverse=True)[0]
    else:
        chosen = sorted(matches, key=lambda x: x.updated_at, reverse=True)[0]
    return chosen, matches


def build_payload(workflow_json: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": workflow_json.get("name"),
        "nodes": workflow_json.get("nodes", []),
        "connections": workflow_json.get("connections", {}),
        "settings": workflow_json.get("settings", {}),
        "staticData": workflow_json.get("staticData"),
    }


def set_workflow_active(n8n_url: str, api_key: str, workflow_id: str, active: bool) -> None:
    endpoint = "activate" if active else "deactivate"
    resp = requests.post(
        f"{n8n_url}/api/v1/workflows/{workflow_id}/{endpoint}",
        headers=n8n_headers(api_key),
        timeout=20,
    )
    resp.raise_for_status()


def sync_one(
    n8n_url: str,
    api_key: str,
    workflows: list[dict[str, Any]],
    file_info: dict[str, Any],
    apply: bool,
) -> dict[str, Any]:
    rel_path = file_info["path"]
    activate_on_create = bool(file_info.get("activate_on_create", False))
    abs_path = ROOT / rel_path
    workflow_json = json.loads(abs_path.read_text(encoding="utf-8"))
    name = str(workflow_json.get("name", "")).strip()

    chosen, duplicates = choose_existing(workflows, name)
    payload = build_payload(workflow_json)

    result: dict[str, Any] = {
        "file": rel_path,
        "name": name,
        "existing_duplicates": [
            {
                "id": d.workflow_id,
                "active": d.active,
                "updated_at": d.updated_at,
            }
            for d in duplicates
        ],
    }

    if chosen:
        result["action"] = "update"
        result["target_id"] = chosen.workflow_id
        result["target_active_before"] = chosen.active
    else:
        result["action"] = "create"
        result["target_active_before"] = False

    if not apply:
        result["mode"] = "dry_run"
        return result

    try:
        if chosen:
            resp = requests.put(
                f"{n8n_url}/api/v1/workflows/{chosen.workflow_id}",
                headers=n8n_headers(api_key),
                json=payload,
                timeout=60,
            )
            resp.raise_for_status()
            workflow_id = chosen.workflow_id
            target_should_be_active = chosen.active
        else:
            resp = requests.post(
                f"{n8n_url}/api/v1/workflows",
                headers=n8n_headers(api_key),
                json=payload,
                timeout=60,
            )
            resp.raise_for_status()
            workflow_id = str(resp.json().get("id"))
            result["target_id"] = workflow_id
            target_should_be_active = activate_on_create

        set_workflow_active(n8n_url, api_key, workflow_id, bool(target_should_be_active))

        result["mode"] = "apply"
        result["status"] = "ok"
        result["target_active_after"] = bool(target_should_be_active)
    except requests.HTTPError as exc:
        response = exc.response
        result["mode"] = "apply"
        result["status"] = "error"
        result["error_status_code"] = response.status_code if response is not None else None
        result["error_body"] = (response.text[:1200] if response is not None else str(exc))
    except Exception as exc:
        result["mode"] = "apply"
        result["status"] = "error"
        result["error_body"] = str(exc)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync selected repository workflows into live n8n")
    parser.add_argument("--n8n-url", default=DEFAULT_N8N_URL)
    parser.add_argument("--api-key", default=DEFAULT_API_KEY)
    parser.add_argument("--apply", action="store_true", help="Apply changes. Default is dry-run.")
    args = parser.parse_args()

    workflows = fetch_workflows(args.n8n_url, args.api_key)
    results = [
        sync_one(
            n8n_url=args.n8n_url,
            api_key=args.api_key,
            workflows=workflows,
            file_info=file_info,
            apply=args.apply,
        )
        for file_info in WORKFLOW_FILES
    ]

    print(json.dumps({"mode": "apply" if args.apply else "dry_run", "results": results}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
