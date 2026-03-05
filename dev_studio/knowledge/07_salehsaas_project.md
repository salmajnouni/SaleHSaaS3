# SaleH SaaS 4.0 — دليل المشروع الشامل

## نظرة عامة

**SaleH SaaS** منصة ذكاء اصطناعي محلية متكاملة مصممة للمؤسسات القانونية والحكومية السعودية. تعمل بالكامل على البنية التحتية المحلية (On-Premise) دون إرسال أي بيانات خارجياً، وتوفر قدرات RAG (الاسترجاع المعزز بالتوليد) متقدمة على الوثائق القانونية السعودية مع أتمتة كاملة لسير العمل عبر n8n.

- **الإصدار الحالي:** 4.0.0
- **موقع الكود:** https://github.com/salmajnouni/SaleHSaaS3
- **مكان التشغيل:** `D:\SaleHSaaS3` على Windows
- **المطور:** صالح المجنوني — مكة المكرمة، المملكة العربية السعودية

---

## الخدمات والمنافذ

| الخدمة | المنفذ | IP الداخلي | الوصف |
|--------|--------|-----------|-------|
| **Open WebUI** | 3000 | 172.20.0.30 | واجهة المحادثة الرئيسية + RAG |
| **PostgreSQL** | 5432 (داخلي) | 172.20.0.10 | قاعدة البيانات الرئيسية |
| **ChromaDB** | 8010 | 172.20.0.20 | قاعدة البيانات المتجهية للوثائق |
| **Apache Tika** | 9998 (داخلي) | 172.20.0.32 | استخراج النصوص من 1000+ صيغة |
| **Ollama** | 11434 | Windows Host | نماذج اللغة والتضمين المحلية |
| **Knowledge Watcher** | داخلي | 172.20.0.61 | خط أنابيب استيعاب الوثائق v3.0 |
| **n8n** | 5678 | 172.20.0.40 | أتمتة سير العمل |
| **mcpo** | 8020 | 172.20.0.60 | وكيل MCP-to-OpenAPI |
| **SearXNG** | 8080 (داخلي) | 172.20.0.33 | بحث محلي على الإنترنت |
| **Code Server** | 8443 | 172.20.0.50 | بيئة التطوير من المتصفح (VS Code) |
| **Pipelines** | 9099 | 172.20.0.31 | خط أنابيب RAG القانوني |

**شبكة Docker:** `salehsaas_net` — Subnet: `172.20.0.0/16`

---

## هيكل المجلدات

```
D:\SaleHSaaS3\
├── agents/              ← تعريفات الوكلاء الذكيين
├── config/              ← ملفات الإعداد (Continue, OpenWebUI, etc.)
├── core/                ← الكود الأساسي للمنصة
├── data/                ← البيانات المحلية
├── data_pipeline/       ← خط أنابيب معالجة البيانات
├── dev_studio/          ← بيئة التطوير (Code Server)
│   ├── Dockerfile
│   ├── docker-compose.dev-studio.yml
│   ├── config/
│   │   ├── continue-config.json
│   │   ├── n8n_expert_model.json
│   │   └── n8n_system_prompt_v2.txt
│   └── workflows/
│       └── knowledge_inbox_workflow.json
├── docker/              ← ملفات Docker المساعدة
├── docs/                ← التوثيق
├── file_watcher/        ← مراقب الملفات
├── knowledge_inbox/     ← ← ← ضع الملفات هنا للهضم التلقائي
├── knowledge_processing/← قيد المعالجة (تلقائي)
├── knowledge_archive/   ← مؤرشف بنجاح (مرتب بالتاريخ)
├── knowledge_failed/    ← فشل المعالجة + تقرير الخطأ
├── knowledge_processed/ ← ملفات تمت معالجتها يدوياً
├── logs/                ← سجلات النظام والتقارير
├── n8n/                 ← إعدادات n8n
├── n8n_workflows/       ← سير عمل n8n المصدّرة
├── pipelines/           ← خطوط أنابيب OpenWebUI
├── saleh_brain/         ← قاعدة المعرفة الذكية
├── saleh_dashboard/     ← لوحة التحكم
├── scripts/             ← سكريبتات PowerShell والأتمتة
├── services/            ← تعريفات الخدمات
├── tools/               ← أدوات مساعدة
├── ui/                  ← واجهة المستخدم
├── .env                 ← متغيرات البيئة (لا ترفعه لـ GitHub)
├── .env.example         ← نموذج متغيرات البيئة
├── docker-compose.yml   ← ملف تشغيل جميع الخدمات
├── ARCHITECTURE.md      ← المخطط المعماري
├── CHANGELOG.md         ← سجل التغييرات
├── INSTALL_GUIDE.md     ← دليل التثبيت
├── MCP_SETUP_GUIDE.md   ← دليل إعداد MCP
├── README.md            ← نظرة عامة
└── SERVICES.md          ← تفاصيل الخدمات
```

---

## خط أنابيب استيعاب المعرفة (Knowledge Watcher v3.0)

```
knowledge_inbox/  ← ضع الملفات هنا
      │ (كل 10 ثوانٍ)
      ▼
Knowledge Watcher (172.20.0.61)
      │
      ├──► Apache Tika :9998  → استخراج النص (1000+ صيغة)
      ├──► Ollama :11434      → توليد التضمينات (nomic-embed-text)
      ├──► ChromaDB :8010     → تخزين chunks + embeddings
      │         Collection: saleh_legal_knowledge
      ├──► knowledge_archive/YYYY-MM-DD/  (نجاح)
      └──► knowledge_failed/              (فشل + تقرير .txt)
```

**الصيغ المدعومة:** PDF، DOCX، XLSX، PPTX، TXT، CSV، MD، وأكثر من 1000 صيغة أخرى.

---

## تدفق المحادثة (RAG Pipeline)

```
المستخدم (Open WebUI :3000)
      │
      ▼
Open WebUI → Pipelines :9099 (saleh_legal_pipeline.py)
      │         ├──► Legal Glossary (حقن تعريفات المصطلحات)
      │         └──► saleh_legal_rag.py → ChromaDB :8010 (بحث دلالي)
      │
      ├──► Ollama :11434 (توليد الإجابة)
      └──► SearXNG :8080 (بحث الإنترنت - اختياري)
```

---

## تدفق n8n_bridge — عرض workflows كنماذج

> **المرجع:** `docker-compose.yml` السطر 321 — `image: ghcr.io/sveneisenschmidt/n8n-openai-bridge:latest`

خدمة `n8n_bridge` تفحص n8n كل دقيقة وتعرض أي workflow يحمل tag اسمه `n8n-openai-bridge` كنموذج مباشر في Open WebUI. شرط ظهور الـ workflow: يجب أن يحتوي على عقدة **Chat Trigger** أو **Webhook**.

```
Open WebUI :3000
      │  (يرى نماذج إضافية)
      ▼
n8n_bridge :11435
      │  (يفحص كل 60 ثانية)
      ▼
n8n :5678
      └──► workflows ذات tag: n8n-openai-bridge + chatTrigger/Webhook
```

---

## متغيرات البيئة الرئيسية (.env)

```env
# كلمات المرور
CODE_SERVER_PASSWORD=ze#nrgmkUhQpD*gq^TbX
N8N_BASIC_AUTH_PASSWORD=admin123
POSTGRES_PASSWORD=salehsaas_secure_2024

# المنافذ
CODE_SERVER_PORT=8443
N8N_PORT=5678
OPENWEBUI_PORT=3000
CHROMA_PORT=8010

# Ollama
OLLAMA_BASE_URL=http://host.docker.internal:11434
EMBEDDING_MODEL=nomic-embed-text:latest

# ChromaDB
CHROMA_HOST=chromadb
CHROMA_PORT_INTERNAL=8000
CHROMA_COLLECTION=saleh_legal_knowledge
```

---

## النماذج المثبتة على Ollama

| النموذج | الحجم | الاستخدام |
|---------|-------|-----------|
| deepseek-r1:7b | 4.7 GB | التفكير العميق والبرمجة |
| deepseek-r1:8b | 5.2 GB | نسخة أكبر من R1 |
| llama3.1:8b | 4.9 GB | المساعد العام |
| llama3.1:latest | 4.9 GB | نفس السابق |
| qwen2.5:3b | 1.9 GB | الإكمال التلقائي السريع |
| mistral:latest | 4.4 GB | الكتابة والتوثيق |
| gemma3:4b | 3.3 GB | المهام الخفيفة |
| nomic-embed-text | 274 MB | التضمينات (RAG) |
| glm-4.7-flash | 19 GB | نموذج ضخم متعدد الاستخدامات |

---

## أوامر التشغيل الشائعة

```powershell
# تشغيل جميع الخدمات
cd D:\SaleHSaaS3
docker-compose up -d

# إيقاف جميع الخدمات
docker-compose down

# تشغيل Dev Studio فقط
docker compose -f dev_studio\docker-compose.dev-studio.yml up -d

# عرض حالة الخدمات
docker-compose ps

# عرض سجلات خدمة معينة
docker-compose logs -f knowledge_watcher

# إعادة بناء خدمة معينة
docker-compose build --no-cache code-server
docker-compose up -d code-server
```

---

## روابط الوصول

| الخدمة | الرابط |
|--------|--------|
| Open WebUI (الشات) | http://localhost:3000 |
| n8n (الأتمتة) | http://localhost:5678 |
| Code Server (التطوير) | http://localhost:8443 |
| ChromaDB API | http://localhost:8010 |
| mcpo API | http://localhost:8020 |

---

## ملاحظات مهمة

- **Ollama يعمل على Windows مباشرة** وليس داخل Docker — يُصل إليه عبر `host.docker.internal:11434`
- **ملف .env لا يُرفع إلى GitHub** — يحتوي على كلمات مرور حساسة
- **knowledge_inbox** هو الطريق الوحيد لإضافة معرفة جديدة تلقائياً
- **ChromaDB collection** الرئيسية: `saleh_legal_knowledge`
- **شبكة Docker الداخلية:** `salehsaas_net` — الخدمات تتواصل بأسمائها مباشرة
