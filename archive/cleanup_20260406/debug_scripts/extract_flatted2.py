import subprocess, json

result = subprocess.run(
    ["docker", "exec", "salehsaas_postgres", "psql", "-U", "salehsaas", "-d", "salehsaas",
     "-t", "-A", "-c",
     "SELECT data FROM execution_data WHERE \"executionId\" = '164';"],
    capture_output=True, text=True
)

raw = result.stdout.strip()
data = json.loads(raw)

# Just look at the structure - first few items
root = json.loads(data[0]) if isinstance(data[0], str) else data[0]
print(f"Root: {root}")

# Get resultData  
rd_idx = int(root.get("resultData", "-1"))
print(f"\nresultData index: {rd_idx}")
rd_raw = data[rd_idx]
if isinstance(rd_raw, str):
    rd = json.loads(rd_raw)
    print(f"resultData keys: {list(rd.keys()) if isinstance(rd, dict) else type(rd)}")
    
    # Get error
    if "error" in rd:
        err_idx = rd["error"]
        print(f"\nerror index: {err_idx}")
        if isinstance(err_idx, str) and err_idx.isdigit():
            err_raw = data[int(err_idx)]
            if isinstance(err_raw, str):
                try:
                    err = json.loads(err_raw)
                    print(f"Error: {json.dumps(err, indent=2, ensure_ascii=False)[:2000]}")
                except:
                    print(f"Error raw: {err_raw[:1000]}")
        else:
            print(f"Error value: {err_idx}")

    # Get runData
    if "runData" in rd:
        rd_data_idx = rd["runData"]
        print(f"\nrunData index: {rd_data_idx}")
        if isinstance(rd_data_idx, str) and rd_data_idx.isdigit():
            rd_data_raw = data[int(rd_data_idx)]
            if isinstance(rd_data_raw, str):
                rd_data = json.loads(rd_data_raw)
                if isinstance(rd_data, dict):
                    print(f"runData nodes: {list(rd_data.keys())}")
                    # For each node, check if there's an error
                    for node_name, runs_idx in rd_data.items():
                        if isinstance(runs_idx, str) and runs_idx.isdigit():
                            runs_raw = data[int(runs_idx)]
                            if isinstance(runs_raw, str):
                                runs = json.loads(runs_raw)
                                if isinstance(runs, list):
                                    for run_idx_str in runs:
                                        if isinstance(run_idx_str, str) and run_idx_str.isdigit():
                                            run_raw = data[int(run_idx_str)]
                                            if isinstance(run_raw, str):
                                                run = json.loads(run_raw)
                                                if isinstance(run, dict) and "error" in run:
                                                    err_idx2 = run["error"]
                                                    if isinstance(err_idx2, str) and err_idx2.isdigit():
                                                        err2_raw = data[int(err_idx2)]
                                                        if isinstance(err2_raw, str):
                                                            try:
                                                                err2 = json.loads(err2_raw)
                                                                print(f"\n=== ERROR IN NODE: {node_name} ===")
                                                                print(f"  message: {err2.get('message', 'N/A')}")
                                                            except:
                                                                print(f"\n=== ERROR IN NODE: {node_name} ===")
                                                                print(f"  raw: {err2_raw[:500]}")
