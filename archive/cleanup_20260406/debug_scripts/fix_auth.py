"""Fix Authorization header syntax in all HTTP Request nodes.

The header value needs to be:
  ={{ 'Bearer ' + ($vars.WEBUI_API_KEY || 'sk-773169e4bcce483fb5e8268e9bf393dc') }}
Instead of:
  Bearer {{ $vars.WEBUI_API_KEY }}

Also adds specifyHeaders: "keypair" which is required.
"""
import json

with open('n8n/workflows/advisory_council_webhook.json', 'r', encoding='utf-8') as f:
    wf = json.load(f)

fixed = 0
for node in wf['nodes']:
    params = node.get('parameters', {})
    if params.get('sendHeaders') is True:
        # Add specifyHeaders if missing
        if 'specifyHeaders' not in params:
            params['specifyHeaders'] = 'keypair'
        
        # Fix Authorization header value
        headers = params.get('headerParameters', {}).get('parameters', [])
        for h in headers:
            if h.get('name') == 'Authorization':
                old = h['value']
                if '{{ $vars.WEBUI_API_KEY }}' in old:
                    h['value'] = "={{ 'Bearer ' + ($vars.WEBUI_API_KEY || 'sk-773169e4bcce483fb5e8268e9bf393dc') }}"
                    print(f"Fixed header in: {node.get('name', node.get('id'))}")
                    print(f"  Old: {old}")
                    print(f"  New: {h['value']}")
                    fixed += 1

print(f"\nTotal nodes fixed: {fixed}")

with open('n8n/workflows/advisory_council_webhook.json', 'w', encoding='utf-8') as f:
    json.dump(wf, f, ensure_ascii=False, indent=2)

print("File saved.")
