# SaleH SaaS 4.0 — دليل المشروع الشامل

> تنبيه حاكم: هذه الوثيقة معرفة داخلية مساندة وليست المرجع التشغيلي الأعلى. عند أي تعارض، تكون الأولوية لـ `docker-compose.yml` ثم `ARCHITECTURE.md` ثم `README.md`.

## تصحيح تشغيلي إلزامي

- خدمة `mcpo` ملغاة حاليًا في المشروع ولا تُستخدم كمسار تشغيلي.
- أي مواد تاريخية مرتبطة بـ `mcpo` تبقى خارج المسار التشغيلي الحي.
- لا توجد خدمة `Code Server` مفعلة ضمن `docker-compose.yml` الحالي.
- الخدمات التشغيلية المضافة فعليًا في البيئة الحالية تشمل `data_pipeline` و `browserless` و `open-terminal`.
- الاستيعاب الحي يستخدم `ChromaDB v1` في المسارات النشطة، والمجموعة الحية هي `saleh_knowledge`.
- الملفات الناجحة من `knowledge_watcher` تنتهي في `knowledge_processed/`، وليس `knowledge_archive/`.
- المجلد المحلي `saleh/` يظهر داخل `open-terminal` على المسار `/home/user/projects`.

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
| **SearXNG** | 8080 (داخلي) | 172.20.0.33 | بحث محلي على الإنترنت |
| **Pipelines** | 9099 | 172.20.0.31 | خط أنابيب RAG القانوني |
| **Data Pipeline** | 8001 | 172.20.0.62 | خدمة استيعاب الملفات والتقطيع |
| **Browserless** | 3001 | 172.20.0.70 | متصفح آلي بلا واجهة |
| **Open Terminal** | 8000 | 172.20.0.80 | طرفية داخلية مرتبطة بـ `saleh/` |

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
├── dev_studio/          ← بيئة تطوير اختيارية مستقلة (مسار Code Server غير مفعّل افتراضيًا)
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
├── knowledge_processed/ ← الملفات الناجحة بعد الاستيعاب
├── knowledge_failed/    ← فشل المعالجة + تقرير الخطأ
├── logs/                ← سجلات النظام والتقارير
├── n8n/                 ← إعدادات n8n
├── n8n_workflows/       ← سير عمل n8n المصدّرة
├── pipelines/           ← خطوط أنابيب OpenWebUI
├── saleh_brain/         ← قاعدة المعرفة الذكية
├── saleh_dashboard/     ← مشروع Dashboard قديم/مرجعي غير مفعل في التشغيل الحالي
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
      │         Collection: saleh_knowledge
      ├──► knowledge_processed/          (نجاح)
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

## ملاحظة عن أدوات MCP

```
الأدوات الخاصة بـ MCP موجودة داخل المستودع كملفات تكامل،
لكن مسار mcpo ملغى حاليًا ضمن هذا المشروع.
وأي مواد تاريخية مرتبطة به تبقى خارج المسار التشغيلي الحي.

لذلك لا يجوز اعتبار المنفذ 8020 جزءًا من التشغيل الحالي
إلا بعد تحقق مباشر من تشغيل خدمة مستقلة لهذا الغرض.
```

---

## متغيرات البيئة الرئيسية (.env)

```env
# ملاحظة
# القيم الفعلية يجب أن تُقرأ من docker-compose.yml وقت التشغيل.
# لا تعتمد هذا المقتطف كمرجع كلمات مرور أو منافذ حاكم.

OLLAMA_BASE_URL=http://host.docker.internal:11434
EMBEDDING_MODEL=nomic-embed-text:latest
CHROMA_HOST=chromadb
CHROMA_PORT_INTERNAL=8000
CHROMA_COLLECTION=saleh_knowledge
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

# تشغيل Dev Studio (اختياري - Compose منفصل)
docker compose -f dev_studio\docker-compose.dev-studio.yml up -d
```

---

## روابط الوصول

| الخدمة | الرابط |
|--------|--------|
| Open WebUI (الشات) | http://localhost:3000 |
| n8n (الأتمتة) | http://localhost:5678 |
| ChromaDB API | http://localhost:8010 |
| Open Terminal | http://localhost:8000 |
| Browserless | http://localhost:3001 |

---

## ملاحظات مهمة

- **Ollama يعمل على Windows مباشرة** وليس داخل Docker — يُصل إليه عبر `host.docker.internal:11434`
- **ملف .env لا يُرفع إلى GitHub** — يحتوي على كلمات مرور حساسة
- **knowledge_inbox** هو الطريق الوحيد لإضافة معرفة جديدة تلقائياً
- **ChromaDB collection** الرئيسية: `saleh_knowledge`
- **شبكة Docker الداخلية:** `salehsaas_net` — الخدمات تتواصل بأسمائها مباشرة
