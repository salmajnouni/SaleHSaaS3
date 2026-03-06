"""
HR Expert Pipeline v2.1.0
Model: qwen2.5:7b | VRAM: 4.7GB (GTX 1660 Ti OK)
RAG: hr_knowledge | Logging: PostgreSQL conversation_logs
"""
from typing import Generator, Iterator
from pydantic import BaseModel
import requests, json

class Pipeline:
    DOMAIN = "hr"

    class Valves(BaseModel):
        OLLAMA_BASE_URL:  str   = "http://host.docker.internal:11434"
        MODEL_ID:         str   = "qwen2.5:7b"
        TEMPERATURE:      float = 0.2
        MAX_TOKENS:       int   = 4096
        TIMEOUT:          int   = 300
        ENABLE_RAG:       bool  = True
        CHROMADB_URL:     str   = "http://chromadb:8000"
        EMBEDDING_MODEL:  str   = "nomic-embed-text:latest"
        RAG_COLLECTION:   str   = "hr_knowledge"
        RAG_TOP_K:        int   = 5
        RAG_MIN_SCORE:    float = 0.25
        PROMPT_VERSION:   str   = "2.1.0"

    SYSTEM_PROMPT = """## الهوية والدور
أنت **خبير موارد بشرية** متخصص في البيئة السعودية ضمن نظام SaleHSaaS.

## نطاق الخبرة
| المجال | المراجع |
|--------|---------|
| نظام العمل | نظام العمل السعودي 1426هـ وتعديلاته |
| الرواتب والمزايا | بدل السكن، النقل، العلاوات |
| الإجازات | السنوية، المرضية، الأمومة، الاضطرارية |
| إنهاء الخدمة | مكافأة نهاية الخدمة، الفصل، الاستقالة |
| التأمينات | GOSI، التأمين الصحي، التأمين ضد التعطل |
| السعودة | نظام نطاقات، متطلبات التوطين |
| التدريب | HRDF، برامج التدريب المدعومة |

## قواعد الإجابة الإلزامية
1. اذكر المادة القانونية أو اللائحة عند الإجابة على أسئلة قانونية
2. تحقق من حسابات الرواتب ومكافآت نهاية الخدمة بدقة
3. وضّح الفرق بين القطاع الحكومي والخاص عند الاقتضاء
4. نبّه إذا كانت اللوائح قد تغيّرت مؤخراً
5. عند استخدام وثيقة مسترجعة: اذكر [المصدر: ...]

## تنسيق الإجابة
**الإجابة**: [ملخص واضح]
**الأساس القانوني**: [نظام العمل، المادة، اللائحة]
**الحساب**: [إذا كان مطلوباً]
**التوصية العملية**: [الخطوات التطبيقية]"""

    def __init__(self):
        self.name   = "👥 HR Management Expert"
        self.id     = "hr-expert"
        self.valves = self.Valves()

    async def on_startup(self):
        print(f"[HR Expert v2.1.0] Model: {self.valves.MODEL_ID}")

    async def on_shutdown(self):
        print("[HR Expert v2.1.0] Shutdown")

    # ── RAG ──────────────────────────────────────────────────────────────────

    def _get_embedding(self, text: str):
        try:
            r = requests.post(
                f"{self.valves.OLLAMA_BASE_URL}/api/embeddings",
                json={"model": self.valves.EMBEDDING_MODEL, "prompt": text[:2000]},
                timeout=30,
            )
            r.raise_for_status()
            return r.json().get("embedding")
        except Exception as e:
            print(f"[{self.name}] Embedding error: {e}")
            return None

    def _retrieve_context(self, query: str):
        """يسترجع الوثائق ذات الصلة من ChromaDB"""
        if not self.valves.ENABLE_RAG:
            return "", []
        embedding = self._get_embedding(query)
        if not embedding:
            return "", []
        try:
            r = requests.post(
                f"{self.valves.CHROMADB_URL}/api/v2/tenants/default_tenant"
                f"/databases/default_database/collections/{self.valves.RAG_COLLECTION}/query",
                json={
                    "query_embeddings": [embedding],
                    "n_results": self.valves.RAG_TOP_K,
                    "include": ["documents", "metadatas", "distances"],
                },
                timeout=15,
            )
            if r.status_code != 200:
                return "", []
            data = r.json()
            docs      = data.get("documents", [[]])[0]
            metas     = data.get("metadatas", [[]])[0]
            distances = data.get("distances", [[]])[0]

            relevant_text = []
            rag_docs_meta = []
            for doc, meta, dist in zip(docs, metas, distances):
                score = round(1 - dist, 4)
                if score >= self.valves.RAG_MIN_SCORE:
                    source = (meta or {}).get("source", "unknown")
                    relevant_text.append(f"[Source: {source}]\n{doc}")
                    rag_docs_meta.append({
                        "source": source,
                        "score":  score,
                        "snippet": doc[:200],
                    })
            return "\n\n---\n\n".join(relevant_text), rag_docs_meta
        except Exception as e:
            print(f"[{self.name}] ChromaDB error: {e}")
            return "", []

    def _build_messages(self, user_message: str, messages: list, system_prompt: str, rag_context: str):
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
        return enriched

    # ── Ollama + Logging ──────────────────────────────────────────────────────

    def _call_ollama(self, messages: list, body: dict, user_message: str, rag_docs_meta: list):
        """يستدعي Ollama ويسجّل النتيجة في PostgreSQL"""
        from conversation_logger import get_logger, Timer
        timer  = Timer()
        logger = get_logger()
        stream = body.get("stream", False)
        payload = {
            "model": self.valves.MODEL_ID,
            "messages": messages,
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
                    full_reply = []
                    for line in r.iter_lines():
                        if not line:
                            continue
                        try:
                            chunk = json.loads(line)
                            content = chunk.get("message", {}).get("content", "")
                            if content:
                                full_reply.append(content)
                                yield content
                            if chunk.get("done"):
                                # تسجيل بعد اكتمال الـ stream
                                logger.log(
                                    user_message=user_message,
                                    assistant_reply="".join(full_reply),
                                    expert_domain=self.DOMAIN,
                                    model_used=self.valves.MODEL_ID,
                                    prompt_version=self.valves.PROMPT_VERSION,
                                    rag_used=bool(rag_docs_meta),
                                    rag_docs=rag_docs_meta,
                                    response_time_ms=timer.elapsed_ms(),
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
                    expert_domain=self.DOMAIN,
                    model_used=self.valves.MODEL_ID,
                    prompt_version=self.valves.PROMPT_VERSION,
                    rag_used=bool(rag_docs_meta),
                    rag_docs=rag_docs_meta,
                    response_time_ms=timer.elapsed_ms(),
                )
                return reply

        except requests.exceptions.ConnectionError:
            return f"Connection error: Cannot reach Ollama at {self.valves.OLLAMA_BASE_URL}"
        except requests.exceptions.Timeout:
            return f"Timeout after {self.valves.TIMEOUT}s. Try a smaller model."
        except requests.exceptions.HTTPError as e:
            code = e.response.status_code
            if code == 404:
                return f"Model not found: {self.valves.MODEL_ID}. Run: ollama pull {self.valves.MODEL_ID}"
            return f"HTTP error {code}: {e.response.text[:300]}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"

    def pipe(self, user_message: str, model_id: str, messages: list, body: dict):
        rag_context, rag_docs_meta = self._retrieve_context(user_message)
        enriched = self._build_messages(user_message, messages, self.SYSTEM_PROMPT, rag_context)
        return self._call_ollama(enriched, body, user_message, rag_docs_meta)
