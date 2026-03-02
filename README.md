<div align="center">

# 🕋 SaleH SaaS 4.0

**نظام ذكاء اصطناعي قانوني متكامل — صُنع بفخر في مكة المكرمة، المملكة العربية السعودية**

[![Version](https://img.shields.io/badge/version-4.0.0-blue.svg)](./CHANGELOG.md)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](./LICENSE)
[![Docker](https://img.shields.io/badge/docker-compose-2496ED.svg)](./docker-compose.yml)
[![Python](https://img.shields.io/badge/python-3.11+-yellow.svg)](./requirements.txt)

</div>

---

## نظرة عامة

**SaleH SaaS** منصة ذكاء اصطناعي محلية متكاملة مصممة للمؤسسات القانونية والحكومية السعودية. تعمل بالكامل على البنية التحتية المحلية دون إرسال أي بيانات خارجياً، وتوفر قدرات RAG (الاسترجاع المعزز بالتوليد) متقدمة على الوثائق القانونية السعودية مع أتمتة كاملة لسير العمل عبر n8n.

---

## المكونات الرئيسية

| # | الخدمة | الصورة | المنفذ | الوصف |
|---|---|---|---|---|
| 1 | **Open WebUI** | `ghcr.io/open-webui/open-webui:main` | `3000` | واجهة المحادثة الرئيسية + RAG |
| 2 | **PostgreSQL** | `postgres:16-alpine` | داخلي | قاعدة البيانات الرئيسية |
| 3 | **ChromaDB** | `chromadb/chroma:latest` | `8010` | قاعدة البيانات المتجهية للوثائق |
| 4 | **Apache Tika** | `salehsaas-tika-fonts:latest` | داخلي | استخراج النصوص من PDF وWord وExcel |
| 5 | **Ollama** | Windows Host | `11434` | نماذج اللغة والتضمين المحلية |
| 6 | **Knowledge Watcher** | مبني محلياً | داخلي | خط أنابيب استيعاب الوثائق التلقائي v3.0 |
| 7 | **n8n** | `n8nio/n8n:latest` | `5678` | أتمتة سير العمل |
| 8 | **mcpo** | مبني محلياً | `8020` | وكيل MCP-to-OpenAPI |
| 9 | **SearXNG** | `searxng/searxng:latest` | داخلي | بحث محلي على الإنترنت |
| 10 | **Code Server** | `codercom/code-server:latest` | `8443` | بيئة التطوير من المتصفح |

---

## المتطلبات

- **نظام التشغيل:** Windows 10/11 مع PowerShell
- **Docker Desktop:** الإصدار 4.x أو أحدث
- **Ollama:** مثبت على Windows ويعمل على المنفذ `11434`
- **Git:** مثبت ومُعدّ
- **ذاكرة RAM:** 16 GB كحد أدنى (32 GB موصى به)
- **مساحة القرص:** 50 GB على الأقل

---

## التثبيت السريع

```powershell
# 1. استنساخ المستودع
git clone https://github.com/salmajnouni/SaleHSaaS3.git
cd SaleHSaaS3

# 2. نسخ ملف الإعدادات
copy .env.example .env

# 3. تعديل الإعدادات (اختياري)
notepad .env

# 4. بناء وتشغيل جميع الخدمات
docker-compose up -d --build

# 5. التحقق من حالة الخدمات
docker-compose ps
```

---

## الوصول إلى الخدمات

| الخدمة | الرابط | بيانات الدخول الافتراضية |
|---|---|---|
| Open WebUI | http://localhost:3000 | أنشئ حساباً عند أول تشغيل |
| n8n | http://localhost:5678 | admin / admin123 |
| Code Server | http://localhost:8443 | salehsaas123 |
| ChromaDB API | http://localhost:8010 | — |
| mcpo API | http://localhost:8020 | — |

---

## خط أنابيب استيعاب المعرفة (v3.0)

يعمل **Knowledge Watcher** تلقائياً على مراقبة مجلد `knowledge_inbox` وإدخال الوثائق إلى قاعدة البيانات المتجهية دون أي تدخل يدوي.

```
knowledge_inbox/          ← ضع الملفات هنا
knowledge_processing/     ← قيد المعالجة (تلقائي)
knowledge_archive/        ← مؤرشف بنجاح (مرتب بالتاريخ)
knowledge_failed/         ← فشل المعالجة + تقرير الخطأ
```

**الصيغ المدعومة:** PDF، DOCX، XLSX، PPTX، TXT، CSV، MD، وأكثر من 1000 صيغة أخرى عبر Apache Tika.

**آلية العمل:**

1. يكتشف الملف في `knowledge_inbox` خلال 10 ثوانٍ
2. يستخرج النص عبر Apache Tika (مع دعم كامل للخطوط العربية والغربية)
3. يقسّم النص إلى أجزاء (400 حرف، تداخل 40)
4. يولّد التضمينات عبر Ollama (`nomic-embed-text:latest`)
5. يخزّن في ChromaDB v2 API (مجموعة: `saleh_legal_knowledge`)
6. يؤرشف الملف في `knowledge_archive/YYYY-MM-DD/`

---

## أدوات MCP المتاحة

يوفر **mcpo** ثلاثة أدوات قابلة للاستخدام مباشرة من Open WebUI:

| الأداة | الوصف | الوظائف الرئيسية |
|---|---|---|
| `ollama_model_builder` | إدارة نماذج Ollama | تحميل، حذف، عرض النماذج |
| `saleh_legal_rag` | بحث قانوني متقدم | بحث دلالي في الوثائق السعودية |
| `n8n_builder` | بناء سير العمل | إنشاء، تفعيل، تنفيذ workflows في n8n |

**إعداد mcpo في Open WebUI:**

1. اذهب إلى: Settings → Tools → Add Tool
2. أدخل URL: `http://localhost:8020`
3. أدخل API Key: `salehsaas-mcpo-key`

---

## إعدادات n8n API

```
URL:     http://localhost:5678
API Key: salehsaas-n8n-api-key
```

يمكن للنموذج الذكي إنشاء وإدارة workflows تلقائياً عبر أداة `n8n_builder` من خلال المحادثة الطبيعية في Open WebUI.

---

## هيكل المشروع

```
SaleHSaaS3/
├── config/
│   ├── mcpo/config.json          # إعدادات أدوات MCP (3 أدوات)
│   ├── postgres/init.sql         # تهيئة قاعدة البيانات
│   └── searxng/settings.yml      # إعدادات البحث المحلي
├── docker/
│   ├── mcpo/Dockerfile           # صورة mcpo المخصصة
│   └── code-server/              # إعدادات Code Server
├── docs/guides/                  # توثيق تقني مفصّل
├── knowledge_inbox/              # مجلد إدخال الوثائق
├── knowledge_archive/            # أرشيف الوثائق المعالجة
├── knowledge_failed/             # الوثائق الفاشلة + تقارير الأخطاء
├── n8n/workflows/                # قوالب سير العمل الجاهزة
├── pipelines/                    # معالجات Open WebUI
│   ├── saleh_legal_pipeline.py   # خط أنابيب RAG القانوني
│   └── saleh_legal_rag.py        # محرك البحث الدلالي
├── saleh_brain/
│   └── glossary/                 # المعجم القانوني السعودي
├── scripts/windows/              # سكريبتات التثبيت والإدارة
├── services/
│   └── knowledge_watcher/        # خدمة استيعاب الوثائق v3.0
│       ├── Dockerfile
│       └── watcher.py
├── tools/mcp/
│   ├── legal_rag_mcp.py          # أداة RAG القانوني
│   ├── n8n_builder.py            # أداة بناء n8n workflows
│   └── ollama_model_builder.py   # أداة إدارة Ollama
├── Dockerfile.tika               # صورة Tika مع خطوط Microsoft
├── docker-compose.yml            # تكوين جميع الخدمات
├── .env.example                  # نموذج متغيرات البيئة
├── CHANGELOG.md                  # سجل التغييرات
└── ARCHITECTURE.md               # المخطط المعماري
```

---

## الأوامر الشائعة

```powershell
# تشغيل جميع الخدمات
docker-compose up -d

# إيقاف جميع الخدمات
docker-compose down

# عرض سجلات خدمة معينة (مثال: Knowledge Watcher)
docker logs salehsaas_watcher --tail 50 -f

# إعادة بناء خدمة معينة
docker-compose build --no-cache tika
docker-compose up -d tika

# التحقق من حالة ChromaDB
Invoke-WebRequest -Uri "http://localhost:8010/api/v2/heartbeat"

# التحقق من n8n API
Invoke-WebRequest -Uri "http://localhost:5678/api/v1/workflows" `
  -Headers @{"X-N8N-API-KEY"="salehsaas-n8n-api-key"}

# سحب آخر التحديثات وإعادة التشغيل
git pull origin main
docker-compose up -d --build
```

---

## استكشاف الأخطاء

| المشكلة | الحل |
|---|---|
| Knowledge Watcher لا يعالج الملفات | `docker logs salehsaas_watcher --tail 30` |
| ChromaDB لا يستجيب | `docker-compose restart chromadb` |
| Ollama لا يولّد تضمينات | تأكد من تشغيل Ollama على Windows وتحميل `nomic-embed-text` |
| تحذيرات خطوط Tika | تم الحل في v4.0 — أعد بناء Tika: `docker-compose build --no-cache tika` |
| mcpo لا يتصل | `docker logs salehsaas_mcpo --tail 20` |
| n8n API لا يستجيب | تحقق من المتغير `N8N_PUBLIC_API_DISABLED=false` في docker-compose.yml |

---

## الأمان والخصوصية

- جميع البيانات تُعالج **محلياً** — لا إرسال خارجي من أي نوع
- Ollama يعمل على الجهاز المحلي مباشرة
- ChromaDB مخزّن في Docker volume محلي
- لا يوجد اتصال بأي خدمة سحابية خارجية

---

## التوثيق التقني

| الملف | المحتوى |
|---|---|
| [CHANGELOG.md](./CHANGELOG.md) | سجل جميع التغييرات والإصدارات |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | المخطط المعماري التفصيلي |
| [INSTALL_GUIDE.md](./INSTALL_GUIDE.md) | دليل التثبيت المفصّل |
| [MCP_SETUP_GUIDE.md](./MCP_SETUP_GUIDE.md) | دليل إعداد أدوات MCP |
| [docs/guides/knowledge_watcher.md](./docs/guides/knowledge_watcher.md) | توثيق خدمة استيعاب الوثائق |

---

<div align="center">

**صُنع بفخر في مكة المكرمة 🕋 — جميع الحقوق محفوظة © 2026 SaleH SaaS**

</div>
