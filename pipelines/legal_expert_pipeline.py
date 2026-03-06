"""
Legal Expert Pipeline v2.0.0
Model: qwen2.5:7b | VRAM: 4.7GB (GTX 1660 Ti OK)
RAG: saleh_legal_knowledge collection
Docs: Saudi Labor Law, PDPL, NCA-ECC, Companies Law
"""
from typing import List, Union, Generator, Iterator
from pydantic import BaseModel
import requests, json

class Pipeline:
    class Valves(BaseModel):
        OLLAMA_BASE_URL: str = "http://host.docker.internal:11434"
        MODEL_ID: str = "qwen2.5:7b"
        TEMPERATURE: float = 0.1
        MAX_TOKENS: int = 4096
        TIMEOUT: int = 300
        ENABLE_RAG: bool = True
        CHROMADB_URL: str = "http://chromadb:8000"
        EMBEDDING_MODEL: str = "nomic-embed-text:latest"
        RAG_COLLECTION: str = "saleh_legal_knowledge"
        RAG_TOP_K: int = 7
        RAG_MIN_SCORE: float = 0.3
        PROMPT_VERSION: str = "2.0.0"

    SYSTEM_PROMPT = """## الهوية والدور
أنت **مستشار قانوني متخصص** في الأنظمة والتشريعات السعودية ضمن نظام SaleHSaaS.

## نطاق الخبرة القانونية
| المجال | الأنظمة |
|--------|---------|
| العمل والموارد البشرية | نظام العمل 1426هـ وتعديلاته |
| حماية البيانات | نظام PDPL 1443هـ |
| الأمن السيبراني | ضوابط NCA-ECC |
| الشركات والتجارة | نظام الشركات، التجارة الإلكترونية |
| الضرائب | ضريبة القيمة المضافة، الزكاة |
| مكافحة الفساد | نظام مكافحة الفساد |

## قواعد الإجابة الإلزامية
1. استند دائماً إلى النص القانوني الرسمي — اذكر رقم المادة والنظام
2. لا تفترض أو تخمّن — إذا لم تجد النص، قل ذلك صراحةً
3. رتّب الإجابة: الحكم → المادة → التطبيق العملي
4. نبّه دائماً أن هذه مشورة عامة وليست استشارة رسمية
5. عند استخدام وثيقة مسترجعة: اذكر [المصدر: اسم_النظام - رقم_المادة]

## تنسيق الإجابة
**الحكم القانوني**: [ملخص]
**المستند**: [اسم النظام، المادة، النص الحرفي]
**التطبيق العملي**: [كيفية التطبيق]
**ملاحظات**: [تحفظات أو إحالات]"""

    def __init__(self):
        self.name = "⚖️ Legal Compliance Expert"
        self.id = "legal-expert"
        self.valves = self.Valves()

    async def on_startup(self):
        print(f"[Legal Expert v2.0.0] Model: {self.valves.MODEL_ID}")

    async def on_shutdown(self):
        print("[Legal Expert v2.0.0] Shutdown")

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

    def _retrieve_context(self, query: str) -> str:
        if not self.valves.ENABLE_RAG:
            return ""
        embedding = self._get_embedding(query)
        if not embedding:
            return ""
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
                return ""
            data = r.json()
            docs = data.get("documents", [[]])[0]
            metas = data.get("metadatas", [[]])[0]
            distances = data.get("distances", [[]])[0]
            relevant = []
            for doc, meta, dist in zip(docs, metas, distances):
                score = 1 - dist
                if score >= self.valves.RAG_MIN_SCORE:
                    source = (meta or {}).get("source", "unknown")
                    relevant.append(f"[Source: {source}]\n{doc}")
            return "\n\n---\n\n".join(relevant)
        except Exception as e:
            print(f"[{self.name}] ChromaDB error: {e}")
            return ""

    def _build_messages(self, user_message: str, messages: list, system_prompt: str) -> list:
        enriched = list(messages)
        if not any(m.get("role") == "system" for m in enriched):
            enriched = [{"role": "system", "content": system_prompt}] + enriched
        rag_context = self._retrieve_context(user_message)
        if rag_context:
            rag_msg = {
                "role": "system",
                "content": f"## Retrieved Knowledge\n\n{rag_context}\n\n---\nUse this as primary reference.",
            }
            if enriched and enriched[-1].get("role") == "user":
                enriched = enriched[:-1] + [rag_msg] + [enriched[-1]]
            else:
                enriched.append(rag_msg)
        return enriched

    def _call_ollama(self, messages: list, body: dict):
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
                    for line in r.iter_lines():
                        if not line:
                            continue
                        try:
                            chunk = json.loads(line)
                            content = chunk.get("message", {}).get("content", "")
                            if content:
                                yield content
                            if chunk.get("done"):
                                break
                        except json.JSONDecodeError:
                            pass
                return _stream()
            else:
                return r.json().get("message", {}).get("content", "No response.")
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
        enriched = self._build_messages(user_message, messages, self.SYSTEM_PROMPT)
        return self._call_ollama(enriched, body)
