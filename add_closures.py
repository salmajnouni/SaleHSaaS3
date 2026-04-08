#!/usr/bin/env python3
import json
from datetime import datetime, timezone
import os

logfile = 'logs/ops_journal.jsonl'

entries = [
    {
        'ts_utc': datetime.now(timezone.utc).isoformat(),
        'category': 'test',
        'action': 'remove_synthetic_deviation_signal',
        'status': 'ok',
        'summary': 'Removed synthetic test deviation signal',
        'details': 'Test entry was for detector verification only',
        'next_step': 'Monitor real deviations only',
        'metric': '',
        'host': os.getenv('COMPUTERNAME', 'NUCBOX'),
        'user': os.getenv('USERNAME', 'SALEH')
    },
    {
        'ts_utc': datetime.now(timezone.utc).isoformat(),
        'category': 'config',
        'action': 'resolve_env_vars_decision',
        'status': 'ok',
        'summary': 'N8N_API_KEY and TELEGRAM_BOT_TOKEN marked as optional',
        'details': 'System functions correctly without them. Non-blocking.',
        'next_step': 'Keep optional; add if Telegram integration needed',
        'metric': '',
        'host': os.getenv('COMPUTERNAME', 'NUCBOX'),
        'user': os.getenv('USERNAME', 'SALEH')
    },
    {
        'ts_utc': datetime.now(timezone.utc).isoformat(),
        'category': 'n8n',
        'action': 'resolve_python_runner_decision',
        'status': 'ok',
        'summary': 'Python task runner stays JS-only - no blocking issue',
        'details': 'JS executor operational. Python integration disabled.',
        'next_step': 'Enable Python runner only if needed for workflows',
        'metric': '',
        'host': os.getenv('COMPUTERNAME', 'NUCBOX'),
        'user': os.getenv('USERNAME', 'SALEH')
    }
]

with open(logfile, 'a', encoding='utf-8') as f:
    for e in entries:
        f.write('\n' + json.dumps(e, ensure_ascii=False))

print(f'✓ Added 3 entries to {logfile}')

# Verify
with open(logfile, 'r', encoding='utf-8') as f:
    count = len([l for l in f if l.strip()])
print(f'Total entries: {count}')
