"""Check published workflow header expressions and if $vars resolves."""
import json
import subprocess

# Get active version from workflow history
result = subprocess.run(
    ["docker", "exec", "salehsaas_postgres", "psql", "-U", "salehsaas", "-d", "salehsaas",
     "-t", "-A", "-c",
     """SELECT nodes::text FROM workflow_history WHERE "versionId" = (SELECT "activeVersionId" FROM workflow_entity WHERE id = 'CwCounclWbhk001')"""],
    capture_output=True, text=True, encoding='utf-8'
)

nodes_text = result.stdout.strip()
nodes = json.loads(nodes_text)

# Check cw-0005 header
for node in nodes:
    if node.get('id') == 'cw-0005':
        headers = node.get('parameters', {}).get('headerParameters', {}).get('parameters', [])
        print(f"Node: {node.get('name')}")
        for h in headers:
            print(f"  Header: {h.get('name')} = {h.get('value')}")
        print(f"  URL: {node.get('parameters', {}).get('url')}")
        jb = node.get('parameters', {}).get('jsonBody', '')
        print(f"  jsonBody (first 200): {jb[:200]}")
        print(f"  sendHeaders: {node.get('parameters', {}).get('sendHeaders')}")
        print(f"  specifyHeaders: {node.get('parameters', {}).get('specifyHeaders', 'NOT SET')}")
        break

# Check how many variables exist
result2 = subprocess.run(
    ["docker", "exec", "salehsaas_postgres", "psql", "-U", "salehsaas", "-d", "salehsaas",
     "-t", "-A", "-c",
     "SELECT key, value FROM variables"],
    capture_output=True, text=True, encoding='utf-8'
)
print(f"\nVariables:\n{result2.stdout.strip()}")
