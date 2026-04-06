import subprocess, json

result = subprocess.run(
    ["docker", "exec", "salehsaas_postgres", "psql", "-U", "salehsaas", "-d", "salehsaas",
     "-t", "-A", "-c",
     "SELECT data FROM execution_data WHERE \"executionId\" = '164';"],
    capture_output=True, text=True
)

raw = result.stdout.strip()
data = json.loads(raw)

# n8n 2.x uses flatted format - https://github.com/nicedreamer/flatted
# data[0] is the root object with string references to indices
# We need to recursively resolve references

def unflatten(arr):
    """Unflatten a flatted JSON array"""
    cache = [None] * len(arr)
    parsed = [None] * len(arr)
    
    def resolve(idx):
        if cache[idx] is not None:
            return cache[idx]
        
        item = arr[idx]
        if isinstance(item, str):
            # Try parsing as JSON
            try:
                val = json.loads(item)
            except:
                cache[idx] = item
                return item
            
            if isinstance(val, dict):
                result = {}
                cache[idx] = result  # Set early for circular refs
                for k, v in val.items():
                    if isinstance(v, str) and v.isdigit():
                        result[k] = resolve(int(v))
                    else:
                        result[k] = v
                return result
            elif isinstance(val, list):
                result = []
                cache[idx] = result
                for v in val:
                    if isinstance(v, str) and v.isdigit():
                        result.append(resolve(int(v)))
                    else:
                        result.append(v)
                return result
            elif isinstance(val, str):
                cache[idx] = val
                return val
            else:
                cache[idx] = val
                return val
        else:
            cache[idx] = item
            return item
    
    return resolve(0)

resolved = unflatten(data)
rd = resolved.get("resultData", {})

error = rd.get("error", None) if isinstance(rd, dict) else None
if error:
    print("=== TOP LEVEL ERROR ===")
    if isinstance(error, dict):
        print(f"Message: {error.get('message', 'N/A')}")
        print(f"Description: {error.get('description', 'N/A')}")
        print(f"Node: {error.get('node', {}).get('name', 'N/A') if isinstance(error.get('node'), dict) else 'N/A'}")
        print(f"Stack: {str(error.get('stack', ''))[:500]}")
    else:
        print(str(error)[:2000])

if isinstance(rd, dict):
    run_data = rd.get("runData", {})
    if isinstance(run_data, dict):
        for node_name, runs in run_data.items():
            if isinstance(runs, list):
                for run in runs:
                    if isinstance(run, dict) and run.get("error"):
                        print(f"\n=== ERROR IN NODE: {node_name} ===")
                        err = run["error"]
                        if isinstance(err, dict):
                            print(f"Message: {err.get('message', 'N/A')}")
                            print(f"Description: {err.get('description', 'N/A')}")
                        else:
                            print(str(err)[:500])
