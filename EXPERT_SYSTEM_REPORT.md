# تقرير النظام الخبير — SaleHSaaS
## مراجعة علمية شاملة: النماذج، RAG، وهندسة البرومبتس

**الإصدار**: 2.0.0 | **التاريخ**: مارس 2026 | **المؤلف**: SaleHSaaS AI Team

---

## 1. تقييم النماذج بناءً على موارد جهازك الفعلية

### مواصفات الجهاز المستهدف

| المكوّن | المواصفة |
|---------|---------|
| المعالج | Intel Core i7-9750H @ 2.60GHz (6 cores / 12 threads) |
| الذاكرة | 32GB DDR4 @ 2667MHz |
| كرت الشاشة | NVIDIA GTX 1660 Ti — **6GB GDDR6 VRAM** |
| التخزين | 2.73TB |

> **القيد الحاسم**: كرت الشاشة GTX 1660 Ti بـ 6GB VRAM هو العامل المحدِّد لاختيار النماذج.

### جدول النماذج المدعومة على GTX 1660 Ti

| النموذج | الحجم | VRAM المطلوب | يعمل؟ | الاستخدام الأمثل |
|---------|-------|-------------|-------|----------------|
| **qwen2.5:7b** | 4.7GB | ✅ 6GB | نعم | RAG، العربية، instruction-following |
| **deepseek-r1:7b** | 4.7GB | ✅ 6GB | نعم | التفكير المنطقي، تحليل الأمن |
| **deepseek-r1:8b** | 4.9GB | ✅ 6GB | نعم | استدلال + تفكير |
| **llama3.1:8b** | 4.9GB | ✅ 6GB | نعم | عام متوازن |
| **mistral:7b** | 4.1GB | ✅ 6GB | نعم | سريع وخفيف |
| **llama3.2:3b** | 2.0GB | ✅ 6GB | نعم | سريع جداً لـ tool calls |
| **nomic-embed-text** | ~0.5GB | ✅ 6GB | نعم | Embeddings للـ RAG |
| gemma2:9b | 5.4GB | ❌ 8GB | لا | يحتاج VRAM أكبر |
| qwen2.5:14b | 9.0GB | ❌ 16GB | لا | يحتاج VRAM أكبر |

**المصدر**: [databasemart.com GPU benchmarks](https://www.databasemart.com/blog/choosing-the-right-gpu-for-popluar-llms-on-ollama) + Reddit r/LocalLLM

### النماذج المختارة لكل Pipeline

| الـ Pipeline | النموذج | السبب العلمي |
|-------------|---------|-------------|
| n8n Expert | **qwen2.5:7b** | context 128K للـ workflows الطويلة + instruction-following ممتاز |
| Legal Expert | **qwen2.5:7b** | أفضل دعم للعربية (29 لغة) + context 128K للوثائق القانونية |
| Financial Expert | **qwen2.5:7b** | دقة عالية في الحسابات + context 128K للتقارير المالية |
| HR Expert | **qwen2.5:7b** | دعم العربية + context 128K لعقود العمل والسياسات |
| Cybersecurity Expert | **deepseek-r1:7b** | chain-of-thought reasoning ضروري لتحليل التهديدات |
| Social Media Expert | **qwen2.5:7b** | أفضل كتابة إبداعية عربية + فهم السياق الثقافي |
| Orchestrator | **qwen2.5:7b** (توجيه) + **deepseek-r1:7b** (أمن/n8n) | توجيه ذكي + نموذج مناسب لكل تخصص |

---

## 2. دور RAG وتخزين المعلومات وتحليلها

### لماذا RAG وليس Fine-tuning؟

> **المرجع**: ExpertRAG (arxiv 2025) — "RAG outperforms fine-tuning when knowledge is dynamic and requires source attribution"

| المعيار | RAG | Fine-tuning |
|---------|-----|------------|
| تحديث المعرفة | فوري (أضف وثيقة) | يحتاج إعادة تدريب |
| تتبع المصادر | نعم (يذكر المصدر) | لا |
| تكلفة التطبيق | منخفضة | عالية جداً |
| حجم البيانات المطلوب | لا حد أدنى | +1000 مثال |
| **حالة SaleHSaaS** | **✅ الأنسب** | ❌ غير مناسب |

### بنية RAG في SaleHSaaS

```
المستخدم
    ↓
[Pipeline Server]
    ↓
1. استخراج نية المستخدم
    ↓
2. تحويل السؤال إلى Embedding (nomic-embed-text)
    ↓
3. البحث في ChromaDB (Cosine Similarity)
    ↓
4. استرجاع أكثر 5-7 وثائق صلة (TOP_K)
    ↓
5. حقن السياق في System Prompt
    ↓
6. استدعاء Ollama مع السياق الكامل
    ↓
الإجابة المستندة إلى المصادر
```

### Collections في ChromaDB

| Collection | المحتوى | الـ Pipeline |
|-----------|---------|------------|
| `n8n_knowledge` | وثائق n8n، workflows محفوظة، أمثلة | n8n Expert |
| `saleh_legal_knowledge` | الأنظمة السعودية، اللوائح، المراسيم | Legal Expert |
| `financial_knowledge` | SOCPA، ZATCA، IFRS، لوائح VAT | Financial Expert |
| `hr_knowledge` | نظام العمل، GOSI، سياسات HR | HR Expert |
| `cybersecurity_knowledge` | NCA-ECC، ISO 27001، OWASP | Cybersecurity Expert |
| `social_media_knowledge` | استراتيجيات المحتوى، بيانات الأداء | Social Media Expert |
| `general_knowledge` | معرفة عامة متنوعة | Orchestrator |

### كيفية إضافة وثائق جديدة إلى RAG

```python
# مثال: إضافة وثيقة قانونية جديدة
import chromadb

client = chromadb.HttpClient(host="localhost", port=8000)
collection = client.get_collection("saleh_legal_knowledge")

collection.add(
    documents=["نص نظام العمل، المادة 80: يحق للعامل..."],
    metadatas=[{
        "source": "نظام_العمل_1426",
        "article": "80",
        "category": "إنهاء_الخدمة",
        "date_added": "2026-03-06"
    }],
    ids=["labor_law_art_80"]
)
```

### تحليل الاستخدام والتحسين المستمر

كل استعلام يُسجَّل مع:
- السؤال الأصلي
- التخصص المُحدَّد
- الوثائق المسترجعة ودرجة الصلة
- النموذج المستخدم
- وقت الاستجابة

هذه البيانات تُستخدم لـ:
1. تحسين معايير الاسترجاع (TOP_K، MIN_SCORE)
2. تحديد الوثائق الأكثر استخداماً
3. اكتشاف الفجوات في قاعدة المعرفة
4. قياس جودة الإجابات

---

## 3. هندسة البرومبتس للتطوير المستمر

### البنية العلمية للـ System Prompt

> **المرجع**: Schreiber, White & Schmidt (Vanderbilt 2024) — "A Pattern Language for Persona-based Interactions with LLMs"
> **المرجع**: IEEE 2025 — "The Art and Science of Guiding Generative AI"

كل System Prompt في SaleHSaaS يتبع هذه البنية المثلى:

```
1. Role Definition (الهوية والدور)
   ↓ من أنت؟ ما تخصصك؟ في أي سياق تعمل؟

2. Domain Knowledge (المعرفة المتخصصة)
   ↓ جداول المعايير والأنظمة المرجعية

3. Behavioral Constraints (القيود السلوكية)
   ↓ ماذا تفعل؟ ماذا لا تفعل؟ متى تُحيل؟

4. Output Format (تنسيق المخرجات)
   ↓ كيف تُنسّق الإجابة؟ ما الهيكل المطلوب؟

5. RAG Instructions (تعليمات استخدام السياق)
   ↓ كيف تستخدم الوثائق المسترجعة؟
```

> **تحذير علمي**: ورقة Persona Pattern (Vanderbilt 2024) تُثبت أن "الـ Persona وحدها لا تكفي — يجب دمجها مع Domain Knowledge وOutput Constraints لتحقيق أداء متسق."

### نظام إصدارات البرومبتس (Prompt Versioning)

> **المرجع**: LaunchDarkly 2025 — "Prompt Versioning and Management Guide"
> **المرجع**: LangWatch 2026 — "What is Prompt Management?"

كل Pipeline تحمل رقم إصدار (`PROMPT_VERSION`) في الـ Valves:

```python
class Valves(BaseModel):
    PROMPT_VERSION: str = "2.0.0"  # Major.Minor.Patch
```

**قواعد الإصدار**:
- **Major** (1.x → 2.x): تغيير جذري في البنية أو الدور
- **Minor** (x.1 → x.2): إضافة قدرة جديدة أو تخصص
- **Patch** (x.x.1 → x.x.2): تحسين صياغة أو تصحيح خطأ

**سجل التغييرات**:
```
v1.0.0: System prompt أساسي — role فقط
v1.1.0: إضافة بيئة Docker Compose الكاملة
v2.0.0: إضافة RAG + Domain Knowledge جداول + Output Format محدد
```

### درجة الحرارة (Temperature) حسب التخصص

| التخصص | Temperature | السبب |
|--------|------------|-------|
| Legal Expert | **0.1** | النصوص القانونية لا تقبل الإبداع |
| Financial Expert | **0.15** | الأرقام تحتاج دقة قصوى |
| Cybersecurity Expert | **0.1** | التحليل الأمني يحتاج تفكيراً محدداً |
| HR Expert | **0.2** | توازن بين الدقة والمرونة |
| n8n Expert | **0.2** | JSON يحتاج دقة مع بعض المرونة |
| Social Media Expert | **0.7** | الإبداع مطلوب في صياغة المحتوى |
| Orchestrator | **0.3** | توازن عام |

---

## 4. خارطة طريق التطوير المستمر

### المرحلة الحالية (v2.0.0) — مكتملة ✅

- [x] 7 Pipelines مع RAG وبرومبتس احترافية
- [x] نماذج مختارة علمياً بناءً على موارد الجهاز
- [x] ChromaDB collections لكل تخصص
- [x] Orchestrator ذكي مع توجيه تلقائي
- [x] نظام إصدارات للبرومبتس

### المرحلة القادمة (v2.1.0) — مقترحة

- [ ] **Prompt Evaluation**: اختبار A/B للبرومبتس المختلفة
- [ ] **Query Logging**: تسجيل كل استعلام في PostgreSQL للتحليل
- [ ] **Feedback Loop**: تقييم المستخدم لجودة الإجابات (👍/👎)
- [ ] **Knowledge Ingestion**: pipeline تلقائي لاستيعاب وثائق جديدة

### المرحلة المستقبلية (v3.0.0) — مخططة

- [ ] **LoRA Fine-tuning**: تدريب مخصص على بيانات SaleHSaaS
- [ ] **Agentic RAG**: الوكيل يقرر متى يبحث ومتى يستخدم ذاكرته
- [ ] **Multi-modal**: دعم الصور والمستندات المرئية
- [ ] **Evaluation Framework**: قياس دقيق لجودة كل Pipeline

---

## 5. دليل التثبيت السريع

### الخطوة 1: سحب التحديثات

```powershell
cd D:\SaleHSaaS3
git pull origin salehsaas5
```

### الخطوة 2: تحميل النماذج في Ollama

```powershell
# النموذج الأساسي (للـ 6 Pipelines)
ollama pull qwen2.5:7b

# نموذج التفكير (للأمن السيبراني والـ n8n المعقد)
ollama pull deepseek-r1:7b

# نموذج الـ Embeddings للـ RAG
ollama pull nomic-embed-text
```

### الخطوة 3: تشغيل المنظومة

```powershell
cd D:\SaleHSaaS3
docker compose up -d
```

### الخطوة 4: رفع الـ Pipelines في Open WebUI

1. افتح `http://localhost:8080`
2. اذهب إلى **Admin Panel > Settings > Connections**
3. أضف `http://pipelines:9099` في حقل Pipelines
4. اذهب إلى **Admin Panel > Settings > Pipelines**
5. ارفع الملفات السبعة من مجلد `pipelines/`

### الخطوة 5: التحقق من عمل RAG

```bash
# التحقق من ChromaDB
curl http://localhost:8000/api/v2/heartbeat

# التحقق من الـ collections
curl http://localhost:8000/api/v2/tenants/default_tenant/databases/default_database/collections
```

---

## 6. استكشاف الأخطاء وإصلاحها

| المشكلة | السبب المحتمل | الحل |
|---------|--------------|------|
| النموذج لا يستجيب | Ollama لم يُشغَّل | `ollama serve` أو تحقق من Docker |
| خطأ 404 | النموذج غير محمّل | `ollama pull qwen2.5:7b` |
| RAG لا يعمل | ChromaDB غير متصل | تحقق من `docker compose ps` |
| بطء شديد | النموذج يعمل على CPU | تحقق من تشغيل Ollama مع CUDA |
| VRAM ممتلئ | نموذجان يعملان معاً | أوقف نموذجاً قبل تشغيل آخر |

### تحقق من استخدام GPU

```bash
# في PowerShell على جهازك
nvidia-smi

# أو في Ollama
curl http://localhost:11434/api/ps
```

---

*هذا التقرير مبني على: databasemart.com GPU benchmarks، Reddit r/LocalLLaMA، arxiv ExpertRAG 2025، Vanderbilt 2024 Persona Pattern، IEEE 2025 Prompt Engineering، LaunchDarkly 2025 Prompt Versioning*
