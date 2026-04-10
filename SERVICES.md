## 🕋 System Services - خدمات النظام

This document provides a detailed overview of all services running within the SaleH SaaS Docker ecosystem.

> Runtime note: this file describes the current services defined in `docker-compose.yml`. Historical or optional components should not be treated as active unless they appear there.

> Cancellation note: the `mcpo` path is cancelled in this project and is not part of current runtime services.
> Legacy note: any historical `mcpo` materials are outside the active runtime and must not be treated as operational dependencies.

| Service Name | Container Name | Port (Host:Container) | Description (الوصف) |
| :--- | :--- | :--- | :--- |
| **Open WebUI** | `salehsaas_webui` | `3000:8080` | **(واجهة المحادثة)** الواجهة الرئيسية للمحادثة، البحث، وRAG. |
| **PostgreSQL** | `salehsaas_postgres` | داخلي | **(قاعدة البيانات)** قاعدة بيانات Open WebUI و n8n. |
| **Data Pipeline** | `salehsaas_data_pipeline` | `8001:8001` | **(خط أنابيب البيانات)** API لاستقبال الملفات، التقطيع، وتخزينها في ChromaDB. |
| **Knowledge Watcher** | `salehsaas_watcher` | داخلي | **(مراقب الملفات)** خدمة خلفية تراقب `knowledge_inbox` وتستدعي `data_pipeline`. |
| **ChromaDB** | `salehsaas_chromadb` | `8010:8000` | **(قاعدة البيانات المتجهية)** The vector database used for storing document chunks and enabling semantic search. | 
| **n8n** | `salehsaas_n8n` | `5678:5678` | **(الأتمتة)** إدارة وتنفيذ سير العمل. |
| **Apache Tika** | `salehsaas_tika` | داخلي | **(استخراج النص)** استخراج النص من PDF و Word وملفات أخرى. |
| **SearXNG** | `salehsaas_searxng` | داخلي | **(البحث المحلي)** محرك بحث محلي مدمج مع WebUI. |
| **Browserless** | `salehsaas_browser` | `3001:3000` | **(متصفح آلي)** خدمة متصفح بلا واجهة للمهام التي تحتاج تنفيذًا متصفحياً. |
| **Open Terminal** | `salehsaas_open-terminal` | `8000:8000` | **(الطرفية الداخلية)** بيئة طرفية مرتبطة بالمجلد المحلي `saleh/`. |

### خدمات خارجية (WSL2)

| Service Name | Host | Port | Description (الوصف) |
| :--- | :--- | :--- | :--- |
| **sanirejal API** | WSL2 (Ubuntu-22.04) | `8500` | **(إدارة التدريب)** REST API لإدارة ومراقبة تدريب نموذج autoresearch على GPU. |

### API Endpoints

#### Data Pipeline (`http://localhost:8001`)

- `POST /process-file/`: Processes a single uploaded file.
- `GET /health`: Checks the health of the pipeline service.

#### Open WebUI (`http://localhost:3000`)

- واجهة المستخدم الرئيسية للمحادثة وRAG.
- لا يوجد في هذا المستودع توثيق معتمد لـ REST API خاص بـ Open WebUI؛ أي تكامل يجب أن يتحقق من الوثائق الرسمية أو من الخدمة الحية مباشرة.

#### n8n (`http://localhost:5678`)

- `GET /api/v1/workflows`: جلب قائمة سير العمل.
- `POST /api/v1/workflows`: إنشاء سير عمل جديد.
- `PATCH /api/v1/workflows/{id}`: تحديث سير عمل موجود.
- `POST /api/v1/workflows/{id}/activate`: تفعيل سير عمل.
- `GET /api/v1/executions`: جلب سجل التنفيذات.

#### Open Terminal (`http://localhost:8000`)

- يستخدم كطرفية داخلية، وليس كبديل لـ Open WebUI.
- المجلد المحلي `saleh/` يظهر بداخله على المسار `/home/user/projects`.

#### sanirejal API (`http://localhost:8500`) — WSL2

- `GET /health`: فحص حالة الخدمة.
- `GET /status`: حالة التدريب الحالية (running/stopped، الخطوة، loss).
- `GET /logs`: آخر سطور سجل التدريب.
- `GET /loss_history`: سجل تاريخ قيم الخسارة.
- `GET /gpu`: معلومات GPU (ROCm/AMD).
- `GET /config`: المعاملات الفائقة الحالية للتدريب.
- `POST /train/start`: بدء جلسة تدريب جديدة.
- `POST /train/stop`: إيقاف التدريب الجاري.
