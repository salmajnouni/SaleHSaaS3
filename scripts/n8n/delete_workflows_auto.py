#!/usr/bin/env python3
"""
Delete unused and duplicate n8n workflows - Non-interactive version
"""
import subprocess
import sys

# List of workflows to DELETE (by ID)
WORKFLOWS_TO_DELETE = [
    "bYX7gyGyLYyWALQX",  # Daily Email Report
    "5xcWk4ecFI5lB8CZ",  # Monitor Ministry of Commerce Website
    "8OXJ3tEWjbi5vo0R",  # My workflow
    "VFNWN9kBfiS2Pj1s",  # My workflow 2
    "tWwHzQ8lsonOjqMM",  # Open WebUI Test Agent
    "Hy039PugRqTDDYbd",  # Saudi Legal Scraper v2 (duplicate)
    "249rwTc6zPcAs6yV",  # Saudi Legal Scraper v2 (duplicate)
    "8wsRLM4Rc0unTZLw",  # استرجاع العنوان من API
    "GMCUQ7WzOokZ9p58",  # مثال سير عمل
    "RpxWBHtRBl544TT6",  # مثال سير عمل
    "6dQHQ9ZsNpDlLEC9",  # مساء الخير
]

def delete_workflow(workflow_id: str) -> bool:
    """Delete a workflow from postgres"""
    try:
        # Delete from workflow_entity first
        cmd = [
            "docker", "exec", "salehsaas_postgres",
            "psql", "-U", "salehsaas", "-d", "salehsaas",
            "-c", f"DELETE FROM workflow_entity WHERE id = '{workflow_id}';"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            # Clean up related tables
            related_tables = [
                "workflow_statistics",
                "workflow_history", 
                "workflow_publish_history",
                "workflow_dependency",
                "workflow_builder_session",
                "workflows_tags",
                "workflow_published_version"
            ]
            
            for table in related_tables:
                cleanup_cmd = [
                    "docker", "exec", "salehsaas_postgres",
                    "psql", "-U", "salehsaas", "-d", "salehsaas",
                    "-c", f"DELETE FROM {table} WHERE workflowId = '{workflow_id}' OR workflow_id = '{workflow_id}' OR \"workflowId\" = '{workflow_id}';"
                ]
                subprocess.run(cleanup_cmd, capture_output=True, timeout=10)
            
            return True
        return False
    
    except Exception as e:
        print(f"  Exception: {e}")
        return False

def main():
    print("\n" + "="*70)
    print("n8n WORKFLOW CLEANUP - Deleting Workflows from Database")
    print("="*70 + "\n")
    
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
    
    # Verify
    print("="*70)
    print(f"[+] DELETION COMPLETE")
    print(f"    Deleted: {deleted_count}/{len(WORKFLOWS_TO_DELETE)}")
    print(f"    Failed: {failed_count}")
    print("="*70 + "\n")
    
    # Check remaining count
    verify_cmd = [
        "docker", "exec", "salehsaas_postgres",
        "psql", "-U", "salehsaas", "-d", "salehsaas", "-t",
        "-c", "SELECT COUNT(*) FROM workflow_entity;"
    ]
    
    result = subprocess.run(verify_cmd, capture_output=True, text=True, timeout=10)
    if result.returncode == 0:
        remaining = result.stdout.strip()
        print(f"[*] Total workflows remaining: {remaining}")
        print(f"[*] Next step: Restart n8n container for changes to take effect")
        print(f"    Command: docker restart salehsaas_n8n\n")

if __name__ == "__main__":
    main()
