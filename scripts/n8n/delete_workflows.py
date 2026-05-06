#!/usr/bin/env python3
"""
Delete unused and duplicate n8n workflows directly via psql
"""
import re
import subprocess

WORKFLOWS_TO_DELETE = [
    ("bYX7gyGyLYyWALQX", "Daily Email Report"),
    ("5xcWk4ecFI5lB8CZ", "Monitor Ministry of Commerce Website"),
    ("8OXJ3tEWjbi5vo0R", "My workflow"),
    ("VFNWN9kBfiS2Pj1s", "My workflow 2"),
    ("tWwHzQ8lsonOjqMM", "Open WebUI Test Agent"),
    ("Hy039PugRqTDDYbd", "Saudi Legal Scraper v2 [DUPLICATE - INACTIVE]"),
    ("249rwTc6zPcAs6yV", "Saudi Legal Scraper v2 [DUPLICATE - INACTIVE]"),
    ("8wsRLM4Rc0unTZLw", "استرجاع العنوان من API"),
    ("GMCUQ7WzOokZ9p58", "مثال سير عمل"),
    ("RpxWBHtRBl544TT6", "مثال سير عمل"),
    ("6dQHQ9ZsNpDlLEC9", "مساء الخير"),
]

WORKFLOWS_TO_KEEP = {
    "DxOu1hA7f9UEyZZ4": "Daily Backup - نسخ احتياطي يومي [ACTIVE]",
    "0iSWoHwHgl6DLriB": "Saudi Laws Sync - سحب وتحديث القوانين السعودية [SYNCED]",
    "HuuRe6ooTrbh5rJF": "Saudi Legal Scraper v2 - سحب القوانين من المصادر الرسمية [ACTIVE]",
    "UaJRWaaHtVldwoUl": "📰 أم القرى - مراقب الأنظمة الجديدة [ACTIVE]",
    "YPVhIxCVGsgPpNDM": "🔄 Saudi Laws Auto-Update - التحديث الذاتي للقوانين [ACTIVE]",
    "heyEz7Msi6myluLX": "🤖 مساعد القوانين السعودية - Saudi Laws Assistant [ACTIVE]",
    "1iMpXFAh3CQbRo1f": "🧠 هضم المعرفة التلقائي - SaleH SaaS [SYNCED]",
}

VALID_WORKFLOW_ID_RE = re.compile(r'^[a-zA-Z0-9]{8,30}$')

RELATED_TABLES = [
    "workflow_statistics",
    "workflow_history",
    "workflow_publish_history",
    "workflow_dependency",
    "workflow_builder_session",
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
    if fetch:
        return result.stdout.strip() if result.returncode == 0 else None
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
    print("n8n WORKFLOW CLEANUP TOOL - Delete Unused & Duplicate Workflows")
    print("=" * 70 + "\n")

    print("[*] WORKFLOWS TO KEEP (Safe - will not be deleted):\n")
    for wf_id, description in WORKFLOWS_TO_KEEP.items():
        print(f"    [OK] {wf_id}")
        print(f"         {description}\n")

    print("[*] WORKFLOWS TO DELETE (Unused/Experimental/Duplicates):\n")
    for wf_id, description in WORKFLOWS_TO_DELETE:
        print(f"    [DEL] {wf_id}")
        print(f"          {description}\n")

    print("=" * 70)
    print(f"\n[!] About to delete {len(WORKFLOWS_TO_DELETE)} workflows")
    print("[!] This action CANNOT be undone")
    print("[!] Make sure to backup if needed\n")

    user_input = input("[?] Proceed with deletion? Type 'yes' to confirm: ").strip().lower()

    if user_input != "yes":
        print("\n[-] Deletion cancelled. Exiting.\n")
        return

    print("\n[*] Starting deletion process...\n")

    deleted_count = 0
    failed_count = 0

    for wf_id, description in WORKFLOWS_TO_DELETE:
        print(f"[*] Deleting: {description}")
        print(f"    ID: {wf_id}")

        if delete_workflow(wf_id):
            print(f"    [+] Successfully deleted\n")
            deleted_count += 1
        else:
            print(f"    [-] Failed to delete\n")
            failed_count += 1

    print("=" * 70)
    print(f"[+] CLEANUP COMPLETE")
    print(f"    Deleted: {deleted_count}/{len(WORKFLOWS_TO_DELETE)}")
    print(f"    Failed: {failed_count}")
    print(f"    Remaining safe workflows: {len(WORKFLOWS_TO_KEEP)}")
    print("=" * 70 + "\n")

    if deleted_count > 0:
        print("[*] Verifying deletion...")
        remaining = run_sql("SELECT COUNT(*) FROM workflow_entity;", fetch=True)
        if remaining is not None:
            print(f"[+] Total workflows remaining in database: {remaining}\n")

        print("[!] Next steps:")
        print("    1. Restart n8n container to reload workflows")
        print("    2. Verify in n8n UI that unwanted workflows are gone\n")


if __name__ == "__main__":
    main()