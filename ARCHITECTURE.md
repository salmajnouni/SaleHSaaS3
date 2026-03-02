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
│  │  n8n :5678           Code Server :8443   mcpo :8020          │    │
│  │  172.20.0.40         172.20.0.50         172.20.0.60         │    │
│  │                                                               │    │
│  │  Knowledge Watcher                                            │    │
│  │  172.20.0.61                                                  │    │
│  └──────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

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
      ├──► Ollama :11434      ──► توليد التضمينات (nomic-embed-text)
      │         (timeout: 300s)
      │
      ├──► ChromaDB :8000     ──► تخزين chunks + embeddings
      │         (API v2: /api/v2/tenants/default_tenant/databases/default_database/)
      │         (Collection: saleh_legal_knowledge)
      │
      ├──► knowledge_archive/YYYY-MM-DD/  (نجاح)
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

## تدفق أدوات MCP

```
المستخدم يكتب في Open WebUI
      │
      ▼
Open WebUI → mcpo :8020 (REST API)
      │
      ├──► ollama_model_builder.py  →  Ollama :11434
      │         (تحميل/حذف/عرض النماذج)
      │
      ├──► legal_rag_mcp.py         →  ChromaDB :8000
      │         (بحث دلالي في الوثائق القانونية)
      │
      └──► n8n_builder.py           →  n8n :5678
                (إنشاء/تفعيل/تنفيذ workflows)
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
| `code_server` | `172.20.0.50` | `8443` | تطوير الكود من المتصفح |
| `mcpo` | `172.20.0.60` | `8020` | تحويل MCP إلى REST API |
| `knowledge_watcher` | `172.20.0.61` | داخلي | مراقبة inbox وإدخال الوثائق |

---

## ChromaDB v2 API — المسارات المستخدمة

```
Base URL: http://chromadb:8000
API Path: /api/v2/tenants/default_tenant/databases/default_database/

GET    /collections                    → قائمة المجموعات
GET    /collections/{name}             → معلومات المجموعة (يُعيد UUID)
POST   /collections/{uuid}/add         → إضافة chunks + embeddings
POST   /collections/{uuid}/query       → بحث دلالي
GET    /heartbeat                      → فحص الصحة
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
