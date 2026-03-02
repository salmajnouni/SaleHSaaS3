# knowledge_processing

This folder is **auto-managed** by the Knowledge Watcher service.

Files appear here temporarily while being processed (text extraction + embedding + ChromaDB ingestion).

- If a file is stuck here after a restart, it will be automatically re-queued to `knowledge_inbox`.
- Do NOT manually add files here.
