"""
Orchestrator Pipeline v2.0.0
Architecture: Intent Classification → Expert Routing → Specialized Response
Models: qwen2.5:7b (routing + general) | deepseek-r1:7b (n8n + cybersecurity)
VRAM: 4.7GB max (GTX 1660 Ti OK)
"""
from typing import List, Union, Generator, Iterator
from pydantic import BaseModel
import requests, json

EXPERT_PROMPTS = {
    "n8n": """أنت خبير أتمتة n8n في SaleHSaaS. تصمّم Workflows وتشخّص الأخطاء وتدير Ollama.
بيئة العمل: n8n:5678 | open-webui:8080 | ollama:11434 | n8n_bridge:3333/v1/ | chromadb:8000
أجب بالعربية، JSON في كتلة ```json، اذكر typeVersion الصحيح دائماً.""",

    "legal": """أنت مستشار قانوني متخصص في الأنظمة السعودية (نظام العمل، PDPL، نظام الشركات، VAT).
استند دائماً إلى النص القانوني واذكر رقم المادة. نبّه أن هذه مشورة عامة وليست استشارة رسمية.""",

    "financial": """أنت خبير مالي ومحاسبي في البيئة السعودية (SOCPA، ZATCA، VAT 15%، IFRS).
تحقق من كل حساب، اذكر المعيار المستند إليه، وضّح الفرق بين المشورة العامة والاستشارة الرسمية.""",

    "hr": """أنت خبير موارد بشرية متخصص في نظام العمل السعودي (GOSI، نطاقات، مكافأة نهاية الخدمة).
اذكر المادة القانونية، تحقق من حسابات الرواتب، وضّح الفرق بين القطاع الحكومي والخاص.""",

    "cybersecurity": """أنت خبير أمن سيبراني متخصص في المعايير السعودية والدولية (NCA-ECC، ISO 27001، OWASP).
فكّر خطوة بخطوة، صنّف المخاطر، اذكر رقم الضابط المرجعي، لا تقدّم أدوات اختراق غير مصرح به.""",

    "social_media": """أنت خبير تسويق رقمي للسوق السعودي والخليجي (LinkedIn، X، Instagram، TikTok، Snapchat).
احترم القيم الإسلامية، اقترح أفضل أوقات النشر، قدّم هاشتاقات مناسبة.""",

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
    "n8n": "n8n_knowledge",
    "legal": "saleh_legal_knowledge",
    "financial": "financial_knowledge",
    "hr": "hr_knowledge",
    "cybersecurity": "cybersecurity_knowledge",
    "social_media": "social_media_knowledge",
    "general": "general_knowledge",
}

REASONING_DOMAINS = {"n8n", "cybersecurity"}

class Pipeline:
    class Valves(BaseModel):
        OLLAMA_BASE_URL: str = "http://host.docker.internal:11434"
        ROUTING_MODEL: str = "qwen2.5:7b"
        DEFAULT_MODEL: str = "qwen2.5:7b"
        REASONING_MODEL: str = "deepseek-r1:7b"
        TEMPERATURE: float = 0.3
        MAX_TOKENS: int = 4096
        TIMEOUT: int = 300
        ENABLE_RAG: bool = True
        CHROMADB_URL: str = "http://chromadb:8000"
        EMBEDDING_MODEL: str = "nomic-embed-text:latest"
        RAG_TOP_K: int = 5
        RAG_MIN_SCORE: float = 0.25
        SHOW_ROUTING: bool = True
        PROMPT_VERSION: str = "2.0.0"

    def __init__(self):
        self.name = "🎯 SaleHSaaS Orchestrator"
        self.id = "orchestrator"
        self.valves = self.Valves()

    async def on_startup(self):
        print(f"[Orchestrator v2.0.0] Ready | Routing: {self.valves.ROUTING_MODEL}")

    async def on_shutdown(self):
        print("[Orchestrator v2.0.0] Shutdown")

    def _route(self, user_message: str) -> str:
        try:
            r = requests.post(
                f"{self.valves.OLLAMA_BASE_URL}/api/chat",
                json={
                    "model": self.valves.ROUTING_MODEL,
                    "messages": [
                        {"role": "system", "content": ROUTING_PROMPT},
                        {"role": "user", "content": user_message[:500]},
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

    def _retrieve_context(self, query: str, collection: str) -> str:
        if not self.valves.ENABLE_RAG:
            return ""
        embedding = self._get_embedding(query)
        if not embedding:
            return ""
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
                return ""
            data = r.json()
            docs = data.get("documents", [[]])[0]
            metas = data.get("metadatas", [[]])[0]
            distances = data.get("distances", [[]])[0]
            relevant = []
            for doc, meta, dist in zip(docs, metas, distances):
                if (1 - dist) >= self.valves.RAG_MIN_SCORE:
                    source = (meta or {}).get("source", "unknown")
                    relevant.append(f"[Source: {source}]\n{doc}")
            return "\n\n---\n\n".join(relevant)
        except Exception:
            return ""

    def pipe(self, user_message: str, model_id: str, messages: list, body: dict):
        domain = self._route(user_message)
        system_prompt = EXPERT_PROMPTS.get(domain, EXPERT_PROMPTS["general"])
        model = self.valves.REASONING_MODEL if domain in REASONING_DOMAINS else self.valves.DEFAULT_MODEL
        collection = COLLECTION_MAP.get(domain, "general_knowledge")
        rag_context = self._retrieve_context(user_message, collection)

        enriched = list(messages)
        if not any(m.get("role") == "system" for m in enriched):
            enriched = [{"role": "system", "content": system_prompt}] + enriched

        if rag_context:
            rag_msg = {
                "role": "system",
                "content": f"## Retrieved Knowledge\n\n{rag_context}\n\n---\nUse as primary reference.",
            }
            if enriched and enriched[-1].get("role") == "user":
                enriched = enriched[:-1] + [rag_msg] + [enriched[-1]]
            else:
                enriched.append(rag_msg)

        routing_suffix = f"\n\n---\n*🎯 Domain: **{domain.upper()}** | Model: `{model}`*" if self.valves.SHOW_ROUTING else ""

        stream = body.get("stream", False)
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
                json=payload,
                timeout=self.valves.TIMEOUT,
                stream=stream,
            )
            r.raise_for_status()
            if stream:
                def _stream():
                    for line in r.iter_lines():
                        if not line:
                            continue
                        try:
                            chunk = json.loads(line)
                            content = chunk.get("message", {}).get("content", "")
                            if content:
                                yield content
                            if chunk.get("done"):
                                if routing_suffix:
                                    yield routing_suffix
                                break
                        except json.JSONDecodeError:
                            pass
                return _stream()
            else:
                content = r.json().get("message", {}).get("content", "No response.")
                return content + routing_suffix
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
