# OpenWebUI — الدليل الشامل

> تنبيه حاكم: هذا الملف شرح معرفي عام لـ OpenWebUI داخل المشروع، وليس مرجعًا حاكمًا للتشغيل الحالي. إعدادات التشغيل الفعلية تُحسم من `docker-compose.yml` ثم `ARCHITECTURE.md`.

## تصحيح تشغيلي إلزامي

- صورة Open WebUI الفعلية في التشغيل الحالي هي `ghcr.io/open-webui/open-webui:v0.8.12`.
- التكامل عبر `mcpo` ملغى حاليًا في المشروع، لذلك لا يجوز افتراض توفره أثناء اتخاذ القرار.
- أي مواد تاريخية مرتبطة بـ `mcpo` لا تُعامل كمرجع تشغيلي حي.
- المسار المرجعي الصحيح للبحث القانوني الحي يعتمد `saleh_knowledge` وواجهات Chroma `v1` في المسارات النشطة.

## ما هو OpenWebUI؟

**OpenWebUI** واجهة مستخدم مفتوحة المصدر لنماذج اللغة الكبيرة (LLMs)، تعمل محلياً بالكامل وتدعم Ollama وأي API متوافق مع OpenAI. في مشروع SaleHSaaS تعمل على المنفذ **3000** (http://localhost:3000).

- **المستودع:** https://github.com/open-webui/open-webui
- **الوثائق:** https://docs.openwebui.com
- **الإصدار في المشروع:** `ghcr.io/open-webui/open-webui:v0.8.12`

---

## الميزات الرئيسية

### 1. الشات (Chat)
- محادثات مع أي نموذج Ollama أو API
- دعم كامل للعربية والـ RTL
- حفظ تاريخ المحادثات في PostgreSQL
- مشاركة المحادثات
- استيراد/تصدير المحادثات

### 2. مساحة العمل (Workspace)

#### أ. Model Builder (بناء النماذج)
- إنشاء "شخصيات" متخصصة فوق أي نموذج أساسي
- تحديد System Prompt مخصص
- ضبط درجة الحرارة (Temperature) ونافذة السياق
- ربط قاعدة معرفة (Knowledge) بالنموذج
- مثال: نموذج "خبير n8n" فوق deepseek-r1:7b

#### ب. Knowledge (قاعدة المعرفة / RAG)
- رفع ملفات (PDF, DOCX, TXT, MD, CSV, XLSX)
- إضافة روابط مواقع ويب مباشرة
- فهرسة تلقائية بالتضمينات (Embeddings)
- استخدامها في المحادثات بكتابة `#` ثم اسم المجموعة
- API لإضافة الملفات برمجياً: `POST /api/v1/knowledge/{id}/file/add`

#### ج. Prompts (القوالب)
- حفظ Prompts متكررة كقوالب
- استدعاؤها بكتابة `/` في الشات

#### د. Tools (الأدوات)
- كتابة أدوات Python تُنفَّذ أثناء المحادثة
- مثال: أداة تجلب بيانات من n8n API وتعرضها

#### هـ. Functions (الدوال)
- دوال Python مخصصة تُحقن في سير المحادثة
- تُستخدم لتعديل المدخلات أو المخرجات

### 3. RAG (الاسترجاع المعزز بالتوليد)
- البحث الدلالي في الوثائق المرفوعة
- دعم ChromaDB كقاعدة بيانات متجهية
- نموذج التضمين: `nomic-embed-text:latest`
- استخدام `#` في الشات لتفعيل RAG على مجموعة معينة

### 4. Web Search (البحث على الإنترنت)
- تكامل مع SearXNG (مثبت في SaleHSaaS)
- البحث التلقائي عند الحاجة لمعلومات آنية
- الإعداد: Admin Panel → Web Search → SearXNG

### 5. Pipelines (خطوط الأنابيب)
- كود Python يعمل بين المستخدم والنموذج
- في SaleHSaaS: `saleh_legal_pipeline.py` للمعالجة القانونية
- يعمل على المنفذ 9099

---

## OpenWebUI API

### المصادقة
```bash
# الحصول على API Key من: Settings → Account → API Keys
Authorization: Bearer YOUR_API_KEY
```

### نقاط النهاية الرئيسية

```bash
# قائمة النماذج
GET /api/models

# إرسال رسالة (متوافق مع OpenAI)
POST /api/chat/completions
{
  "model": "deepseek-r1:7b",
  "messages": [{"role": "user", "content": "مرحبا"}]
}

# قائمة مجموعات المعرفة
GET /api/v1/knowledge/

# إنشاء مجموعة معرفة جديدة
POST /api/v1/knowledge/create
{"name": "n8n Expert Knowledge", "description": "..."}

# إضافة ملف لمجموعة معرفة
POST /api/v1/knowledge/{id}/file/add
Content-Type: multipart/form-data
file: [binary]

# رفع ملف
POST /api/v1/files/
Content-Type: multipart/form-data
file: [binary]
```

---

## إعداد OpenWebUI في SaleHSaaS

### الإعدادات الرئيسية (Admin Panel)
- **Ollama URL:** `http://host.docker.internal:11434`
- **Default Model:** `deepseek-r1:7b`
- **RAG Embedding Model:** `nomic-embed-text:latest`
- **Vector DB:** ChromaDB → `http://chromadb:8000`
- **Web Search:** SearXNG → `http://searxng:8080`

### متغيرات البيئة المهمة
```env
WEBUI_SECRET_KEY=salehsaas_secret_key
OLLAMA_BASE_URL=http://host.docker.internal:11434
CHROMA_HTTP_HOST=chromadb
CHROMA_HTTP_PORT=8000
```

---

## نموذج "خبير أتمتة n8n" في OpenWebUI

تم إنشاؤه في **Workspace → Models** بالإعدادات:
- **الاسم:** `🔄 خبير أتمتة n8n`
- **النموذج الأساسي:** `deepseek-r1:7b`
- **Temperature:** `0.3` (دقيق ومنطقي)
- **Top P:** `0.9`
- **Context:** `8192` token
- **قاعدة المعرفة:** `n8n Expert Knowledge`
- **System Prompt:** متخصص في بناء سير عمل n8n وتوليد JSON صحيح

---

## أفضل الممارسات في OpenWebUI

1. **استخدم `#` لتفعيل RAG** — اكتب `#n8n Expert Knowledge` قبل سؤالك
2. **استخدم `/` للقوالب** — احفظ Prompts متكررة كقوالب
3. **ربط Knowledge بالنموذج** — أفضل من كتابة `#` في كل مرة
4. **درجة الحرارة 0.3** للمهام التقنية، **0.7-0.9** للإبداعية
5. **Context Window** — اضبطه حسب حجم الوثائق التي تعمل عليها

---

## مجتمع OpenWebUI

- **GitHub:** https://github.com/open-webui/open-webui (⭐ 80k+)
- **Discord:** https://discord.gg/5rJgQTnV4s
- **Reddit:** r/OpenWebUI
- **الوثائق:** https://docs.openwebui.com
