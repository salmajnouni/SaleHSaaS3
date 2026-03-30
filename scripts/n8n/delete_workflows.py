#!/usr/bin/env python3
"""
Delete unused and duplicate n8n workflows directly via psql
"""
import subprocess
import json

# List of workflows to DELETE (by ID)
# Criteria: Inactive + either experimental/duplicate or not in the main project
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

# Workflows to KEEP
WORKFLOWS_TO_KEEP = {
    "DxOu1hA7f9UEyZZ4": "Daily Backup - نسخ احتياطي يومي [ACTIVE]",
    "0iSWoHwHgl6DLriB": "Saudi Laws Sync - سحب وتحديث القوانين السعودية [SYNCED]",
    "HuuRe6ooTrbh5rJF": "Saudi Legal Scraper v2 - سحب القوانين من المصادر الرسمية [ACTIVE]",
    "UaJRWaaHtVldwoUl": "📰 أم القرى - مراقب الأنظمة الجديدة [ACTIVE]",
    "YPVhIxCVGsgPpNDM": "🔄 Saudi Laws Auto-Update - التحديث الذاتي للقوانين [ACTIVE]",
    "heyEz7Msi6myluLX": "🤖 مساعد القوانين السعودية - Saudi Laws Assistant [ACTIVE]",
    "1iMpXFAh3CQbRo1f": "🧠 هضم المعرفة التلقائي - SaleH SaaS [SYNCED]",
}

def delete_workflow(workflow_id: str) -> bool:
    """Delete a workflow from postgres"""
    try:
        # Simple approach: use 'public.api_user'. But we need to use n8n's API
        # For safety, we'll use docker exec to call psql and delete
        cmd = [
            "docker", "exec", "salehsaas_postgres",
            "psql", "-U", "salehsaas", "-d", "salehsaas",
            "-c", f"DELETE FROM workflow_entity WHERE id = '{workflow_id}';"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            # Also need to clean up related tables
            # Delete from workflow_statistics, workflow_history, etc.
            related_tables = [
                "workflow_statistics",
                "workflow_history",
                "workflow_publish_history",
                "workflow_dependency",
                "workflow_builder_session"
            ]
            
            for table in related_tables:
                cleanup_cmd = [
                    "docker", "exec", "salehsaas_postgres",
                    "psql", "-U", "salehsaas", "-d", "salehsaas",
                    "-c", f"DELETE FROM {table} WHERE workflowId = '{workflow_id}' OR workflow_id = '{workflow_id}';"
                ]
                subprocess.run(cleanup_cmd, capture_output=True, timeout=10)
            
            return True
        else:
            print(f"  Error: {result.stderr}")
            return False
    
    except Exception as e:
        print(f"  Exception: {e}")
        return False

def main():
    print("\n" + "="*70)
    print("n8n WORKFLOW CLEANUP TOOL - Delete Unused & Duplicate Workflows")
    print("="*70 + "\n")
    
    # Show what we're keeping
    print("[*] WORKFLOWS TO KEEP (Safe - will not be deleted):\n")
    for wf_id, description in WORKFLOWS_TO_KEEP.items():
        print(f"    ✓ {wf_id}")
        print(f"      {description}\n")
    
    # Show what we're deleting
    print("[*] WORKFLOWS TO DELETE (Unused/Experimental/Duplicates):\n")
    for wf_id, description in WORKFLOWS_TO_DELETE:
        print(f"    ✗ {wf_id}")
        print(f"      {description}\n")
    
    # Confirm
    print("="*70)
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
    
    # Summary
    print("="*70)
    print(f"[+] CLEANUP COMPLETE")
    print(f"    Deleted: {deleted_count}/{len(WORKFLOWS_TO_DELETE)}")
    print(f"    Failed: {failed_count}")
    print(f"    Remaining safe workflows: {len(WORKFLOWS_TO_KEEP)}")
    print("="*70 + "\n")
    
    if deleted_count > 0:
        print("[*] Verifying deletion...")
        verify_cmd = [
            "docker", "exec", "salehsaas_postgres",
            "psql", "-U", "salehsaas", "-d", "salehsaas", "-t",
            "-c", "SELECT COUNT(*) FROM workflow_entity;"
        ]
        
        result = subprocess.run(verify_cmd, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            remaining = result.stdout.strip()
            print(f"[+] Total workflows remaining in database: {remaining}\n")
        
        print("[!] Next steps:")
        print("    1. Restart n8n container to reload workflows")
        print("    2. Verify in n8n UI that unwanted workflows are gone\n")

if __name__ == "__main__":
    main()
