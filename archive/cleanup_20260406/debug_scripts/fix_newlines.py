"""Fix newlines in jsonBody expressions - replace literal \\n with \\\\n in JSON."""
import json

with open('n8n/workflows/advisory_council_webhook.json', 'r', encoding='utf-8') as f:
    wf = json.load(f)

fixed = 0
for node in wf['nodes']:
    params = node.get('parameters', {})
    # Fix jsonBody expressions
    if 'jsonBody' in params and params['jsonBody'].startswith('={{'):
        old = params['jsonBody']
        # In the loaded Python string, \n chars are literal newlines
        # We need to replace them with the two-char sequence \n 
        new = old.replace('\n', '\\n')
        if new != old:
            params['jsonBody'] = new
            print(f"Fixed jsonBody in: {node.get('name', node.get('id'))}")
            fixed += 1
    
    # Fix text expressions (Telegram node)
    if 'text' in params and isinstance(params['text'], str) and params['text'].startswith('={{'):
        old = params['text']
        new = old.replace('\n', '\\n')
        if new != old:
            params['text'] = new
            print(f"Fixed text in: {node.get('name', node.get('id'))}")
            fixed += 1

print(f"\nTotal fields fixed: {fixed}")

with open('n8n/workflows/advisory_council_webhook.json', 'w', encoding='utf-8') as f:
    json.dump(wf, f, ensure_ascii=False, indent=2)

print("File saved.")
