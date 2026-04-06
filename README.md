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

> تنبيه تشغيلي: هذا الملف يصف التشغيل الحالي المعتمد في `docker-compose.yml`. عند أي تعارض بين هذه الصفحة وبين أي وثيقة أخرى، يكون المرجع الأعلى هو `docker-compose.yml` ثم `ARCHITECTURE.md`.

---

## المكونات الرئيسية

| # | الخدمة | الصورة | المنفذ | الوصف |
|---|---|---|---|---|
| 1 | **Open WebUI** | `ghcr.io/open-webui/open-webui:v0.8.12` | `3000` | واجهة المحادثة الرئيسية + RAG |
| 2 | **PostgreSQL** | `postgres:16-alpine` | داخلي | قاعدة البيانات الرئيسية |
| 3 | **ChromaDB** | `chromadb/chroma:0.5.3` | `8010` | قاعدة البيانات المتجهية للوثائق |
| 4 | **Apache Tika** | `apache/tika:latest` | داخلي | استخراج النصوص من PDF وWord وExcel |
| 5 | **Ollama** | Windows Host | `11434` | نماذج اللغة والتضمين المحلية |
| 6 | **Knowledge Watcher** | مبني محلياً | داخلي | خط أنابيب استيعاب الوثائق التلقائي v3.0 |
| 7 | **n8n** | `n8nio/n8n:latest` | `5678` | أتمتة سير العمل |
| 8 | **SearXNG** | `searxng/searxng:latest` | داخلي | بحث محلي على الإنترنت |
| 9 | **Data Pipeline** | مبني محلياً | `8001` | استقبال الملفات، التقطيع، وتخزينها في ChromaDB |
| 10 | **Browserless** | `browserless/chrome:latest` | `3001` | متصفح آلي للخدمات التي تحتاج تنفيذًا متصفحياً |
| 11 | **Open Terminal** | `ghcr.io/open-webui/open-terminal` | `8000` | طرفية داخلية مرتبطة بالمجلد المحلي `saleh/` |

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
| n8n | http://localhost:5678 | admin / `salehsaas_pass` من `docker-compose.yml` |
| Open Terminal | http://localhost:8000 | يتطلب `OPEN_TERMINAL_API_KEY` |
| Browserless | http://localhost:3001 | — |
| ChromaDB API | http://localhost:8010 | — |

---

## خط أنابيب استيعاب المعرفة (v3.0)

يعمل **Knowledge Watcher** تلقائياً على مراقبة مجلد `knowledge_inbox` وإدخال الوثائق إلى قاعدة البيانات المتجهية دون أي تدخل يدوي.

```
knowledge_inbox/          ← ضع الملفات هنا
knowledge_processed/      ← الملفات الناجحة بعد الاستيعاب
knowledge_failed/         ← فشل المعالجة + تقرير الخطأ
```

**الصيغ المدعومة:** PDF، DOCX، XLSX، PPTX، TXT، CSV، MD، وأكثر من 1000 صيغة أخرى عبر Apache Tika.

**آلية العمل:**

1. يكتشف الملف في `knowledge_inbox` خلال 10 ثوانٍ
2. يستخرج النص عبر Apache Tika (مع دعم كامل للخطوط العربية والغربية)
3. يقسّم النص إلى أجزاء عبر `data_pipeline`
4. يولّد التضمينات عبر Ollama (`nomic-embed-text:latest`)
5. يخزّن في ChromaDB عبر واجهة `v1` (مجموعة: `saleh_knowledge`)
6. ينقل الملف الناجح إلى `knowledge_processed/`

---

## ملاحظة حول أدوات MCP

ملفات أدوات MCP موجودة داخل المستودع كمرجع تاريخي فقط، ومسار `mcpo` ملغي في التشغيل الحالي.
ولا يجوز اعتبار أي أصول legacy مرتبطة به جزءًا من الشجرة التشغيلية الحية أو مرجعًا حاكمًا للتشغيل.

بالتالي:

1. لا يجوز للوكلاء افتراض وجود endpoint حي على `localhost:8020`.
2. لا يعتمد هذا المشروع حاليًا أي مسار تشغيل عبر `mcpo`.
3. البديل التشغيلي المعتمد للأدوات/المعالجات هو `pipelines` و`data_pipeline` حسب `docker-compose.yml`.

---

## إعدادات n8n API

```
URL:     http://localhost:5678
Header:  X-N8N-API-KEY: salehsaas-n8n-api-key
```

يمكن للنموذج الذكي تصميم workflows كـ JSON وإرساله للإنشاء في n8n عبر المحادثة، وتشغيل سير عمل موجودة عبر أداة `n8n_builder`. ومع ذلك، "نجاح التنفيذ" في n8n يعني فقط إكمال العُقد — لا يُؤكد إنشاء ملفات أو نجاح عمليات النظام الخارجية. التحقق يتطلب فحص ناتج سير العمل الفعلي.

---

## هيكل المشروع

```
SaleHSaaS3/
├── config/
│   ├── postgres/init.sql         # تهيئة قاعدة البيانات
│   └── searxng/settings.yml      # إعدادات البحث المحلي
├── docker/
│   └── code-server/              # ملفات بيئة تطوير غير مفعلة في التشغيل الحالي
├── docs/guides/                  # توثيق تقني مفصّل
├── knowledge_inbox/              # مجلد إدخال الوثائق
├── knowledge_processed/          # الملفات الناجحة بعد الاستيعاب
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
Invoke-WebRequest -Uri "http://localhost:8010/api/v1/collections"

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
| Open Terminal لا يعمل | تحقق من `OPEN_TERMINAL_API_KEY` ومن ربط المجلد `saleh/` في `docker-compose.yml` |
| n8n API لا يستجيب | تحقق من الوصول إلى `http://localhost:5678/api/v1/workflows` باستخدام Header `X-N8N-API-KEY` |

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
| [RUNTIME_STATUS_CARD.md](./RUNTIME_STATUS_CARD.md) | بطاقة سريعة: ما هو حي الآن وما هو ملغى/Legacy |
| [الحقائق التشغيلية الحاكمة - v0.1.md](./الحقائق التشغيلية الحاكمة%20-%20v0.1.md) | المرجع المختصر الحاكم للحقائق التشغيلية الحالية |
| [INSTALL_GUIDE.md](./INSTALL_GUIDE.md) | دليل التثبيت المفصّل |
| [docs/guides/knowledge_watcher.md](./docs/guides/knowledge_watcher.md) | توثيق خدمة استيعاب الوثائق |

---

<div align="center">

**صُنع بفخر في مكة المكرمة 🕋 — جميع الحقوق محفوظة © 2026 SaleH SaaS**

</div>
