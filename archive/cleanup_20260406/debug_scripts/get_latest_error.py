import subprocess, json

result = subprocess.run(
    ["docker", "exec", "salehsaas_postgres", "psql", "-U", "salehsaas", "-d", "salehsaas",
     "-t", "-A", "-c",
     "SELECT data FROM execution_data WHERE \"executionId\" = (SELECT MAX(id) FROM execution_entity WHERE \"workflowId\" = 'CwCounclWbhk001');"],
    capture_output=True, text=True
)

raw = result.stdout.strip()
data = json.loads(raw)

# data[5] is error, data[7] is last node, data[23] is message
# But indices might differ. Let's navigate from root
root = data[0]
rd_idx = int(root["resultData"])
rd = data[rd_idx]

if "error" in rd:
    err_idx = int(rd["error"])
    err = data[err_idx]
    
    msg_idx = int(err["message"])
    print(f"Error message: {data[msg_idx]}")
    
    desc_idx = int(err.get("description", "0"))
    print(f"Description: {data[desc_idx]}")
    
    node_idx = int(err.get("node", "0"))
    node = data[node_idx]
    if isinstance(node, dict):
        name_ref = node.get("name", "")
        if isinstance(name_ref, str) and name_ref.isdigit():
            print(f"Node: {data[int(name_ref)]}")
        else:
            print(f"Node: {name_ref}")
    
    # Check for httpCode
    if "httpCode" in err:
        hc_idx = int(err["httpCode"])
        print(f"HTTP Code: {data[hc_idx]}")

# Print run data node names
if "runData" in rd:
    rd_data_idx = int(rd["runData"])
    rd_data = data[rd_data_idx]
    if isinstance(rd_data, dict):
        print(f"\nNodes executed: {list(rd_data.keys())}")
