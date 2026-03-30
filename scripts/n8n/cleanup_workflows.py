#!/usr/bin/env python3
"""
Clean up unused and duplicate n8n workflows
"""
import requests
import json
from typing import List, Dict, Optional

# n8n configuration
N8N_URL = "http://localhost:5678"
N8N_USER = "salmajnouni@gmail.com"
N8N_PASSWORD = "SalehSaaS2026!"

# Workflows to keep (by exact name)
WORKFLOWS_TO_KEEP = {
    "Knowledge Ingestion",
    "Saudi Laws Sync",
    "Saudi Laws Chat",
    "Saudi Laws Auto Update",
    "UQN Gazette Monitor",
    "Saudi Legal Scraper"
}

class N8NWorkflowManager:
    def __init__(self, url: str, user: str, password: str):
        self.base_url = url
        self.user = user
        self.password = password
        self.session = requests.Session()
        self.api_key = None
        
    def login(self) -> bool:
        """Login and get API key"""
        try:
            print("[*] Attempting to login to n8n...")
            response = self.session.post(
                f"{self.base_url}/api/v1/auth/login",
                json={"email": self.user, "password": self.password},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.api_key = data.get("data", {}).get("apiKey")
                if self.api_key:
                    print(f"[+] Login successful. API Key: {self.api_key[:20]}...")
                    self.session.headers.update({"X-N8N-API-Key": self.api_key})
                    return True
                else:
                    print("[-] No API key in response")
                    return False
            else:
                print(f"[-] Login failed: {response.status_code}")
                print(response.text)
                return False
        except Exception as e:
            print(f"[-] Login error: {e}")
            return False
    
    def get_workflows(self) -> Optional[List[Dict]]:
        """Get all workflows"""
        try:
            print("[*] Fetching workflows...")
            response = self.session.get(
                f"{self.base_url}/api/v1/workflows",
                timeout=10
            )
            
            if response.status_code == 200:
                workflows = response.json().get("data", [])
                print(f"[+] Found {len(workflows)} workflows")
                return workflows
            else:
                print(f"[-] Failed to fetch workflows: {response.status_code}")
                print(response.text)
                return None
        except Exception as e:
            print(f"[-] Error fetching workflows: {e}")
            return None
    
    def identify_duplicates(self, workflows: List[Dict]) -> Dict[str, List[Dict]]:
        """Group workflows by name and identify duplicates"""
        grouped = {}
        for wf in workflows:
            name = wf.get("name", "Unknown")
            if name not in grouped:
                grouped[name] = []
            grouped[name].append(wf)
        
        duplicates = {name: wfs for name, wfs in grouped.items() if len(wfs) > 1}
        return duplicates
    
    def should_delete(self, workflow: Dict) -> bool:
        """Determine if a workflow should be deleted"""
        name = workflow.get("name", "")
        is_active = workflow.get("active", False)
        
        # Keep active workflows
        if is_active:
            return False
        
        # Keep workflows in the keep list
        if name in WORKFLOWS_TO_KEEP:
            return False
        
        # Delete inactive workflows that don't match keep list or are duplicates
        return True
    
    def delete_workflow(self, workflow_id: str, name: str) -> bool:
        """Delete a workflow by ID"""
        try:
            print(f"  [*] Deleting workflow: {name} (ID: {workflow_id})")
            response = self.session.delete(
                f"{self.base_url}/api/v1/workflows/{workflow_id}",
                timeout=10
            )
            
            if response.status_code == 204 or response.status_code == 200:
                print(f"  [+] Successfully deleted: {name}")
                return True
            else:
                print(f"  [-] Failed to delete {name}: {response.status_code}")
                print(f"      {response.text}")
                return False
        except Exception as e:
            print(f"  [-] Error deleting {name}: {e}")
            return False
    
    def cleanup(self) -> None:
        """Main cleanup process"""
        print("\n" + "="*60)
        print("n8n WORKFLOW CLEANUP TOOL")
        print("="*60 + "\n")
        
        # Login
        if not self.login():
            print("[-] Failed to authenticate. Exiting.")
            return
        
        # Get workflows
        workflows = self.get_workflows()
        if not workflows:
            print("[-] No workflows found or error fetching. Exiting.")
            return
        
        # Print current state
        print("\n[*] Current workflows:")
        for wf in workflows:
            status = "[ACTIVE]" if wf.get("active") else "[INACTIVE]"
            print(f"    {status} {wf.get('name')} (ID: {wf.get('id')})")
        
        # Identify candidates for deletion
        print("\n[*] Analyzing for cleanup candidates...")
        to_delete = []
        
        for wf in workflows:
            name = wf.get("name", "")
            workflow_id = wf.get("id", "")
            is_active = wf.get("active", False)
            
            if self.should_delete(wf):
                to_delete.append({
                    "id": workflow_id,
                    "name": name,
                    "active": is_active
                })
        
        # Check for duplicates
        duplicates = self.identify_duplicates(workflows)
        print(f"\n[*] Found {len(duplicates)} duplicate workflow names:")
        for name, wfs in duplicates.items():
            print(f"    {name}:")
            for wf in wfs:
                status = "ACTIVE" if wf.get("active") else "INACTIVE"
                print(f"        - ID: {wf.get('id')} [{status}]")
            
            # Keep the active one, mark others for deletion if inactive
            active_wfs = [w for w in wfs if w.get("active")]
            inactive_wfs = [w for w in wfs if not w.get("active")]
            
            if active_wfs and len(active_wfs) == 1:
                print(f"        → Keeping active version: {active_wfs[0].get('id')}")
                # Add inactive ones to deletion list
                for wf in inactive_wfs:
                    if wf not in to_delete:
                        to_delete.append({
                            "id": wf.get("id"),
                            "name": f"{name} (duplicate)",
                            "active": False
                        })
        
        # Report and confirm
        if to_delete:
            print(f"\n[!] Found {len(to_delete)} workflow(s) to delete:")
            for wf in to_delete:
                print(f"    - {wf['name']} (ID: {wf['id']}) [{'ACTIVE' if wf['active'] else 'INACTIVE'}]")
            
            # Confirm before deletion
            confirm = input("\n[?] Proceed with deletion? (yes/no): ").strip().lower()
            if confirm == "yes":
                print("\n[*] Starting deletion process...\n")
                deleted_count = 0
                for wf in to_delete:
                    if self.delete_workflow(wf["id"], wf["name"]):
                        deleted_count += 1
                
                print(f"\n[+] Cleanup complete. Deleted {deleted_count}/{len(to_delete)} workflows.")
            else:
                print("\n[-] Deletion cancelled.")
        else:
            print("\n[+] No workflows to delete. System is clean!")
        
        print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    manager = N8NWorkflowManager(N8N_URL, N8N_USER, N8N_PASSWORD)
    manager.cleanup()
