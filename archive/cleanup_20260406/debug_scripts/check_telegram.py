"""Check what was sent to Telegram in execution 162."""
import json
import subprocess

result = subprocess.run(
    ["docker", "exec", "salehsaas_postgres", "psql", "-U", "salehsaas", "-d", "salehsaas",
     "-t", "-A", "-c",
     'SELECT "data"::text FROM execution_data WHERE "executionId" = 162'],
    capture_output=True, text=True, encoding='utf-8'
)
raw = result.stdout.strip()
data = json.loads(raw)

# Find Telegram-related data
for i, item in enumerate(data):
    if isinstance(item, str):
        if 'reply_markup' in item.lower() or 'inline_keyboard' in item.lower() or 'callback' in item.lower():
            print(f"  [{i}]: {item[:500]}")
        elif 'telegram' in item.lower() or 'sendMessage' in item.lower():
            print(f"  [{i}]: {item[:300]}")
        elif 'اعتماد' in item or 'رفض' in item or 'APPROVE' in item:
            print(f"  [{i}]: {item[:300]}")
    elif isinstance(item, dict):
        for k, v in item.items():
            if isinstance(v, str) and ('reply_markup' in v.lower() or 'inline' in v.lower() or 'callback' in v.lower() or 'اعتماد' in v or 'APPROVE' in v):
                print(f"  [{i}].{k}: {v[:500]}")
            elif k in ('reply_markup', 'inline_keyboard'):
                print(f"  [{i}].{k}: {json.dumps(v, ensure_ascii=False)[:500]}")

print("\n--- Telegram node output ---")
# Find the Telegram response (message_id, chat, etc.)
for i, item in enumerate(data):
    if isinstance(item, dict):
        if 'message_id' in item or 'chat' in item:
            print(f"  [{i}]: {json.dumps(item, ensure_ascii=False)[:500]}")
