"""Check the Telegram node in the published workflow version."""
import json
import subprocess

# Get the published version nodes
result = subprocess.run(
    ["docker", "exec", "salehsaas_postgres", "psql", "-U", "salehsaas", "-d", "salehsaas",
     "-t", "-A", "-c",
     """SELECT nodes::text FROM workflow_history WHERE "versionId" = (SELECT "activeVersionId" FROM workflow_entity WHERE id = 'CwCounclWbhk001')"""],
    capture_output=True, text=True, encoding='utf-8'
)

nodes = json.loads(result.stdout.strip())

for node in nodes:
    if node.get('id') == 'cw-0014':
        print("=== Telegram Node (cw-0014) from PUBLISHED version ===")
        print(json.dumps(node.get('parameters', {}), indent=2, ensure_ascii=False))
        break

# Also check the workflow_entity (draft) version
result2 = subprocess.run(
    ["docker", "exec", "salehsaas_postgres", "psql", "-U", "salehsaas", "-d", "salehsaas",
     "-t", "-A", "-c",
     "SELECT nodes::text FROM workflow_entity WHERE id = 'CwCounclWbhk001'"],
    capture_output=True, text=True, encoding='utf-8'
)

nodes2 = json.loads(result2.stdout.strip())

for node in nodes2:
    if node.get('id') == 'cw-0014':
        print("\n=== Telegram Node (cw-0014) from ENTITY version ===")
        print(json.dumps(node.get('parameters', {}), indent=2, ensure_ascii=False))
        break

# Also check execution 152 (working - but no buttons) workflowData
result3 = subprocess.run(
    ["docker", "exec", "salehsaas_postgres", "psql", "-U", "salehsaas", "-d", "salehsaas",
     "-t", "-A", "-c",
     'SELECT "workflowData"::text FROM execution_data WHERE "executionId" = 152'],
    capture_output=True, text=True, encoding='utf-8'
)
wf = json.loads(result3.stdout.strip())
if isinstance(wf, dict):
    for node in wf.get('nodes', []):
        if node.get('id') == 'cw-0014':
            print("\n=== Telegram Node (cw-0014) from EXECUTION 152 ===")
            print(json.dumps(node.get('parameters', {}), indent=2, ensure_ascii=False))
            break
