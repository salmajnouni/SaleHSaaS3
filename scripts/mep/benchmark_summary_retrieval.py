"""Benchmark retrieval quality for MEP summary cards in Chroma.

Scoring rule:
- Pass if at least one of top-k sources includes the expected code token (e.g., sbc501, sbc701, sbc801, ashrae, nfpa).
"""

from __future__ import annotations

import argparse
import json
import math
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

import requests


DEFAULT_CHROMA_BASE_URL = "http://localhost:8010/api/v1"
DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_EMBED_MODEL = "auto"
DEFAULT_EMBED_CANDIDATES = [
    "nomic-embed-text:latest",
    "qwen3-embedding:0.6b",
]


def parse_expected_tokens(expected_source: str) -> set[str]:
    text = expected_source.lower()
    tokens = set()

    # Normalize SBC forms like SBC-501, SBC 501.
    for m in re.findall(r"sbc\s*-?\s*(\d+)", text):
        tokens.add(f"sbc{m}")

    if "ashrae" in text:
        tokens.add("ashrae")
    if "nfpa" in text:
        tokens.add("nfpa")

    # Fallback tokenization if no known anchors were found.
    if not tokens:
        for t in re.findall(r"[a-z0-9]+", text):
            if len(t) >= 4:
                tokens.add(t)
    return tokens


def get_collection_id(chroma_base_url: str, collection_name: str) -> str:
    resp = requests.get(f"{chroma_base_url}/collections", timeout=30)
    resp.raise_for_status()
    cols = resp.json()
    name_to_id = {c.get("name"): c.get("id") for c in cols}
    cid = name_to_id.get(collection_name)
    if not cid:
        raise RuntimeError(
            f"Collection '{collection_name}' not found. Available: {list(name_to_id.keys())}"
        )
    return cid


def get_collection_dimension(chroma_base_url: str, collection_id: str) -> int:
    resp = requests.post(
        f"{chroma_base_url}/collections/{collection_id}/get",
        json={"include": ["embeddings"], "limit": 1},
        timeout=60,
    )
    resp.raise_for_status()
    payload = resp.json()
    embeddings = payload.get("embeddings") or []
    if not embeddings or not embeddings[0]:
        raise RuntimeError("Could not infer collection embedding dimension")
    return len(embeddings[0])


def embed_query(ollama_base_url: str, model: str, query: str) -> list[float]:
    resp = requests.post(
        f"{ollama_base_url}/api/embeddings",
        json={"model": model, "prompt": query},
        timeout=60,
    )
    resp.raise_for_status()
    payload = resp.json()
    emb = payload.get("embedding")
    if not emb:
        raise RuntimeError("No embedding returned from Ollama")
    return emb


def choose_embed_model(
    ollama_base_url: str,
    collection_dim: int,
    preferred_model: str,
    candidates: list[str],
) -> str:
    candidate_list = [preferred_model] if preferred_model != "auto" else list(candidates)
    if not candidate_list:
        raise RuntimeError("No embedding model candidates provided")

    for model in candidate_list:
        try:
            emb = embed_query(ollama_base_url, model, "dimension-check")
            if len(emb) == collection_dim:
                return model
        except Exception:
            continue

    raise RuntimeError(
        f"No compatible embedding model found for collection dimension {collection_dim}. "
        f"Tried: {candidate_list}"
    )


def retrieve_sources(
    summary_vectors: list[dict[str, Any]],
    query_embedding: list[float],
    n_results: int,
) -> tuple[list[str], list[float]]:
    q_norm = math.sqrt(sum(v * v for v in query_embedding))
    if q_norm == 0:
        raise RuntimeError("Query embedding has zero norm")

    scored: list[tuple[str, float]] = []
    for row in summary_vectors:
        emb = row["embedding"]
        dot = sum(a * b for a, b in zip(query_embedding, emb))
        emb_norm = row["norm"]
        if emb_norm == 0:
            continue
        cosine = dot / (q_norm * emb_norm)
        distance = 1.0 - cosine
        scored.append((row["source"], float(distance)))

    scored.sort(key=lambda x: x[1])
    top = scored[:n_results]
    sources = [src.lower() for src, _ in top]
    distances = [dist for _, dist in top]
    return sources, distances


def fetch_summary_vectors(chroma_base_url: str, collection_id: str) -> list[dict[str, Any]]:
    count_resp = requests.get(f"{chroma_base_url}/collections/{collection_id}/count", timeout=30)
    count_resp.raise_for_status()
    total = count_resp.json()

    get_resp = requests.post(
        f"{chroma_base_url}/collections/{collection_id}/get",
        json={"include": ["embeddings", "metadatas"], "limit": total},
        timeout=180,
    )
    get_resp.raise_for_status()
    payload = get_resp.json()

    vectors: list[dict[str, Any]] = []
    for emb, meta in zip(payload.get("embeddings", []), payload.get("metadatas", [])):
        if not isinstance(meta, dict):
            continue
        source = str(meta.get("source", ""))
        if "summary-card_" not in source:
            continue
        if not emb:
            continue
        norm = math.sqrt(sum(v * v for v in emb))
        vectors.append({"source": source, "embedding": emb, "norm": norm})
    return vectors


def evaluate_question(
    q: dict[str, Any],
    summary_vectors: list[dict[str, Any]],
    ollama_base_url: str,
    embed_model: str,
    top_k: int,
) -> dict[str, Any]:
    query_text = str(q.get("question_ar", "")).strip()
    expected_source = str(q.get("expected_source", ""))
    expected_tokens = parse_expected_tokens(expected_source)

    embedding = embed_query(ollama_base_url, embed_model, query_text)
    sources, distances = retrieve_sources(summary_vectors, embedding, top_k)

    hits = []
    for src in sources:
        matched = sorted([t for t in expected_tokens if t in src])
        hits.append({"source": src, "matched_tokens": matched})

    pass_hit = any(h["matched_tokens"] for h in hits)
    min_distance = min(distances) if distances else None

    return {
        "id": q.get("id"),
        "domain": q.get("domain"),
        "expected_source": expected_source,
        "expected_tokens": sorted(expected_tokens),
        "pass": pass_hit,
        "min_distance": min_distance,
        "top_hits": hits,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark summary-card retrieval quality")
    parser.add_argument(
        "--benchmark-file",
        default="data/mep_rag/benchmark_questions_mep.json",
        help="Path to benchmark JSON file",
    )
    parser.add_argument("--chroma-base-url", default=DEFAULT_CHROMA_BASE_URL)
    parser.add_argument("--collection", default="saleh_knowledge")
    parser.add_argument("--ollama-base-url", default=DEFAULT_OLLAMA_BASE_URL)
    parser.add_argument("--embed-model", default=DEFAULT_EMBED_MODEL)
    parser.add_argument(
        "--embed-model-candidates",
        default=",".join(DEFAULT_EMBED_CANDIDATES),
        help="Comma-separated candidate models for auto mode",
    )
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument(
        "--output-json",
        default="data/mep_rag/benchmark_results_summary_retrieval.json",
        help="Where to write detailed benchmark result JSON",
    )
    args = parser.parse_args()

    benchmark_path = Path(args.benchmark_file)
    payload = json.loads(benchmark_path.read_text(encoding="utf-8"))
    questions = payload.get("questions", [])

    collection_id = get_collection_id(args.chroma_base_url, args.collection)

    collection_dim = get_collection_dimension(args.chroma_base_url, collection_id)
    summary_vectors = fetch_summary_vectors(args.chroma_base_url, collection_id)
    candidate_models = [m.strip() for m in args.embed_model_candidates.split(",") if m.strip()]
    active_embed_model = choose_embed_model(
        ollama_base_url=args.ollama_base_url,
        collection_dim=collection_dim,
        preferred_model=args.embed_model,
        candidates=candidate_models,
    )

    results = []
    for q in questions:
        results.append(
            evaluate_question(
                q=q,
                summary_vectors=summary_vectors,
                ollama_base_url=args.ollama_base_url,
                embed_model=active_embed_model,
                top_k=args.top_k,
            )
        )

    total = len(results)
    passed = sum(1 for r in results if r["pass"])
    by_domain_total: dict[str, int] = defaultdict(int)
    by_domain_pass: dict[str, int] = defaultdict(int)
    for r in results:
        domain = str(r.get("domain", "unknown"))
        by_domain_total[domain] += 1
        if r["pass"]:
            by_domain_pass[domain] += 1

    summary = {
        "collection": args.collection,
        "collection_id": collection_id,
        "collection_dimension": collection_dim,
        "embed_model": active_embed_model,
        "summary_vector_count": len(summary_vectors),
        "top_k": args.top_k,
        "total_questions": total,
        "passed_questions": passed,
        "pass_rate": round((passed / total) * 100, 2) if total else 0.0,
        "domain_pass_rate": {
            d: round((by_domain_pass[d] / by_domain_total[d]) * 100, 2)
            for d in sorted(by_domain_total)
        },
    }

    report = {"summary": summary, "results": results}
    out_path = Path(args.output_json)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"Detailed report written to: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
