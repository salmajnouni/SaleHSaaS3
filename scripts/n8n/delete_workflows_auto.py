#!/usr/bin/env python3
"""
Delete unused and duplicate n8n workflows - Non-interactive version
"""
import re
import subprocess
import sys

WORKFLOWS_TO_DELETE = [
    "bYX7gyGyLYyWALQX",
    "5xcWk4ecFI5lB8CZ",
    "8OXJ3tEWjbi5vo0R",
    "VFNWN9kBfiS2Pj1s",
    "tWwHzQ8lsonOjqMM",
    "Hy039PugRqTDDYbd",
    "249rwTc6zPcAs6yV",
    "8wsRLM4Rc0unTZLw",
    "GMCUQ7WzOokZ9p58",
    "RpxWBHtRBl544TT6",
    "6dQHQ9ZsNpDlLEC9",
]

VALID_WORKFLOW_ID_RE = re.compile(r'^[a-zA-Z0-9]{8,30}$')

RELATED_TABLES = [
    "workflow_statistics",
    "workflow_history",
    "workflow_publish_history",
    "workflow_dependency",
    "workflow_builder_session",
    "workflows_tags",
    "workflow_published_version",
]


def validate_workflow_id(workflow_id: str) -> None:
    if not VALID_WORKFLOW_ID_RE.match(workflow_id):
        raise ValueError(f"Invalid workflow ID format: {workflow_id!r}")


def run_sql(query: str, fetch: bool = False):
    cmd = [
        "docker", "exec", "salehsaas_postgres",
        "psql", "-U", "salehsaas", "-d", "salehsaas", "-t",
        "-c", query,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    if result.returncode != 0:
        print(f"  [ERR] SQL error: {result.stderr.strip()}")
    if fetch:
        return result.stdout.strip()
    return result.returncode == 0


def delete_workflow(workflow_id: str) -> bool:
    try:
        validate_workflow_id(workflow_id)
    except ValueError as e:
        print(f"  [ERR] {e}")
        return False

    if not run_sql(f"DELETE FROM workflow_entity WHERE id = '{workflow_id}';"):
        return False

    for table in RELATED_TABLES:
        run_sql(
            f"DELETE FROM {table} WHERE "
            f"\"workflowId\" = '{workflow_id}' OR workflow_id = '{workflow_id}';"
        )

    return True


def main():
    print("\n" + "=" * 70)
    print("n8n WORKFLOW CLEANUP - Deleting Workflows from Database")
    print("=" * 70 + "\n")

    deleted_count = 0
    failed_count = 0

    for wf_id in WORKFLOWS_TO_DELETE:
        print(f"[*] Deleting workflow: {wf_id}")

        if delete_workflow(wf_id):
            print(f"    [+] Deleted successfully\n")
            deleted_count += 1
        else:
            print(f"    [-] Failed\n")
            failed_count += 1

    print("=" * 70)
    print(f"[+] DELETION COMPLETE")
    print(f"    Deleted: {deleted_count}/{len(WORKFLOWS_TO_DELETE)}")
    print(f"    Failed: {failed_count}")
    print("=" * 70 + "\n")

    remaining = run_sql("SELECT COUNT(*) FROM workflow_entity;", fetch=True)
    if remaining is not None:
        print(f"[*] Total workflows remaining: {remaining}")
        print(f"[*] Next step: Restart n8n container for changes to take effect")
        print(f"    Command: docker restart salehsaas_n8n\n")


if __name__ == "__main__":
    main()