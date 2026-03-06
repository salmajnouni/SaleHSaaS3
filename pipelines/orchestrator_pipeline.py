
# ── Embedded Conversation Logger ─────────────────────────────────────────────
import threading, time, json as _json, uuid as _uuid, os as _os

try:
    import psycopg2 as _pg
    import psycopg2.extras as _pgx
    _PG_OK = True
except ImportError:
    _PG_OK = False

class _Logger:
    """تسجيل المحادثات في PostgreSQL — غير متزامن، لا يؤثر على الأداء"""
    _inst = None

    def __init__(self):
        self._conn = None
        self._lock = threading.Lock()
        self._cfg = {
            "host":     _os.getenv("POSTGRES_HOST",     "postgres"),
            "port":     int(_os.getenv("POSTGRES_PORT", "5432")),
            "dbname":   _os.getenv("POSTGRES_DB",       "salehsaas"),
            "user":     _os.getenv("POSTGRES_USER",     "salehsaas"),
            "password": _os.getenv("POSTGRES_PASSWORD", "salehsaas_pass"),
            "connect_timeout": 3,
        }

    @classmethod
    def get(cls):
        if cls._inst is None:
            cls._inst = cls()
        return cls._inst

    def _conn_ok(self):
        if not _PG_OK: return None
        try:
            if self._conn is None or self._conn.closed:
                self._conn = _pg.connect(**self._cfg)
                self._conn.autocommit = True
            return self._conn
        except Exception as e:
            print(f"[Logger] DB error: {e}")
            self._conn = None
            return None

    def log(self, *, user_message, assistant_reply, expert_domain, model_used,
            prompt_version="2.1.0", rag_used=False, rag_docs=None,
            response_time_ms=None, tokens_used=None, extra=None):
        if not _PG_OK: return
        rag_score_avg = None
        if rag_docs:
            scores = [d.get("score", 0) for d in rag_docs if "score" in d]
            if scores: rag_score_avg = round(sum(scores)/len(scores), 4)
        if tokens_used is None:
            tokens_used = (len(user_message) + len(assistant_reply)) // 4
        rid = str(_uuid.uuid4())
        threading.Thread(target=self._insert, daemon=True, args=(
            rid, user_message, assistant_reply, expert_domain, model_used,
            prompt_version, rag_used, rag_docs, rag_score_avg,
            response_time_ms, tokens_used, extra,
        )).start()

    def _insert(self, rid, user_message, assistant_reply, expert_domain, model_used,
                prompt_version, rag_used, rag_docs, rag_score_avg,
                response_time_ms, tokens_used, extra):
        with self._lock:
            conn = self._conn_ok()
            if conn is None: return
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO conversation_logs (
                            id, user_message, assistant_reply,
                            expert_domain, model_used, prompt_version,
                            rag_used, rag_docs, rag_score_avg,
                            response_time_ms, tokens_used, extra
                        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """, (
                        rid, user_message[:10000], assistant_reply[:20000],
                        expert_domain, model_used, prompt_version,
                        rag_used, _json.dumps(rag_docs or []),
                        rag_score_avg, response_time_ms, tokens_used,
                        _json.dumps(extra or {}),
                    ))
            except Exception as e:
                print(f"[Logger] Insert error: {e}")
                self._conn = None

class _Timer:
    def __init__(self): self._s = time.monotonic()
    def ms(self): return int((time.monotonic() - self._s) * 1000)
# ─────────────────────────────────────────────────────────────────────────────
"""
Orchestrator Pipeline v2.1.0 — SaleHSaaS
Routes to the right expert automatically
Models: qwen2.5:7b (routing+general) | deepseek-r1:7b (n8n+cybersecurity)
"""
from pydantic import BaseModel
import requests, json

EXPERT_PROMPTS = {
    "n8n": """أنت خبير أتمتة n8n في SaleHSaaS. تصمّم Workflows وتشخّص الأخطاء وتدير Ollama.
بيئة العمل: n8n:5678 | open-webui:8080 | ollama:11434 | n8n_bridge:3333/v1/ | chromadb:8000 | postgres:5432
أجب بالعربية، JSON في كتلة ```json، اذكر typeVersion الصحيح دائماً.""",

    "legal": """أنت مستشار قانوني متخصص في الأنظمة السعودية (نظام العمل، PDPL، نظام الشركات، VAT).
استند دائماً إلى النص القانوني واذكر رقم المادة. نبّه أن هذه مشورة عامة وليست استشارة رسمية.""",

    "financial": """أنت خبير مالي ومحاسبي في البيئة السعودية (SOCPA، ZATCA، VAT 15%، IFRS).
تحقق من كل حساب، اذكر المعيار المستند إليه.""",

    "hr": """أنت خبير موارد بشرية متخصص في نظام العمل السعودي (GOSI، نطاقات، مكافأة نهاية الخدمة).
اذكر المادة القانونية، تحقق من حسابات الرواتب.""",

    "cybersecurity": """أنت خبير أمن سيبراني متخصص في المعايير السعودية والدولية (NCA-ECC، ISO 27001، OWASP).
فكّر خطوة بخطوة، صنّف المخاطر، اذكر رقم الضابط المرجعي.""",

    "social_media": """أنت خبير تسويق رقمي للسوق السعودي والخليجي (LinkedIn، X، Instagram، TikTok، Snapchat).
احترم القيم الإسلامية، اقترح أفضل أوقات النشر.""",

    "general": """أنت مساعد ذكي متعدد التخصصات في نظام SaleHSaaS للأعمال السعودية.
أجب بشكل شامل ودقيق، وأحِل للمتخصص المناسب عند الحاجة.""",
}

ROUTING_PROMPT = """Classify the user query into exactly one domain:
n8n | legal | financial | hr | cybersecurity | social_media | general

Rules:
- n8n: automation, workflow, n8n, API, Docker, Ollama, integration
- legal: law, regulation, contract, compliance, PDPL, labor law
- financial: finance, accounting, tax, VAT, zakat, budget, ZATCA
- hr: human resources, salary, leave, employment, GOSI, nitaqat
- cybersecurity: security, vulnerability, NCA, ISO 27001, OWASP, encryption
- social_media: content, platform, marketing, LinkedIn, Instagram, hashtag
- general: anything else

Respond with ONE word only."""

COLLECTION_MAP = {
    "n8n":           "n8n_knowledge",
    "legal":         "saleh_legal_knowledge",
    "financial":     "financial_knowledge",
    "hr":            "hr_knowledge",
    "cybersecurity": "cybersecurity_knowledge",
    "social_media":  "social_media_knowledge",
    "general":       "general_knowledge",
}
REASONING_DOMAINS = {"n8n", "cybersecurity"}

class Pipeline:
    DOMAIN = "orchestrator"

    class Valves(BaseModel):
        OLLAMA_BASE_URL:  str   = "http://host.docker.internal:11434"
        ROUTING_MODEL:    str   = "qwen2.5:7b"
        DEFAULT_MODEL:    str   = "qwen2.5:7b"
        REASONING_MODEL:  str   = "deepseek-r1:7b"
        TEMPERATURE:      float = 0.3
        MAX_TOKENS:       int   = 4096
        TIMEOUT:          int   = 300
        ENABLE_RAG:       bool  = True
        CHROMADB_URL:     str   = "http://chromadb:8000"
        EMBEDDING_MODEL:  str   = "nomic-embed-text:latest"
        RAG_TOP_K:        int   = 5
        RAG_MIN_SCORE:    float = 0.25
        SHOW_ROUTING:     bool  = True
        PROMPT_VERSION:   str   = "2.1.0"

    def __init__(self):
        self.name   = "🎯 SaleHSaaS Orchestrator"
        self.id     = "orchestrator"
        self.valves = self.Valves()

    async def on_startup(self):
        print(f"[Orchestrator v2.1.0] Ready | Routing: {self.valves.ROUTING_MODEL}")

    async def on_shutdown(self):
        print("[Orchestrator v2.1.0] Shutdown")

    def _route(self, user_message: str) -> str:
        try:
            r = requests.post(
                f"{self.valves.OLLAMA_BASE_URL}/api/chat",
                json={
                    "model": self.valves.ROUTING_MODEL,
                    "messages": [
                        {"role": "system", "content": ROUTING_PROMPT},
                        {"role": "user",   "content": user_message[:500]},
                    ],
                    "stream": False,
                    "options": {"temperature": 0.0, "num_predict": 10},
                },
                timeout=30,
            )
            r.raise_for_status()
            domain = r.json().get("message", {}).get("content", "general").strip().lower()
            for key in EXPERT_PROMPTS:
                if key in domain:
                    return key
            return "general"
        except Exception as e:
            print(f"[Orchestrator] Routing error: {e}")
            return "general"

    def _get_embedding(self, text: str):
        try:
            r = requests.post(
                f"{self.valves.OLLAMA_BASE_URL}/api/embeddings",
                json={"model": self.valves.EMBEDDING_MODEL, "prompt": text[:2000]},
                timeout=30,
            )
            r.raise_for_status()
            return r.json().get("embedding")
        except Exception:
            return None

    def _retrieve_context(self, query: str, collection: str):
        if not self.valves.ENABLE_RAG:
            return "", []
        embedding = self._get_embedding(query)
        if not embedding:
            return "", []
        try:
            r = requests.post(
                f"{self.valves.CHROMADB_URL}/api/v2/tenants/default_tenant"
                f"/databases/default_database/collections/{collection}/query",
                json={
                    "query_embeddings": [embedding],
                    "n_results": self.valves.RAG_TOP_K,
                    "include": ["documents", "metadatas", "distances"],
                },
                timeout=15,
            )
            if r.status_code != 200:
                return "", []
            data      = r.json()
            docs      = data.get("documents", [[]])[0]
            metas     = data.get("metadatas", [[]])[0]
            distances = data.get("distances", [[]])[0]
            relevant_text, rag_docs_meta = [], []
            for doc, meta, dist in zip(docs, metas, distances):
                score = round(1 - dist, 4)
                if score >= self.valves.RAG_MIN_SCORE:
                    source = (meta or {}).get("source", "unknown")
                    relevant_text.append(f"[Source: {source}]\n{doc}")
                    rag_docs_meta.append({"source": source, "score": score, "snippet": doc[:200]})
            return "\n\n---\n\n".join(relevant_text), rag_docs_meta
        except Exception:
            return "", []

    def pipe(self, user_message: str, model_id: str, messages: list, body: dict):
        timer  = _Timer()
        logger = _Logger.get()

        domain     = self._route(user_message)
        model      = self.valves.REASONING_MODEL if domain in REASONING_DOMAINS else self.valves.DEFAULT_MODEL
        collection = COLLECTION_MAP.get(domain, "general_knowledge")
        sys_prompt = EXPERT_PROMPTS.get(domain, EXPERT_PROMPTS["general"])

        rag_context, rag_docs_meta = self._retrieve_context(user_message, collection)

        enriched = list(messages)
        if not any(m.get("role") == "system" for m in enriched):
            enriched = [{"role": "system", "content": sys_prompt}] + enriched
        if rag_context:
            rag_msg = {
                "role": "system",
                "content": f"## Retrieved Knowledge\n\n{rag_context}\n\n---\nUse as primary reference.",
            }
            if enriched and enriched[-1].get("role") == "user":
                enriched = enriched[:-1] + [rag_msg] + [enriched[-1]]
            else:
                enriched.append(rag_msg)

        routing_suffix = (
            f"\n\n---\n*Domain: **{domain.upper()}** | Model: `{model}`*"
            if self.valves.SHOW_ROUTING else ""
        )

        stream  = body.get("stream", False)
        payload = {
            "model": model,
            "messages": enriched,
            "stream": stream,
            "options": {
                "temperature": body.get("temperature", self.valves.TEMPERATURE),
                "num_predict": body.get("max_tokens", self.valves.MAX_TOKENS),
            },
        }

        try:
            r = requests.post(
                f"{self.valves.OLLAMA_BASE_URL}/api/chat",
                json=payload, timeout=self.valves.TIMEOUT, stream=stream,
            )
            r.raise_for_status()

            if stream:
                def _stream():
                    full_reply = []
                    for line in r.iter_lines():
                        if not line: continue
                        try:
                            chunk   = json.loads(line)
                            content = chunk.get("message", {}).get("content", "")
                            if content:
                                full_reply.append(content)
                                yield content
                            if chunk.get("done"):
                                if routing_suffix:
                                    yield routing_suffix
                                logger.log(
                                    user_message=user_message,
                                    assistant_reply="".join(full_reply),
                                    expert_domain=domain,
                                    model_used=model,
                                    prompt_version=self.valves.PROMPT_VERSION,
                                    rag_used=bool(rag_docs_meta),
                                    rag_docs=rag_docs_meta,
                                    response_time_ms=timer.ms(),
                                    extra={"routed_by": "orchestrator"},
                                )
                                break
                        except json.JSONDecodeError:
                            pass
                return _stream()
            else:
                reply = r.json().get("message", {}).get("content", "No response.")
                logger.log(
                    user_message=user_message,
                    assistant_reply=reply,
                    expert_domain=domain,
                    model_used=model,
                    prompt_version=self.valves.PROMPT_VERSION,
                    rag_used=bool(rag_docs_meta),
                    rag_docs=rag_docs_meta,
                    response_time_ms=timer.ms(),
                    extra={"routed_by": "orchestrator"},
                )
                return reply + routing_suffix

        except requests.exceptions.ConnectionError:
            return f"Connection error: Cannot reach Ollama at {self.valves.OLLAMA_BASE_URL}"
        except requests.exceptions.Timeout:
            return f"Timeout after {self.valves.TIMEOUT}s"
        except requests.exceptions.HTTPError as e:
            code = e.response.status_code
            if code == 404:
                return f"Model not found: {model}. Run: ollama pull {model}"
            return f"HTTP error {code}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"
