## [4.2.0] - 2026-03-02

### تحسينات الأمان والأداء
- تعطيل التسجيل التلقائي (ENABLE_SIGNUP=false) لمنع الوصول غير المصرح
- تثبيت إصدارات الصور: Open WebUI v0.6.5، Pipelines v0.6.5، n8n 2.9.4
- ضبط n8n لحفظ بيانات الأخطاء فقط (EXECUTIONS_DATA_SAVE_ON_SUCCESS=none)
- تفعيل تنظيف سجلات التنفيذ تلقائياً بعد 7 أيام (EXECUTIONS_DATA_MAX_AGE=168)

# Changelog

## [4.3.3] - 2026-03-30

### توثيق تشغيلي
- إضافة طبقة تحذير وتصحيح تشغيلي في `dev_studio/knowledge/07_salehsaas_project.md` و `dev_studio/knowledge/08_openwebui_guide.md` و `USER_GUIDE_AR.md` لمنع اعتماد الوكلاء على وصف قديم أو تجريبي.
- إزالة أكثر السطور المضللة مباشرة من ملفات المعرفة الداخلية ودليل المستخدم، خصوصًا ما يتعلق بـ `mcpo` و `Code Server` و `saleh_legal_knowledge` و `AnythingLLM`.
- إضافة وثيقة مرجعية مختصرة: `الحقائق التشغيلية الحاكمة - v0.1.md` وربطها بالوثائق الأساسية لتكون مرجعًا سريعًا قبل اتخاذ القرار.
- تصحيح `docs/guides/sbc_rag_bootstrap.md` بحيث يشير نجاح الاستيعاب إلى `knowledge_processed/` بدل المسار القديم.
- ربط وثائق الخدمات والجودة والأدلة المتخصصة بالمرجع الحاكم حتى لا تُقرأ كمصدر مستقل لحقيقة التشغيل التقني.
- إضافة تنبيهات موحدة على ملفات `dev_studio/knowledge` العامة حتى لا يخلط الوكيل بين المعرفة التعليمية العامة وحقيقة التشغيل الحالية.
- تنظيف الجذر من الضوضاء الصغيرة عبر نقل `temp_doc_code_report.txt` و `temp_uncoded_groups.txt` و `temp_wf.json` إلى حزمة حفظ تاريخية خارج المسار الحي.
- نقل `test_results.json` إلى حزمة نواتج تاريخية باعتباره ناتج اختبار مولدًا.
- إزالة `__pycache__/` من الجذر، ونقل ملفات التحقق والنصوص المتناثرة من المجلد الحي `saleh/` إلى حفظ تاريخي خارج المسار الحي.
- توسيع تنظيف الكاش ليشمل جميع مجلدات `__pycache__` المولدة داخل المشروع خارج `.venv`، بما في ذلك المسارات البرمجية النشطة وبعض بقايا الأرشيف المؤقت.
- تثبيت فرق تشغيلي إضافي في الوثائق: watcher الحي الحالي هو `file_watcher/watcher.py`، و`knowledge_processing/` ليس مسار نجاح حيًا، بينما `knowledge_archive/` يبقى مستخدمًا لأرشفة مرجعية مثل مخرجات UQN.
- تثبيت أن `saleh_dashboard/` مشروع قديم/مرجعي غير مفعل في التشغيل الحالي، مع تحذير صريح داخل ملفاته ومنع الخلط بينه وبين واجهة `Open WebUI` الحية.
- إضافة تقييم مستقل لإعادة `AnythingLLM` كخدمة اختيارية مستقبلية، مع حفظ الأصول المتبقية والمخاطر وشروط الإرجاع المنضبط دون خلطه بالتشغيل الحالي.
- إضافة تحذيرات تشغيلية صريحة داخل ملفات Legacy ذات الخطورة المعرفية (`INSTALL_GUIDE.md` و `scripts/windows/SETUP_SALEHSAAS3.ps1` و `scripts/windows/SETUP_SALEHSAAS3.bat` و `saleh_brain/agent.py`) لمنع قراءتها كمرجع حاكم للتشغيل الحالي.
- إغلاق دفعة تضليل إضافية: تصحيح منفذ `AnythingLLM` التاريخي في `USER_GUIDE_AR.md` إلى `3002`، وتحديث تسميات `setup.ps1` و `final_system_report.py` من `Code Server` إلى `Open Terminal` على `8000`، مع تحذيرات Legacy في سكربتات التثبيت القديمة.
- تحسين مخرجات سكربتات Windows القديمة (`SETUP_SALEHSAAS3.ps1` و `SETUP_SALEHSAAS3.bat` و `INSTALL_SALEHSAAS.bat`) لتفصل بوضوح بين Profile Legacy والتشغيل الحالي المتحقق، وتصحيح فتح الواجهة الافتراضية إلى `Open WebUI`.
- تشديد إضافي على مخرجات التثبيت القديمة: إزالة عرض الخدمات غير المفعلة من قائمة الخدمات الجاهزة، وقصر القائمة على الخدمات الحية الحالية مع إبقاء `AnythingLLM` و`Code Server` و`Grafana` كخيارات Legacy اختيارية فقط.
- توسيع وسم Legacy/Optional في ملفات الإعداد المرجعية (`.env.example` و `SETUP_SALEHSAAS3.ps1` و `SETUP_SALEHSAAS3.bat` و `INSTALL_GUIDE.md` و `dev_studio/README.md`) لتقليل أي خلط بين المسارات الاختيارية والتشغيل الأساسي الحالي.
- إضافة وسم Legacy/Optional صريح على إعدادات `mcpo` و`Qdrant` و`Dashboard` داخل قوالب البيئة وسكربتات الإعداد القديمة حتى لا تُفهم كخدمات تشغيل افتراضية حالية.
- دفعة تحصين إضافية للملفات المتبقية عالية الخطورة: تحويل `MCP_SETUP_GUIDE.md` لصياغة تاريخية صريحة، وتشديد تنبيه `dev_studio/README.md`، وتوسيم `docs/guides/TECHNICAL_ROADMAP_ENGINEERING.md` كخارطة منتج غير حاكمة للتشغيل.
- مواءمة سكربتات الإدخال القانونية (`auto_update_laws.py` و `scripts/uqn_scraper.py`) مع افتراضات التشغيل الحي عبر `CHROMA_COLLECTION=saleh_knowledge` و`EMBEDDING_MODEL=nomic-embed-text:latest` مع إبقاء قابلية override بالبيئة.
- إضافة guard آمن في `apply_n8n_builder.ps1` لمنع محاولة تشغيل مسار `mcpo` عندما لا تكون الخدمة مفعلة، مع رسالة إرشادية بدل فشل مضلل.
- تحصين سكربتات Legacy التقنية المتبقية: جعل `scripts/fix_vectordb2.js` لا يعمل إلا بتفعيل صريح عبر `ALLOW_LEGACY_ANYTHINGLLM_FIX=true`.
- تقليل التضليل في `saleh_brain/agent.py` عبر إزالة افتراض مراقبة `AnythingLLM/Redis` افتراضيًا، واعتماد قائمة خدمات حرجة قابلة للتخصيص عبر `CRITICAL_SERVICES`.
- توضيح مسار `scripts/reembed_qwen3.py` كمسار ترحيل اختياري قديم، مع دعم override للهدف عبر `TARGET_COLLECTION` و`TARGET_EMBED_MODEL`.
- تشديد سكربت `scripts/windows/INSTALL_CONTINUE.bat` بإيقافه افتراضيًا ما لم يُفعَّل صراحة عبر `ALLOW_LEGACY_CODE_SERVER=true`، مع تحقق مسبق من تشغيل الحاوية `salehsaas_code_server` لتجنب تنفيذ مضلل.
- تحسين صياغة `MCP_SETUP_GUIDE.md` عند مثال `Server URL` لتأكيد أنه مثال تاريخي لمسار اختياري وليس دلالة على خدمة مفعلة حاليًا.
- تحسين `docs/guides/mep_summary_only_rag.md` لتوسيم `saleh_knowledge_qwen3` كمسار ترحيل legacy يتطلب override موثق، بدل فهمه كمسار افتراضي.
- إضافة قسم مرجعي مباشر داخل `دليل السياسات والإجراءات - نظام الوكلاء الذكيين.md` يحدد بوضوح ملفات القرار التشغيلي الآمنة مقابل الملفات السياقية/الاختيارية.
- مواءمة سكربتات الإعداد القديمة على Windows (`SETUP_SALEHSAAS3.ps1` و`SETUP_SALEHSAAS3.bat`) مع مسار التضمين الحي عبر `nomic-embed-text:latest` بدل سحب `qwen3-embedding` تلقائياً.
- جعل تنزيل `qwen3-embedding:0.6b` في سكربتات الإعداد القديمة اختياريًا فقط عبر opt-in صريح: `ALLOW_LEGACY_QWEN3=true`.
- تحسين رسالة النجاح في `INSTALL_SALEHSAAS.bat` لإزالة اللبس حول Profile Legacy وتثبيت قاعدة أن المرجع الأعلى هو `docker-compose.yml`.
- تثبيت قرار تشغيلي جديد: `mcpo` مسار ملغى حاليًا في المشروع (Cancelled)، وليس مجرد خدمة غير مفعلة.
- تحويل `apply_n8n_builder.ps1` إلى سكربت ملغى يتوقف مباشرة بدون تنفيذ خطوات MCPO.
- تحديث الوثائق الحاكمة (`README.md`, `ARCHITECTURE.md`, `MCP_SETUP_GUIDE.md` حينها، `الحقائق التشغيلية الحاكمة - v0.1.md`, `دليل السياسات والإجراءات - نظام الوكلاء الذكيين.md`) لتوصيف `mcpo` كمسار ملغى.
- تدقيق لغوي نهائي للملفات الحاكمة مع تثبيت صياغة `MCP_SETUP_GUIDE.md` كمرجع تاريخي غير قابل للتنفيذ في التشغيل الحالي.
- إضافة توضيح تشغيلي مباشر في `SERVICES.md` بأن مسار `mcpo` ملغى وغير داخل خدمات التشغيل الحالية.
- وسم `docker/mcpo/Dockerfile` كأثر تاريخي فقط لمنع تفسيره كمكوّن runtime نشط.
- إضافة بطاقة مرجعية سريعة `RUNTIME_STATUS_CARD.md` لتحديد الخدمات الحية مقابل المسارات الملغاة/Legacy وتثبيت ترتيب فضّ التعارض بين الوثائق.
- توحيد الصياغة الرسمية في الوثائق الحاكمة إلى: `mcpo` مسار/خدمة ملغاة في التشغيل الحالي.
- إضافة توضيح مباشر للمسار البديل بعد إلغاء `mcpo`: الاعتماد على `pipelines` و`data_pipeline` في `README.md` ورسالة `apply_n8n_builder.ps1`.
- تشديد `MCP_SETUP_GUIDE.md` بإضافة نص صريح أن البديل التشغيلي الحالي هو `pipelines` و`data_pipeline`، وتحويل المقدمة الإجرائية إلى صيغة تاريخية بالكامل.
- إضافة قسم مستقل داخل `MCP_SETUP_GUIDE.md` بعنوان "المسار التشغيلي البديل الحالي" يوضح المنافذ والخدمات الفعلية (`Open WebUI`/`pipelines`/`data_pipeline`).
- تعزيز `MCP_SETUP_GUIDE.md` بتحذير واضح أنه مرجع تاريخي غير تنفيذي، مع توجيه مباشر لقراءة `RUNTIME_STATUS_CARD.md` و`docker-compose.yml` قبل أي إجراء.
- نقل ملف `MCP_SETUP_GUIDE.md` ومواد `mcpo` القديمة إلى حفظ تاريخي خارج المسار الحي، مع تحديث المراجع الحاكمة المرتبطة به.
- توحيد توثيق المواد التاريخية الخاصة بـ `mcpo` داخل الملفات الحاكمة (`README.md` و`ARCHITECTURE.md` و`SERVICES.md`) لمنع أي لبس بين التشغيل الحالي والمحتوى التاريخي.
- مواءمة ملفات المعرفة الداخلية (`dev_studio/knowledge/07_salehsaas_project.md` و`dev_studio/knowledge/08_openwebui_guide.md`) لتثبيت أن مواد `mcpo` أصبحت تاريخية وخارج الشجرة التشغيلية الحية.
- استكمال المواءمة في الوثائق الحاكمة المرجعية: إضافة توضيح صريح بشأن خروج مواد `mcpo` من المسار التشغيلي الحي داخل `الحقائق التشغيلية الحاكمة - v0.1.md` و`دليل السياسات والإجراءات - نظام الوكلاء الذكيين.md`.
- تحييد لبس `Code Server` في التوثيق الحي: تشديد `dev_studio/README.md` و`INSTALL_GUIDE.md` وخريطة `dev_studio/knowledge/07_salehsaas_project.md` لتأكيد أنه مسار تطوير اختياري منفصل وليس جزءًا من runtime الأساسي.
- توحيد مرجع `AnythingLLM` في الوثائق الحية بحيث يبقى غير مفعّل حاليًا، ويُحال أي تقييم مستقبلي له حصريًا إلى `docs/guides/anythingllm_optional_return_assessment.md`.
- مواءمة سكربتات Python المساعدة في الجذر مع مسار التضمين الحي: تحديث `run_scraper_now.py` و`test_rag.py` لاستخدام `EMBEDDING_MODEL` مع افتراضي `nomic-embed-text:latest`.
- إضافة قفل أمان تدميري في `scripts/cleanup_chromadb.py` بحيث لا ينفذ إلا عند التفعيل الصريح `ALLOW_LEGACY_CHROMA_CLEANUP=true`.

## [4.3.2] - 2026-03-30

### توثيق الحوكمة
- إضافة كود وثيقة مسودة لملف الأمانة: `DRAFT-GOV-CHARTER-001` بإصدار `v0.1`.
- إضافة سجل تغييرات داخل ملف الأمانة لتتبع أي تعديل لاحق بشكل رسمي.

## [4.3.1] - 2026-03-03

### إصلاح mcpo - إضافة n8n_builder
- تحديث تعليقات docker-compose.yml لتشمل n8n_builder في قائمة أدوات mcpo
- تحديث label salehsaas.description لـ mcpo

## [4.3.0] - 2026-03-03

### توحيد البنية (Structure Unification)
- إضافة مجلدات knowledge_inbox/processed/processing/failed/archive مع .gitkeep
- تحديث .gitignore: استثناء محتوى مجلدات knowledge مع الحفاظ على البنية
- إضافة chromadb_data/ و n8n_data/ إلى .gitignore
- إضافة مجلد n8n_workflows/ مع README توضيحي للمسار الصحيح

All notable changes to SaleH SaaS are documented in this file.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [4.1.3] - 2026-03-02

### Fixed
- **SearXNG radio_browser (final fix)**: Replaced `disabled: true` approach with `use_default_settings.engines.remove` directive. This is the correct SearXNG API to prevent engines from loading entirely - they are removed before initialization, not just flagged as disabled. Eliminates `socket.herror: No address associated with name` crash permanently.

---

## [4.1.2] - 2026-03-02

### Fixed
- **n8n crash**: Removed `N8N_RUNNERS_MODE=external` which caused fatal error `Missing auth token`. n8n now runs in default internal mode (JS runner only). Python runner warning is informational only and does not affect functionality.
- **SearXNG radio_browser**: Added explicit `engine: radio_browser` field alongside `disabled: true` to ensure SearXNG correctly matches and disables the engine before initialization.

---

## [4.1.1] - 2026-03-02

### Fixed
- **Open WebUI CORS**: Replaced `CORS_ALLOW_ORIGIN` with correct `WEBUI_URL` variable that Open WebUI actually reads for allowed origins. Eliminates `http://localhost:3000 is not an accepted origin` error.
- **SearXNG radio_browser**: Changed strategy from `keep_only` to explicit `disabled: true` per engine. Eliminates `socket.herror: No address associated with name` crash on startup.
- **n8n Python runner**: Added `N8N_RUNNERS_MODE=external` to suppress `Failed to start Python task runner in internal mode` warning.

---

## [4.1.0] - 2026-03-02

### Fixed
- **SearXNG limiter.toml**: Created `config/searxng/limiter.toml` to resolve startup warning. Configured to allow all Docker network IPs (172.20.0.0/16).
- **SearXNG engines**: Updated `settings.yml` to use `keep_only` strategy, disabling failed engines (ahmia, torch, radio_browser) and keeping only stable ones (google, bing, duckduckgo, wikipedia, brave).
- **Open WebUI CORS**: Replaced wildcard `CORS_ALLOW_ORIGIN=*` with explicit `http://localhost:3000,http://127.0.0.1:3000`.
- **Open WebUI USER_AGENT**: Added `USER_AGENT` environment variable to identify requests from langchain.
- **n8n deprecation**: Removed deprecated `N8N_RUNNERS_ENABLED=true` variable (no longer needed in n8n v2.9+).

---

## [4.0.0] - 2026-03-02

### Added
- **Dockerfile.tika**: Custom Tika image with Microsoft TrueType core fonts (Arial, Times New Roman, Helvetica, Courier New). Eliminates all `Using fallback font LiberationSans` PDFBox warnings.
- **n8n_builder MCP Tool** (`tools/mcp/n8n_builder.py`): 10-function MCP tool enabling AI models to create, manage, activate, and execute n8n workflows from natural language chat.
- **n8n Public API**: Enabled `N8N_PUBLIC_API_DISABLED=false` and configured `N8N_API_KEY` for programmatic workflow management.
- **Knowledge Watcher v3.0** (`services/knowledge_watcher/watcher.py`): Professional document ingestion pipeline with automatic monitoring, Tika extraction, Ollama embeddings (300s timeout), ChromaDB v2 storage, and date-based archival.
- **mcpo config** (`config/mcpo/config.json`): Three registered MCP tools: `ollama_model_builder`, `saleh_legal_rag`, `n8n_builder`.

### Fixed
- **ChromaDB v2 API**: Migrated from deprecated v1 to full v2 path `/api/v2/tenants/default_tenant/databases/default_database/`.
- **ChromaDB UUID addressing**: Collection add operations now use UUID-based endpoint.
- **Ollama timeout**: Increased to 300 seconds for large document chunks.
- **PowerShell encoding**: All log messages in English to prevent Unicode issues on Windows.
- **File re-queue**: Crash-proof using copy+delete instead of move.

### Changed
- **docker-compose.yml**: `tika` service builds from `Dockerfile.tika`, image tagged `salehsaas-tika-fonts:latest`.
- **Knowledge Watcher**: Removed `IGNORE_FILENAMES` — inbox processes all files by design.
- **Documentation**: Consolidated knowledge watcher docs into `docs/guides/knowledge_watcher.md`.

---

## [3.0.0] - 2026-03-01

### Added
- **MCP Setup Guide** (`MCP_SETUP_GUIDE.md` حينها، ثم أُخرج لاحقًا من المسار الحي): Complete guide for configuring MCP tools in Open WebUI.
- **saleh_legal_rag MCP Tool**: Semantic search over ingested legal documents.
- **ollama_model_builder MCP Tool**: Manage Ollama models from chat.
- **mcpo service**: MCP-to-OpenAPI proxy at port `8020`.
- **n8n workflows folder** (`n8n/workflows/`): Pre-built workflow templates.
- **Pipelines**: `saleh_legal_pipeline.py` and `saleh_legal_rag.py` for RAG-enhanced processing.
- **Legal Glossary**: Saudi legal terminology database in `saleh_brain/glossary/`.

### Changed
- Architecture expanded to 10 services.
- PostgreSQL added as persistent backend for n8n.

---

## [2.0.0] - 2026-03-01

### Added
- **Smart Chat API**: Full RAG pipeline with Llama 3 and ChromaDB.
- **Dashboard v2.0**: New UI with 4 tabs (Overview, Chat, Search, Files).
- **Ollama Embeddings Search**: Uses `nomic-embed-text` via Ollama.

### Changed
- Dashboard port changed from `8088` to `8000`.
- Improved logging in `file_watcher`.

---

## [1.0.0] - 2026-03-01

### Added
- **Initial System**: Data Pipeline, File Watcher, ChromaDB, Ollama, and AnythingLLM.
- **Dashboard v1.0**: Basic monitoring dashboard.
- **File Watcher Service**: Automated file processing from the `incoming` folder.
- **Data Pipeline**: Initial version for processing and storing documents.
