import subprocess, json

result = subprocess.run(
    ["docker", "exec", "salehsaas_postgres", "psql", "-U", "salehsaas", "-d", "salehsaas",
     "-t", "-A", "-c",
     "SELECT data FROM execution_data WHERE \"executionId\" = '164';"],
    capture_output=True, text=True
)

raw = result.stdout.strip()
data = json.loads(raw)

# Error is at index 5
err = data[5]
print(f"Error object: {json.dumps(err, ensure_ascii=False)[:500]}")
print()

# Get message at index 23
msg_idx = int(err["message"]) if isinstance(err.get("message"), str) and err["message"].isdigit() else err.get("message")
if isinstance(msg_idx, int):
    print(f"Error message (idx {msg_idx}): {data[msg_idx]}")
else:
    print(f"Error message: {msg_idx}")

# Get description at index 16
desc_idx = int(err["description"]) if isinstance(err.get("description"), str) and err["description"].isdigit() else err.get("description")
if isinstance(desc_idx, int):
    print(f"Description (idx {desc_idx}): {str(data[desc_idx])[:500]}")
else:
    print(f"Description: {desc_idx}")

# Get node info at index 20
node_idx = int(err["node"]) if isinstance(err.get("node"), str) and err["node"].isdigit() else err.get("node")
if isinstance(node_idx, int):
    node_data = data[node_idx]
    if isinstance(node_data, dict):
        # Get node name
        name_idx = node_data.get("name", "")
        if isinstance(name_idx, str) and name_idx.isdigit():
            print(f"Node name: {data[int(name_idx)]}")
        else:
            print(f"Node name: {name_idx}")
    print(f"Node raw: {json.dumps(node_data, ensure_ascii=False)[:500]}")

# Last node executed at index 7
print(f"\nLast node executed: {data[7]}")

# httpCode at index 22
httpcode_idx = err.get("httpCode")
if isinstance(httpcode_idx, str) and httpcode_idx.isdigit():
    print(f"HTTP Code: {data[int(httpcode_idx)]}")
