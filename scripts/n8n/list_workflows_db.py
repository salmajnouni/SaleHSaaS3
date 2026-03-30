#!/usr/bin/env python3
"""
Get n8n workflows directly from postgres database
"""
import psycopg2
import json
from typing import List, Dict

# Database configuration
DB_HOST = "localhost"
DB_PORT = 5432
DB_NAME = "salehsaas"
DB_USER = "salehsaas"
DB_PASSWORD = "salehsaas_pass"

def get_workflows():
    """Fetch workflows from postgres"""
    try:
        print("[*] Connecting to postgres...")
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            connect_timeout=5
        )
        
        cursor = conn.cursor()
        print("[+] Connected successfully\n")
        
        # Query workflows
        print("[*] Fetching workflows from database...")
        cursor.execute("""
            SELECT id, name, active 
            FROM workflow 
            ORDER BY name, active DESC
        """)
        
        workflows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if not workflows:
            print("[-] No workflows found")
            return []
        
        print(f"[+] Found {len(workflows)} workflows:\n")
        
        # Parse and display
        result = []
        prev_name = None
        duplicate_count = {}
        
        for workflow_id, name, active in workflows:
            result.append({
                "id": workflow_id,
                "name": name,
                "active": active
            })
            
            # Track duplicates
            if name != prev_name:
                prev_name = name
                duplicate_count[name] = 0
            duplicate_count[name] += 1
            
            status = "[ACTIVE]" if active else "[INACTIVE]"
            dup_marker = f" (#{duplicate_count[name]})" if duplicate_count[name] > 1 else ""
            print(f"    {status} {name}{dup_marker}")
            print(f"        ID: {workflow_id}\n")
        
        return result
    
    except Exception as e:
        print(f"[-] Error: {e}")
        return []

if __name__ == "__main__":
    workflows = get_workflows()
    
    if workflows:
        # Analyze and report deletable workflows
        print("\n" + "="*60)
        print("CLEANUP ANALYSIS")
        print("="*60 + "\n")
        
        # Group by name
        by_name = {}
        for wf in workflows:
            name = wf["name"]
            if name not in by_name:
                by_name[name] = []
            by_name[name].append(wf)
        
        # Find duplicates and inactive ones
        to_delete = []
        for name, wfs in by_name.items():
            if len(wfs) > 1:
                print(f"[!] DUPLICATE: {name}")
                active_versions = [w for w in wfs if w["active"]]
                inactive_versions = [w for w in wfs if not w["active"]]
                
                if active_versions:
                    print(f"    Keep: {active_versions[0]['id']} [ACTIVE]")
                    for wf in inactive_versions:
                        print(f"    Delete: {wf['id']} [INACTIVE]")
                        to_delete.append(wf)
                else:
                    print(f"    Keep: {wfs[0]['id']} [NEWEST]")
                    for wf in wfs[1:]:
                        print(f"    Delete: {wf['id']}")
                        to_delete.append(wf)
                print()
        
        # Also check for completely unused workflows
        print(f"[*] Checking for unused/experimental workflows...\n")
        keep_keywords = {"knowledge", "saudi", "uqn", "legal", "chat", "sync", "update", "scraper", "monitor"}
        
        for wf in workflows:
            if not wf["active"] and wf not in to_delete:
                name_lower = wf["name"].lower()
                if not any(kw in name_lower for kw in keep_keywords):
                    print(f"    Candidate: {wf['id']} - {wf['name']} [INACTIVE]")
                    to_delete.append(wf)
        
        if not any(not wf["active"] and wf not in to_delete for wf in workflows):
            print("    (All other workflows are active or relevant)\n")
        
        # Summary
        print("\n" + "="*60)
        if to_delete:
            print(f"[+] READY TO DELETE: {len(to_delete)} workflow(s)")
            print("="*60 + "\n")
            for wf in to_delete:
                print(f"    {wf['id']} - {wf['name']}")
            print()
        else:
            print("[+] No workflows to delete - system is clean!")
            print("="*60 + "\n")
