# SaleH SaaS 4.0 — المخطط المعماري

## نظرة عامة على البنية

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Windows Host                                  │
│  ┌─────────────┐                                                     │
│  │   Ollama    │  :11434  (LLM + Embeddings)                        │
│  └─────────────┘                                                     │
│         │ host.docker.internal                                       │
│  ┌──────┴──────────────────────────────────────────────────────┐    │
│  │              Docker Network: salehsaas_net                   │    │
│  │              Subnet: 172.20.0.0/16                           │    │
│  │                                                               │    │
│  │  Open WebUI :3000    PostgreSQL :5432    ChromaDB :8010      │    │
│  │  172.20.0.30         172.20.0.10         172.20.0.20         │    │
│  │                                                               │    │
│  │  Pipelines :9099     Apache Tika :9998   SearXNG :8080       │    │
│  │  172.20.0.31         172.20.0.32         172.20.0.33         │    │
│  │                                                               │    │
│  │  n8n :5678           Data Pipeline :8001 Open Terminal :8000 │    │
│  │  172.20.0.40         172.20.0.62         172.20.0.80         │    │
│  │                                                               │    │
│  │  Knowledge Watcher      Browserless :3001                     │    │
│  │  172.20.0.61            172.20.0.70                           │    │
│  └──────────────────────────────────────────────────────────────┘    │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │              WSL2 Ubuntu-22.04 — Training Subsystem           │    │
│  │                                                               │    │
│  │  autoresearch (/home/saleh/autoresearch)                      │    │
│  │    └─ train_cpu.py (GPT ~11.5M params, AMD ROCm 6.3)        │    │
│  │    └─ checkpoints/ (periodic + final.pt)                      │    │
│  │                                                               │    │
│  │  sanirejal API :8500                                          │    │
│  │    └─ /health /status /logs /gpu /config                      │    │
│  │    └─ /train/start /train/stop                                │    │
│  │                                                               │    │
│  │  GPU: AMD Radeon 8060S (ROCm 6.3, librocdxg WSL2 DXG)       │    │
│  └──────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

## مسار الحقيقة التشغيلية (إلزامي)

عند أي تعارض بين المعمار الموصوف والواقع التشغيلي، الترتيب الحاكم هو:

1. `docker-compose.yml`
2. `RUNTIME_STATUS_CARD.md`
3. `الحقائق التشغيلية الحاكمة - v0.1.md`
4. `الحقيقة.md`
5. `logs/ops_journal.jsonl` (أثر التنفيذ الفعلي المستمر)

---

## تدفق استيعاب الوثائق (Knowledge Watcher v3.0)

```
knowledge_inbox/
      │
      │ (كل 10 ثوانٍ)
      ▼
Knowledge Watcher (172.20.0.61)
      │
      ├──► Apache Tika :9998  ──► استخراج النص (1000+ صيغة)
      │
      ├──► Ollama :11434      ──► توليد التضمينات (qwen3-embedding:0.6b)
      │         (timeout: 300s)
      │
      ├──► ChromaDB :8000     ──► تخزين chunks + embeddings
      │         (API v1: /api/v1/...)
      │         (Collection: saleh_knowledge_qwen3)
      │
      ├──► knowledge_processed/           (نجاح)
      │
      └──► knowledge_failed/              (فشل + تقرير .txt)
```

---

## تدفق المحادثة (RAG Pipeline)

```
المستخدم (Open WebUI :3000)
      │
      ▼
Open WebUI
      │
      ├──► Pipelines :9099 (saleh_legal_pipeline.py)
      │         │
      │         ├──► Legal Glossary (حقن تعريفات المصطلحات)
      │         └──► saleh_legal_rag.py
      │                   │
      │                   └──► ChromaDB :8000 (بحث دلالي)
      │
      ├──► Ollama :11434 (توليد الإجابة - llama3.1 أو غيره)
      │
      └──► SearXNG :8080 (بحث الإنترنت - اختياري)
```

---

## تدفق التدريب والمعرفة (Training ↔ RAG)

```
WSL2 Ubuntu-22.04
      │
      ├──► autoresearch/train_cpu.py
      │         │
      │         ├──► GPU (AMD Radeon 8060S, ROCm 6.3)
      │         │         └──► checkpoints/ (كل 1000 خطوة + final.pt)
      │         │
      │         └──► sanirejal API :8500 (مراقبة وتحكم)
      │                   │
      │                   └──► Open WebUI :3000 (Tool مسجلة على Evo2)
      │
      ├──► researchai/rag_docs/ (7 وثائق معرفية)
      │         │
      │         └──► Open WebUI Knowledge Base
      │                   │
      │                   └──► ChromaDB (فهرسة + بحث دلالي)
      │
      └──► Cline (VS Code)
                │
                └──► Evo2 عبر OpenAI-compatible API :3000
```

---

## أدوات MCP المرجعية خارج التشغيل الحالي

```
ملفات MCP موجودة داخل المستودع كأدوات مرجعية وتكاملية،
لكن لا توجد خدمة `mcpo` مفعلة ضمن `docker-compose.yml` الحالي.
كما أن مسار `mcpo` ملغي حاليًا في هذا المشروع ولا يُعتمد للتشغيل.
وأي مواد تاريخية مرتبطة به لا يجوز التعامل معها كجزء من التشغيل الحي.

بالتالي لا يجوز لأي وكيل أن يفترض توفر endpoint حي على المنفذ 8020
إلا بعد التحقق من تشغيل خدمة مستقلة لهذا الغرض.
```

---

## الخدمات والمسؤوليات

| الخدمة | IP | المنفذ | المسؤولية |
|---|---|---|---|
| `open_webui` | `172.20.0.30` | `3000` | واجهة المستخدم، RAG، إدارة الوثائق |
| `postgres` | `172.20.0.10` | `5432` | بيانات Open WebUI و n8n |
| `chromadb` | `172.20.0.20` | `8010` | تخزين التضمينات والبحث الدلالي |
| `tika` | `172.20.0.32` | `9998` | استخراج النص من 1000+ صيغة |
| `pipelines` | `172.20.0.31` | `9099` | معالجة RAG القانونية المخصصة |
| `searxng` | `172.20.0.33` | `8080` | بحث الإنترنت المحلي |
| `n8n` | `172.20.0.40` | `5678` | أتمتة سير العمل |
| `knowledge_watcher` | `172.20.0.61` | داخلي | مراقبة inbox وإدخال الوثائق |
| `data_pipeline` | `172.20.0.62` | `8001` | استقبال الملفات، التقطيع، والتخزين في ChromaDB |
| `browserless` | `172.20.0.70` | `3001` | متصفح آلي لخدمات تحتاج تنفيذًا متصفحياً |
| `open-terminal` | `172.20.0.80` | `8000` | بيئة طرفية داخلية مرتبطة بالمجلد المحلي `saleh/` |

---

## حقائق تشغيلية معتمدة للوكلاء

- ChromaDB العاملة حاليًا هي `chromadb/chroma:0.5.3` وتُستخدم عبر واجهات `v1` في المسارات الحية.
- اسم مجموعة المعرفة الحية المعتمد في البحث القانوني والاستيعاب الحالي هو `saleh_knowledge_qwen3`.
- نموذج التضمين المعتمد حاليًا هو `qwen3-embedding:0.6b`، وأبعاده `1024`.
- أي تعارض أبعاد بين النموذج والمجموعة (مثل استخدام 768-dim مع مجموعة 1024-dim) يؤدي إلى فشل أو تدهور البحث الدلالي.
- خدمة `knowledge_watcher` تنقل الملفات الناجحة إلى `knowledge_processed/`، والفاشلة إلى `knowledge_failed/`.
- خدمة `knowledge_watcher` الحية الحالية تُبنى من المجلد `file_watcher/`، والملف التنفيذي المعتمد هو `file_watcher/watcher.py`.
- المجلد `knowledge_processing/` ليس جزءًا من مسار النجاح الحي الحالي، ويجب عدم اعتباره وجهة تشغيلية نهائية ما لم يتغير الكود و`docker-compose.yml`.
- المجلد `knowledge_archive/` ليس وجهة النجاح الحي لـ watcher، لكنه ما زال مستخدمًا لأرشفة بعض المصادر المرجعية مثل مخرجات `scripts/uqn_scraper.py` تحت `knowledge_archive/uqn/`.
- المجلد `saleh_dashboard/` موجود داخل المستودع كمشروع Dashboard قديم/مرجعي، لكنه ليس خدمة مفعلة ضمن `docker-compose.yml` الحالي ولا يجوز اعتباره الواجهة الحية للمستخدم.
- خدمة `data_pipeline` هي المسار التنفيذي الفعلي لاستيعاب الملفات على المنفذ `8001`.
- لا يجوز افتراض أن `mcpo` جزء من التشغيل الحالي؛ هذا المسار ملغي حاليًا.
- لا يجوز افتراض أن `code_server` جزء من التشغيل الحالي ما لم تتم إضافته صراحة إلى `docker-compose.yml`.

---

## مسارات open-terminal المعتمدة

- المسار `/home/user` داخل حاوية `open-terminal` هو مساحة المنزل الداخلية للحاوية ويُغذى من volume مستقل باسم `open-terminal-data`.
- المجلد المحلي `saleh/` في جذر المشروع ليس هو `home` نفسه، لكنه مربوط داخل الحاوية على المسار `/home/user/projects`.
- أي إشارة تشغيلية من الوكلاء إلى ملفات المشروع داخل بيئة `open-terminal` يجب أن تتعامل مع `/home/user/projects` على أنه المرآة الداخلية للمجلد المحلي `saleh/`.
- لا يجوز نقل أو إعادة تسمية المجلد `saleh/` أو تغيير هذا الربط إلا مع تحديث `docker-compose.yml` والتحقق من خدمة `open-terminal` بعد التعديل.

---

## ChromaDB v1 API — المسارات المستخدمة

```
Base URL: http://chromadb:8000
API Path: /api/v1/

GET    /collections                    → قائمة المجموعات
GET    /collections/{name}             → معلومات المجموعة
POST   /collections/{uuid}/query       → بحث دلالي
```

---

## n8n Public API — المسارات المستخدمة

```
Base URL: http://n8n:5678
Header:   X-N8N-API-KEY: salehsaas-n8n-api-key

GET    /api/v1/workflows               → قائمة الـ workflows
POST   /api/v1/workflows               → إنشاء workflow جديد
PATCH  /api/v1/workflows/{id}          → تحديث workflow
POST   /api/v1/workflows/{id}/activate → تفعيل workflow
POST   /api/v1/workflows/{id}/run      → تنفيذ workflow
GET    /api/v1/executions              → سجل التنفيذات
DELETE /api/v1/workflows/{id}          → حذف workflow
```

---

## Apache Tika — دعم الخطوط

الصورة `salehsaas-tika-fonts:latest` (مبنية من `Dockerfile.tika`) تتضمن:

- `ttf-mscorefonts-installer`: Arial, Times New Roman, Courier New, Verdana, Georgia
- `fonts-liberation2`: بديل مفتوح المصدر لخطوط Microsoft
- `fonts-freefont-ttf`: FreeSans, FreeSerif, FreeMono
- `fonts-dejavu-core`: DejaVu Sans, DejaVu Serif

هذا يُلغي جميع تحذيرات `Using fallback font LiberationSans` من PDFBox.
