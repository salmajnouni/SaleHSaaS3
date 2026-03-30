#!/usr/bin/env python3
"""
Re-embed all ChromaDB chunks with Qwen3-Embedding-0.6B
=======================================================
Since dimensions changed (768 → 1024), creates a NEW collection,
copies all documents + metadata with new embeddings, then swaps.

Operational note:
This is a migration helper for a Qwen3 path, not the current default runtime path.
Current runtime uses `saleh_knowledge` + `nomic-embed-text:latest` unless explicitly changed.

Usage:
    python scripts/reembed_qwen3.py              # full re-embed
    python scripts/reembed_qwen3.py --test 10    # test with 10 chunks
    python scripts/reembed_qwen3.py --resume     # resume from last checkpoint
"""
import requests, json, time, sys, os, logging, argparse


def _configure_stdio_utf8():
    """Keep Arabic output readable when redirected/piped on Windows."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding='utf-8')
        except Exception:
            pass


_configure_stdio_utf8()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    stream=sys.stdout,
)
log = logging.getLogger(__name__)

CHROMADB = 'http://localhost:8010/api/v1'
OLLAMA = 'http://localhost:11434'
OLD_CID = '8c394725-8a25-4c26-a0d3-4711f554aab8'
NEW_COLLECTION_NAME = os.getenv('TARGET_COLLECTION', 'saleh_knowledge_qwen3')
NEW_MODEL = os.getenv('TARGET_EMBED_MODEL', 'qwen3-embedding:0.6b')
BATCH_SIZE = 50
UPSERT_BATCH = 40  # smaller batch for upsert with full data
CHECKPOINT_FILE = 'data/reembed_checkpoint.json'


def get_total_count():
    r = requests.get(f'{CHROMADB}/collections/{OLD_CID}/count')
    return r.json()


def get_or_create_new_collection():
    """Create new collection for Qwen3 embeddings."""
    # Check if exists
    r = requests.get(f'{CHROMADB}/collections')
    for col in r.json():
        if col['name'] == NEW_COLLECTION_NAME:
            log.info(f"Found existing collection: {col['id']}")
            return col['id']
    # Create
    r = requests.post(f'{CHROMADB}/collections', json={
        'name': NEW_COLLECTION_NAME,
        'metadata': {'hnsw:space': 'cosine'}
    })
    new_col = r.json()
    log.info(f"Created new collection: {new_col['id']}")
    return new_col['id']


def get_all_data(offset, limit):
    """Get chunk IDs, documents, and metadata from OLD collection."""
    r = requests.post(f'{CHROMADB}/collections/{OLD_CID}/get', json={
        'include': ['documents', 'metadatas'],
        'limit': limit,
        'offset': offset
    })
    return r.json()


def embed_text(text):
    """Get embedding from Qwen3 via Ollama."""
    r = requests.post(f'{OLLAMA}/api/embeddings', json={
        'model': NEW_MODEL,
        'prompt': text
    }, timeout=120)
    return r.json()['embedding']


def upsert_to_new(new_cid, ids, documents, metadatas, embeddings):
    """Upsert chunks into new collection."""
    r = requests.post(f'{CHROMADB}/collections/{new_cid}/upsert', json={
        'ids': ids,
        'documents': documents,
        'metadatas': metadatas,
        'embeddings': embeddings
    })
    return r.json()


def save_checkpoint(processed_count, new_cid):
    os.makedirs(os.path.dirname(CHECKPOINT_FILE), exist_ok=True)
    with open(CHECKPOINT_FILE, 'w') as f:
        json.dump({
            'processed': processed_count,
            'new_cid': new_cid,
            'model': NEW_MODEL,
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S')
        }, f)


def load_checkpoint():
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, 'r') as f:
            return json.load(f)
    return None


def main():
    parser = argparse.ArgumentParser(description='Re-embed ChromaDB chunks with Qwen3-Embedding')
    parser.add_argument('--test', type=int, help='Only process N chunks (for testing)')
    parser.add_argument('--resume', action='store_true', help='Resume from last checkpoint')
    args = parser.parse_args()

    log.info("=" * 60)
    log.info(f"  Re-embedding with {NEW_MODEL}")
    log.info(f"  768-dim (nomic) → 1024-dim (qwen3)")
    log.info("=" * 60)

    # Warm up model
    log.info("Warming up model...")
    start = time.time()
    test_emb = embed_text("اختبار")
    dim = len(test_emb)
    log.info(f"Model ready: dimension={dim}, warmup={time.time()-start:.1f}s")

    # Create new collection
    new_cid = get_or_create_new_collection()
    total = get_total_count()
    log.info(f"Old collection chunks: {total}")

    # Resume support
    start_offset = 0
    if args.resume:
        cp = load_checkpoint()
        if cp and cp.get('new_cid') == new_cid:
            start_offset = cp['processed']
            log.info(f"Resuming from offset {start_offset}")

    if args.test:
        total = min(args.test, total)
        log.info(f"TEST MODE: processing {total} chunks only")

    # Process in batches
    success = 0
    errors = 0
    offset = start_offset
    start_time = time.time()
    fetch_batch = 200  # fetch more, process in smaller upsert batches

    while offset < total:
        # Fetch batch from old collection
        data = get_all_data(offset, min(fetch_batch, total - offset))
        ids = data.get('ids', [])
        documents = data.get('documents', [])
        metadatas = data.get('metadatas', [])

        if not ids:
            break

        # Process in upsert-sized sub-batches
        for sub_start in range(0, len(ids), UPSERT_BATCH):
            sub_end = min(sub_start + UPSERT_BATCH, len(ids))
            sub_ids = ids[sub_start:sub_end]
            sub_docs = documents[sub_start:sub_end]
            sub_metas = metadatas[sub_start:sub_end]

            # Embed each document
            sub_embeddings = []
            valid_ids = []
            valid_docs = []
            valid_metas = []

            for chunk_id, doc, meta in zip(sub_ids, sub_docs, sub_metas):
                if not doc or not doc.strip():
                    log.warning(f"  Empty doc: {chunk_id}")
                    errors += 1
                    continue
                try:
                    emb = embed_text(doc)
                    sub_embeddings.append(emb)
                    valid_ids.append(chunk_id)
                    valid_docs.append(doc)
                    valid_metas.append(meta)
                except Exception as e:
                    log.error(f"  Embed error {chunk_id}: {e}")
                    errors += 1

            # Upsert to new collection
            if valid_ids:
                try:
                    upsert_to_new(new_cid, valid_ids, valid_docs, valid_metas, sub_embeddings)
                    success += len(valid_ids)
                except Exception as e:
                    log.error(f"  Upsert error: {e}")
                    errors += len(valid_ids)

        offset += len(ids)

        # Progress
        elapsed = time.time() - start_time
        rate = success / elapsed if elapsed > 0 else 0
        remaining = total - offset
        eta = remaining / rate / 60 if rate > 0 else 0
        log.info(f"  [{offset}/{total}] success={success} errors={errors} "
                 f"rate={rate:.1f}/s ETA={eta:.1f}min")

        # Checkpoint every 500
        if offset % 500 < fetch_batch:
            save_checkpoint(offset, new_cid)

    # Final checkpoint
    elapsed = time.time() - start_time
    save_checkpoint(offset, new_cid)

    # Verify new collection count
    r = requests.get(f'{CHROMADB}/collections/{new_cid}/count')
    new_count = r.json()

    log.info("")
    log.info("=" * 60)
    log.info(f"  RE-EMBEDDING COMPLETE")
    log.info(f"  Model: {NEW_MODEL} (dim={dim})")
    log.info(f"  New collection: {NEW_COLLECTION_NAME} ({new_cid})")
    log.info(f"  Chunks migrated: {new_count}")
    log.info(f"  Success: {success}, Errors: {errors}")
    log.info(f"  Time: {elapsed/60:.1f} minutes")
    log.info("=" * 60)
    log.info("")
    log.info("Next steps:")
    log.info("  1. Test RAG with new collection")
    log.info("  2. If good, rename collections (swap old/new)")
    log.info(f"  3. Update CID in scripts to: {new_cid}")


if __name__ == '__main__':
    main()
