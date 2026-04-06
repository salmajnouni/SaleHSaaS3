import os
import time
import requests
import json
from datetime import datetime

LOG_FILE = 'logs/self_improvement.log'
KNOWLEDGE_INBOX = 'knowledge_inbox'
CHROMA_URL = 'http://localhost:8010/api/v1/heartbeat'

def log_event(message):
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"[{datetime.now()}] {message}\n")

def check_system_health():
    # 1. Check if ChromaDB is responding
    try:
        response = requests.get(CHROMA_URL, timeout=5)
        if response.status_code != 200:
            log_event("WARNING: ChromaDB heartbeat failed. Indexing may be slow.")
    except:
        log_event("CRITICAL: ChromaDB unreachable via HTTP.")

    # 2. Check for pending legal files
    inbox_files = os.listdir(KNOWLEDGE_INBOX)
    if len(inbox_files) > 0:
        log_event(f"SUCCESS: System is processing {len(inbox_files)} new legal files in inbox.")
        # Trigger re-index if needed (placeholder for future trigger)

if __name__ == "__main__":
    log_event("System Self-Improvement Loop Started.")
    while True:
        check_system_health()
        time.sleep(300) # Check every 5 minutes
