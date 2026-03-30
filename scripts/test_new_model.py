"""Quick test: warm up qwen3-embedding:0.6b and compare dimensions."""
import requests, time

OLLAMA = "http://localhost:11434/api/embeddings"

print("Warming up qwen3-embedding:0.6b (first call loads model into RAM)...")
start = time.time()
r = requests.post(OLLAMA, json={"model": "qwen3-embedding:0.6b", "prompt": "test"}, timeout=600)
emb = r.json()["embedding"]
print(f"  Qwen3 dimension: {len(emb)}  (took {time.time()-start:.1f}s)")

start2 = time.time()
r2 = requests.post(OLLAMA, json={"model": "nomic-embed-text", "prompt": "test"}, timeout=600)
emb2 = r2.json()["embedding"]
print(f"  Nomic dimension: {len(emb2)}  (took {time.time()-start2:.1f}s)")

# Arabic legal test
r3 = requests.post(OLLAMA, json={"model": "qwen3-embedding:0.6b", "prompt": "ما هي حقوق العامل في نظام العمل السعودي"}, timeout=60)
emb3 = r3.json()["embedding"]
print(f"  Arabic legal test OK: {len(emb3)} dims")
print("Done!")
