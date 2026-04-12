"""Fix Code nodes: replace fetch() with helpers.httpRequest() in all scheduled workflows."""
import requests, json, os, re

env = {}
with open(os.path.join(os.path.dirname(__file__), '..', '.env')) as f:
    for line in f:
        line = line.strip()
        if '=' in line and not line.startswith('#'):
            k, v = line.split('=', 1)
            env[k] = v

key = env['N8N_API_KEY']
base = 'http://localhost:5678'
h = {'X-N8N-API-KEY': key, 'Content-Type': 'application/json'}

WORKFLOWS = {
    'UaJRWaaHtVldwoUl': 'Um Al-Qura Monitor',
    'YPVhIxCVGsgPpNDM': 'Auto-Update Laws',
    'HuuRe6ooTrbh5rJF': 'Legal Scraper',
}


def fetch_to_helpers(code: str) -> str:
    """Convert fetch()-based code to helpers.httpRequest()."""
    
    # Pattern 1: const resp = await fetch(url); const data = await resp.json();
    # → const data = await helpers.httpRequest({ method: 'GET', url: url, json: true });
    
    # Pattern 2: const resp = await fetch(url, {method:'POST', headers:{...}, body: JSON.stringify(data)});
    # const result = await resp.json();
    # → const result = await helpers.httpRequest({ method:'POST', url: url, headers:{...}, body: data, json: true });
    
    original = code
    changes = []
    
    # Strategy: line-by-line replacement
    lines = code.split('\n')
    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Match: const/let/var X = await fetch(URL);
        fetch_match = re.match(
            r'(\s*)(const|let|var)\s+(\w+)\s*=\s*await\s+fetch\(([^,)]+)\)\s*;',
            line
        )
        
        # Match: const/let/var X = await fetch(URL, { ... });
        fetch_opts_match = re.match(
            r'(\s*)(const|let|var)\s+(\w+)\s*=\s*await\s+fetch\(([^,]+),\s*\{',
            line
        )
        
        if fetch_match and not fetch_opts_match:
            # Simple GET fetch
            indent = fetch_match.group(1)
            decl = fetch_match.group(2)
            var_name = fetch_match.group(3)
            url_expr = fetch_match.group(4).strip()
            
            # Check if next line is .json()
            if i + 1 < len(lines):
                json_match = re.match(
                    r'\s*(const|let|var)\s+(\w+)\s*=\s*await\s+' + re.escape(var_name) + r'\.json\(\)\s*;',
                    lines[i + 1]
                )
                if json_match:
                    result_var = json_match.group(2)
                    new_lines.append(f'{indent}{json_match.group(1)} {result_var} = await helpers.httpRequest({{ method: "GET", url: {url_expr}, json: true }});')
                    changes.append(f'GET fetch → helpers.httpRequest (var: {result_var})')
                    i += 2
                    continue
            
            # No .json() follow-up - just replace fetch with helpers.httpRequest returning text
            new_lines.append(f'{indent}{decl} {var_name} = await helpers.httpRequest({{ method: "GET", url: {url_expr} }});')
            changes.append(f'GET fetch → helpers.httpRequest (var: {var_name}, raw)')
            i += 1
            continue

        elif fetch_opts_match:
            # Fetch with options - need to collect the full options block
            indent = fetch_opts_match.group(1)
            decl = fetch_opts_match.group(2)
            var_name = fetch_opts_match.group(3)
            url_expr = fetch_opts_match.group(4).strip()
            
            # Collect all lines until we find the closing });
            opts_lines = [line]
            j = i + 1
            brace_count = line.count('{') - line.count('}')
            while j < len(lines) and brace_count > 0:
                opts_lines.append(lines[j])
                brace_count += lines[j].count('{') - lines[j].count('}')
                j += 1
            
            # Parse method and body from the options
            full_fetch = '\n'.join(opts_lines)
            
            method_match = re.search(r'method\s*:\s*["\'](\w+)["\']', full_fetch)
            method = method_match.group(1) if method_match else 'POST'
            
            # Extract body - look for body: JSON.stringify(...)
            body_match = re.search(r'body\s*:\s*JSON\.stringify\((.+?)\)\s*[,}]', full_fetch, re.DOTALL)
            if not body_match:
                body_match = re.search(r'body\s*:\s*(.+?)\s*[,}]', full_fetch)
            
            body_expr = body_match.group(1).strip() if body_match else 'null'
            
            # Extract headers
            headers_match = re.search(r"headers\s*:\s*\{([^}]+)\}", full_fetch)
            headers_str = ''
            if headers_match:
                headers_str = f', headers: {{{headers_match.group(1)}}}'
            
            # Check if next line after fetch block is .json()
            if j < len(lines):
                json_match = re.match(
                    r'\s*(const|let|var)\s+(\w+)\s*=\s*await\s+' + re.escape(var_name) + r'\.json\(\)\s*;',
                    lines[j]
                )
                if json_match:
                    result_var = json_match.group(2)
                    new_lines.append(f'{indent}{json_match.group(1)} {result_var} = await helpers.httpRequest({{ method: "{method}", url: {url_expr}{headers_str}, body: {body_expr}, json: true }});')
                    changes.append(f'{method} fetch → helpers.httpRequest (var: {result_var})')
                    i = j + 1
                    continue
            
            # No .json() follow-up
            new_lines.append(f'{indent}{decl} {var_name} = await helpers.httpRequest({{ method: "{method}", url: {url_expr}{headers_str}, body: {body_expr}, json: true }});')
            changes.append(f'{method} fetch → helpers.httpRequest (var: {var_name})')
            i = j
            continue
        
        else:
            # Also handle: await resp.json() on its own line (if resp was already replaced)
            new_lines.append(line)
            i += 1
    
    new_code = '\n'.join(new_lines)
    return new_code, changes


fixed_count = 0
for wf_id, wf_name in WORKFLOWS.items():
    print(f'\n{"="*60}')
    print(f'Workflow: {wf_name} ({wf_id})')
    
    r = requests.get(f'{base}/api/v1/workflows/{wf_id}', headers=h)
    wf = r.json()
    
    modified = False
    for node in wf.get('nodes', []):
        if node.get('type') != 'n8n-nodes-base.code':
            continue
        
        code = node.get('parameters', {}).get('jsCode', '')
        if 'fetch(' not in code:
            continue
        
        print(f'\n  Node: {node["name"]}')
        print(f'  Has fetch() calls - converting...')
        
        new_code, changes = fetch_to_helpers(code)
        
        if changes:
            for c in changes:
                print(f'    ✓ {c}')
            node['parameters']['jsCode'] = new_code
            modified = True
            fixed_count += 1
        else:
            print(f'    ⚠ No patterns matched - manual review needed')
            print(f'    Code preview: {code[:200]}')
    
    if modified:
        # Deactivate first
        requests.post(f'{base}/api/v1/workflows/{wf_id}/deactivate', headers=h)
        
        # Update
        update_data = {
            'nodes': wf['nodes'],
            'connections': wf['connections'],
            'settings': wf.get('settings', {}),
            'name': wf['name']
        }
        r2 = requests.put(f'{base}/api/v1/workflows/{wf_id}', headers=h, json=update_data)
        print(f'  Update: {r2.status_code}')
        
        # Reactivate
        r3 = requests.post(f'{base}/api/v1/workflows/{wf_id}/activate', headers=h)
        print(f'  Activate: {r3.status_code}')
    else:
        print(f'  No fetch() calls found in Code nodes - skipping')

print(f'\n{"="*60}')
print(f'Total Code nodes fixed: {fixed_count}')
