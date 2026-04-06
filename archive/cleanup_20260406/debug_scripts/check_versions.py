"""Check if the published version in workflow_history has correct expressions."""
import json
import subprocess

# Get the published version data
result = subprocess.run(
    ["docker", "exec", "salehsaas_postgres", "psql", "-U", "salehsaas", "-d", "salehsaas",
     "-t", "-A", "-c",
     """SELECT nodes::text FROM workflow_history WHERE "versionId" = '0e2cc9df-31a8-4341-95ac-f1108a9e5c30'"""],
    capture_output=True, text=True, encoding='utf-8'
)

nodes_text = result.stdout.strip()
print(f"History nodes length: {len(nodes_text)}")

try:
    nodes = json.loads(nodes_text)
    # Find the legal agent node (cw-0005)
    for node in nodes:
        if node.get('id') == 'cw-0005':
            jb = node.get('parameters', {}).get('jsonBody', '')
            print(f"\n=== cw-0005 jsonBody from HISTORY ===")
            print(jb[:500])
            break
except json.JSONDecodeError as e:
    print(f"JSON error: {e}")
    print(f"First 200 chars: {nodes_text[:200]}")

# Also check what workflow_entity has
result2 = subprocess.run(
    ["docker", "exec", "salehsaas_postgres", "psql", "-U", "salehsaas", "-d", "salehsaas",
     "-t", "-A", "-c",
     "SELECT nodes::text FROM workflow_entity WHERE id = 'CwCounclWbhk001'"],
    capture_output=True, text=True, encoding='utf-8'
)

nodes_text2 = result2.stdout.strip()
print(f"\nEntity nodes length: {len(nodes_text2)}")

try:
    nodes2 = json.loads(nodes_text2)
    for node in nodes2:
        if node.get('id') == 'cw-0005':
            jb2 = node.get('parameters', {}).get('jsonBody', '')
            print(f"\n=== cw-0005 jsonBody from ENTITY ===")
            print(jb2[:500])
            break
except json.JSONDecodeError as e:
    print(f"JSON error: {e}")

# Compare working execution 152's workflow data  
result3 = subprocess.run(
    ["docker", "exec", "salehsaas_postgres", "psql", "-U", "salehsaas", "-d", "salehsaas",
     "-t", "-A", "-c",
     """SELECT "workflowData" FROM execution_data WHERE "executionId" = 152"""],
    capture_output=True, text=True, encoding='utf-8'
)

wf_text = result3.stdout.strip()
print(f"\nExecution 152 workflowData length: {len(wf_text)}")
if wf_text:
    try:
        wf = json.loads(wf_text)
        if isinstance(wf, list):
            # Compressed format - find jsonBody entries
            for i, item in enumerate(wf):
                if isinstance(item, str) and 'COUNCIL_MODEL' in item and 'الامتثال' in item:
                    print(f"\n=== Execution 152 jsonBody (index {i}) ===")
                    print(item[:500])
                    break
        elif isinstance(wf, dict):
            nodes3 = wf.get('nodes', [])
            for node in nodes3:
                if node.get('id') == 'cw-0005':
                    jb3 = node.get('parameters', {}).get('jsonBody', '')
                    print(f"\n=== cw-0005 jsonBody from exec 152 ===")
                    print(jb3[:500])
                    break
    except json.JSONDecodeError:
        pass
