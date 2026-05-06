# خطة مراجعة الكود — SaleH SaaS 4.0

> تاريخ الإنشاء: 2026-04-28
> الحالة: قيد التنفيذ

---

## توزيع الوكلاء

| # | الوكيل | الجزء | الأولوية | الحالة |
|---|--------|--------|----------|--------|
| 1 | Big Pickle Free | أمنية حرجة | 🔴 أعلى | ⬜ لم يبدأ |
| 2 | GPT-5 Nano Free | جودة الكود | 🟡 عالية | ⬜ لم يبدأ |
| 3 | Hy3 preview Free Free | اختبارات | 🟠 متوسطة | ⬜ لم يبدأ |
| 4 | Ling 2.6 Flash Free Free | إدارة الاعتماديات | 🔵 متوسطة | ⬜ لم يبدأ |
| 5 | MiniMax M2.5 Free Free | معمارية | 🟢 منخفضة | ⬜ لم يبدأ |
| 6 | Nemotron 3 Super Free Free | مراجعة نهائية | ⚪ احتياطي | ⬜ لم يبدأ |

---

## الجزء 1 — أمنية حرجة 🔴
### الوكيل: Big Pickle Free

### 1.1 حذف `.env` من تاريخ Git
- [ ] تشغيل `git filter-branch` أو `BFG Repo-Cleaner` لإزالة `.env` من التاريخ
- [ ] تدوير جميع البيانات السرية المكشوفة فوراً:
  - `SMTP_PASS`
  - `POSTGRES_PASSWORD`
  - `WEBUI_SECRET_KEY`
  - `N8N_PASSWORD`
  - `PIPELINES_API_KEY`
  - `N8N_API_KEY` (JWT كامل)
  - `WEBUI_API_KEY`
  - `N8N_RUNNERS_AUTH_TOKEN`
  - `SEARXNG_SECRET`
  - `OPEN_TERMINAL_API_KEY`
  - `CRAWL4AI_API_TOKEN`
  - `LINKEDIN_ACCESS_TOKEN`

### 1.2 نقل الأسرار من الكود إلى متغيرات بيئة
- [ ] `docker-compose.yml:110` — نقل `WEBUI_API_KEY` إلى `.env`
- [ ] `scripts/update_evo_prompt.py:3` — استبدال القيمة الصلبة بـ `os.getenv("WEBUI_API_KEY")`
- [ ] `core/grc_engine/grc_engine.py:139` — نقل `postgresql://salehsaas:salehsaas_pass@postgres:5432/salehsaas` إلى `os.getenv("DATABASE_URL")`
- [ ] `services/knowledge_watcher/watcher.py:21` — إزالة القيمة الافتراضية `"salehsaas_super_secret_key"` من `os.getenv("WEBUI_API_KEY", ...)`

### 1.3 إصلاح SQL Injection
- [ ] `scripts/n8n/delete_workflows_auto.py` — استبدال f-string في SQL بـ parameterized queries
- [ ] `scripts/n8n/delete_workflows.py` — استبدال f-string في SQL بـ parameterized queries
- [ ] `scripts/_check_webui_keys.py:23` — استبدال `f"PRAGMA table_info({t})"` بـ parameterized query

### 1.4 إزالة بيانات شخصية مكشوفة
- [ ] `.env.example:44` — استبدال البريد الإلكتروني الحقيقي بـ `your-email@example.com`
- [ ] `docker-compose.yml:67` — استخدام `${N8N_LOGIN_EMAIL}` بدل القيمة الصلبة

---

## الجزء 2 — جودة الكود 🟡
### الوكيل: GPT-5 Nano Free

### 2.1 تقسيم الملفات الضخمة
- [ ] تقسيم `pipelines/n8n_controller.py` (1250 سطر) إلى:
  - `pipelines/n8n_api_client.py` — عميل API لـ n8n
  - `pipelines/rag_search.py` — منطق بحث ChromaDB
  - `pipelines/intent_classifier.py` — تصنيف النوايا بالكلمات المفتاحية
  - `pipelines/web_search.py` — بحث SearXNG
  - `pipelines/n8n_controller.py` — الملف الرئيسي يستورد من الوحدات أعلاه

### 2.2 استخراج الكود المكرر
- [ ] إنشاء `shared/__init__.py`
- [ ] إنشاء `shared/utils.py` — نقل `_normalize_content()` و `_safe_text()` من:
  - `pipelines/n8n_controller.py`
  - `pipelines/agency_keyword_filter.py`
  - `pipelines/crewai_operator_pipe.py`
  - `cline_openwebui_proxy.py`
- [ ] إنشاء `shared/chromadb_search.py` — توحيد منطق بحث ChromaDB من:
  - `pipelines/saleh_legal_rag.py`
  - `pipelines/n8n_controller.py`
  - `pipelines/crewai_operator_pipe.py`

### 2.3 توحيد منافذ ChromaDB
- [ ] استبدال جميع القيم الصلبة (`chromadb:8000`, `localhost:8010`) بـ `os.getenv("CHROMADB_URL", "http://chromadb:8000")`
- [ ] إضافة `CHROMADB_URL` إلى `.env.example`

### 2.4 استبدال print بـ logging
- [ ] `pipelines/saleh_legal_pipeline.py` — استبدال `print()` بـ `logging`
- [ ] `pipelines/saleh_legal_rag.py` — استبدال `print()` بـ `logging`
- [ ] `pipelines/salehLegal_ingest.py` — استبدال `print()` بـ `logging`
- [ ] `pipelines/n8n_controller.py` — استبدال `print()` بـ `logging`
- [ ] `pipelines/crewai_operator_pipe.py` — استبدال `print()` بـ `logging`

### 2.5 نقل الأرقام السحرية إلى إعدادات
- [ ] نقل `MIN_RELEVANCE_SCORE`, `TOP_K`, `web_query_max_chars` وغيرها إلى `Valves` أو ملف إعدادات مركزي

### 2.6 إصلاح مسار بيئة خاطئ
- [ ] `services/knowledge_watcher/watcher.py` — إزالة `sys.path.append("/mnt/workspace/iumDLdMeLEk8LXJooJDdK1u4FnvzMAiga1jTUcLZEz/core/grc_engine")` واستبداله بمسار نسبي صحيح

### 2.7 استبدال الإيموجي برموز نصية
- [ ] استبدال ✅ ❌ ⚠️ إلخ في رسائل السجلات بـ `[OK]` `[ERR]` `[WARN]`

---

## الجزء 3 — اختبارات 🟠
### الوكيل: Hy3 preview Free Free

### 3.1 إعداد البنية التحتية للاختبارات
- [ ] إنشاء `tests/__init__.py`
- [ ] إنشاء `tests/conftest.py` مع fixtures لـ:
  - ChromaDB mock client
  - Ollama mock responses
  - n8n mock API responses
  - نماذج وثائق قانونية سعودية
- [ ] إنشاء `pytest.ini` أو إضافة pytest config في `pyproject.toml`

### 3.2 اختبارات وحدة — Pipelines
- [ ] `tests/test_legal_pipeline.py` — اختبار `detect_legal_terms()`, `build_legal_context()`, `is_report_request()`
- [ ] `tests/test_legal_rag.py` — اختبار بحث ChromaDB, حقن السياق, streaming
- [ ] `tests/test_legal_ingest.py` — اختبار `_smart_chunk_legal_text()`, `_fallback_chunking()`, `_extract_text_from_file()`
- [ ] `tests/test_n8n_controller.py` — اختبار `_sanitize_id()`, `_infer_action_from_user_text()`, تنفيذ الأفعال
- [ ] `tests/test_agency_keyword_filter.py` — اختبار الكلمات المفتاحية وحقن الأنظمة

### 3.3 اختبارات وحدة — GRC Engine
- [ ] `tests/test_pdpl_checker.py` — اختبار `scan_text()` لكشف الهوية الوطنية، رقم الجوال، IBAN
- [ ] `tests/test_nca_checker.py` — اختبار فحص السجلات

### 3.4 اختبارات وحدة — مشتركة
- [ ] `tests/test_shared_utils.py` — اختبار `_normalize_content()`, `_safe_text()`
- [ ] `tests/test_chromadb_search.py` — اختبار منطق البحث الموحد

### 3.5 اختبارات وحدة — File Watchers
- [ ] `tests/test_file_watcher.py` — اختبار مراقبة الملفات وإعادة المحاولة
- [ ] `tests/test_knowledge_watcher.py` — اختبار فحص PDPL ورفع الملفات

### 3.6 إعداد CI/CD
- [ ] إنشاء `.github/workflows/test.yml` لتشغيل pytest تلقائياً
- [ ] إضافة `ruff` + `black` في `pyproject.toml` مع إعدادات مناسبة

---

## الجزء 4 — إدارة الاعتماديات 🔵
### الوكيل: Ling 2.6 Flash Free Free

### 4.1 توحيد ملفات الاعتماديات
- [ ] إنشاء `pyproject.toml` مركزي مع مجموعات:
  - `[project.dependencies]` — اعتماديات أساسية
  - `[project.optional-dependencies.pipelines]` — اعتماديات pipelines
  - `[project.optional-dependencies.data-pipeline]` — اعتماديات data_pipeline
  - `[project.optional-dependencies.dev]` — pytest, ruff, black, mypy
- [ ] تثبيت إصدارات دقيقة في `pipelines/requirements.txt` (استبدال `>=` بـ `==`)
- [ ] إنشاء `requirements.lock` أو `pip freeze > requirements-lock.txt`

### 4.2 تنظيف المستودع
- [ ] إضافة `archive/` إلى `.gitignore` أو تقليل حجمه
- [ ] إزالة `__pycache__/` المتبقية
- [ ] مراجعة الاعتماديات غير المستخدمة في كل `requirements.txt`

### 4.3 إعداد أدوات التطوير
- [ ] إضافة `[tool.ruff]` في `pyproject.toml` مع قواعد مناسبة
- [ ] إضافة `[tool.black]` في `pyproject.toml`
- [ ] إضافة `[tool.pytest.ini_options]` في `pyproject.toml`
- [ ] إنشاء `.pre-commit-config.yaml` اختياري

---

## الجزء 5 — معمارية 🟢
### الوكيل: MiniMax M2.5 Free Free

### 5.1 توحيد خدمات الـ Watchers
- [ ] توثيق الفرق بين `file_watcher/watcher.py` و `services/knowledge_watcher/watcher.py`
- [ ] إما دمجهما في خدمة واحدة أو إضافة تنسيق واضح بينهما
- [ ] تحديث `docker-compose.yml` ليعكس التوحيد

### 5.2 توحيد أسماء مجموعات ChromaDB
- [ ] إنشاء `shared/constants.py` يحتوي على:
  - `DEFAULT_COLLECTION_NAME = "saleh_knowledge_qwen3"`
  - `DEFAULT_EMBEDDING_MODEL = "qwen3-embedding:0.6b"`
  - `DEFAULT_EMBEDDING_DIMENSIONS = 1024`
- [ ] استبدال جميع القيم الصلبة في الكود بالثوابت المشتركة

### 5.3 خطة تحسين n8n Workflows
- [ ] توثيق خطة لنقل منطق JavaScript المضمّن في JSON إلى Python scripts خارجية
- [ ] إنشاء قالب لـ n8n workflow يستدعي Python script بدل كود JavaScript مضمّن

### 5.4 توحيد لغة الكود
- [ ] وضع دليل أسلوب: أسماء المتغيرات والدوال بالإنجليزية، التعليقات والتوثيق بالعربي
- [ ] إنشاء `CONTRIBUTING.md` بالقواعد

### 5.5 مراجعة GRC Engine
- [ ] تحديد حالة كل وحدة:
  - NCA: يعمل جزئياً (regex فقط) — يحتاج تطوير
  - PDPL: `scan_text()` يعمل، `run_checks()` stub — يحتاج تنفيذ
  - CITC: stub بالكامل — يحتاج تنفيذ أو إزالة
- [ ] إنشاء خارطة طريق لتطوير أو إزالة الوحدات غير المكتملة

---

## الجزء 6 — مراجعة نهائية ⚪
### الوكيل: Nemotron 3 Super Free Free

### 6.1 مراجعة نتائج الوكلاء الخمسة
- [ ] التحقق من عدم وجود تعارضات بين التعديلات
- [ ] مراجعة الكود المُعاد هيكلته (refactored)
- [ ] التأكد من أن جميع الاختبارات تنجح

### 6.2 فحص أمني نهائي
- [ ] `git log --all --full-history -- .env` — التأكد من إزالة `.env` من التاريخ
- [ ] `grep -r "sk-" pipelines/ scripts/ core/` — التأكد من عدم وجود مفاتيح مكشوفة
- [ ] `grep -r "password\|secret\|token" --include="*.py" --include="*.yml"` — فحص نهائي

### 6.3 تشغيل الاختبارات والبناء
- [ ] `pytest tests/ -v`
- [ ] `ruff check .`
- [ ] `black --check .`
- [ ] `docker-compose build --dry-run` (إن أمكن)

---

## ترتيب التنفيذ

```
المرحلة 1 (فوري):      Big Pickle Free — أمنية حرجة
المرحلة 2 (بعد 1):     GPT-5 Nano Free — جودة الكود
المرحلة 3 (بعد 2):     Hy3 preview Free Free — اختبارات
المرحلة 4 (بالتوازي):  Ling 2.6 Flash Free Free — إدارة الاعتماديات
المرحلة 5 (بعد 2-3):   MiniMax M2.5 Free Free — معمارية
المرحلة 6 (نهائي):     Nemotron 3 Super Free Free — مراجعة نهائية
```

> ملاحظة: الأجزاء 2 و 3 و 4 يمكن تنفيذها بالتوازي بعد إكمال الجزء 1 (الأمنية).