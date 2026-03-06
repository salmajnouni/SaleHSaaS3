# دليل تثبيت واستخدام الـ Pipelines في SaleHSaaS

## نظرة عامة

الـ **Pipelines** هي الجسر الذي يربط نماذج Open WebUI الخبيرة بـ n8n وأي تطبيق خارجي. كل Pipeline تظهر كـ "نموذج" في `/v1/models` وتمرر الطلبات للنموذج الخبير المناسب مع حقن السياق المتخصص تلقائياً.

---

## الـ Pipelines المتاحة

| الملف | الاسم | النموذج الأساسي | التخصص |
|-------|-------|-----------------|---------|
| `n8n_expert_pipeline.py` | 🔄 n8n Automation Expert | deepseek-r1:7b | تصميم workflows، JSON، cron |
| `legal_expert_pipeline.py` | ⚖️ Legal Compliance Expert | llama3.1:8b | الأنظمة السعودية، PDPL، NCA |
| `financial_expert_pipeline.py` | 💰 Financial Intelligence Expert | llama3.1:8b | التحليل المالي، VAT، SOCPA |
| `hr_expert_pipeline.py` | 👥 HR Management Expert | llama3.1:8b | نظام العمل، الرواتب، الإجازات |
| `cybersecurity_expert_pipeline.py` | 🛡️ Cybersecurity Expert | deepseek-r1:7b | NCA-ECC، ISO 27001، OWASP |
| `social_media_expert_pipeline.py` | 📱 Social Media Expert | llama3.1:8b | المحتوى العربي، التسويق الرقمي |
| `orchestrator_pipeline.py` | 🎯 SaleHSaaS Orchestrator | (توجيه ذكي) | يوجه للخبير المناسب تلقائياً |

---

## خطوات التثبيت

### الخطوة 1: التأكد من تشغيل الخدمات

```powershell
# في مجلد D:\SaleHSaaS3
docker-compose up -d open-webui pipelines
docker-compose ps
```

### الخطوة 2: الحصول على API Key

1. افتح `http://localhost:3000`
2. اذهب إلى **Settings** > **Account** > **API Keys**
3. انقر **Create new secret key**
4. احفظ المفتاح

### الخطوة 3: تثبيت الـ Pipelines

#### الطريقة أ — Python (موصى به)

```bash
cd D:\SaleHSaaS3\pipelines
python install_pipelines.py
# أدخل API Key عند الطلب
```

#### الطريقة ب — PowerShell

```powershell
cd D:\SaleHSaaS3\pipelines
.\install_pipelines.ps1 -ApiKey "sk-your-api-key"
```

#### الطريقة ج — يدوياً من واجهة Open WebUI

1. افتح `http://localhost:3000`
2. اذهب إلى **Admin Panel** > **Pipelines**
3. انقر **Upload a pipeline**
4. ارفع كل ملف `.py` من مجلد `pipelines/`

### الخطوة 4: إنشاء النماذج الخبيرة

```bash
cd D:\SaleHSaaS3\pipelines
python create_expert_models.py
# أدخل API Key عند الطلب
```

---

## التحقق من التثبيت

```bash
# قائمة الـ Pipelines المثبتة
curl -H "Authorization: Bearer YOUR_API_KEY" \
     http://localhost:3000/api/v1/pipelines/list

# قائمة النماذج (تشمل الـ Pipelines)
curl -H "Authorization: Bearer YOUR_API_KEY" \
     http://localhost:3000/api/v1/models
```

---

## الاستخدام من n8n

### 1. إعداد Credentials في n8n

في n8n، أضف Credential من نوع **OpenAI API**:
- **Base URL**: `http://n8n_bridge:3333/v1`
- **API Key**: `salehsaas-bridge-key`

### 2. استخدام Pipeline في Workflow

في عقدة **AI Agent** أو **OpenAI Chat Model**:
- اختر الـ Credential المضافة
- في حقل **Model**: اكتب اسم الـ Pipeline مثل `n8n-expert-pipeline`

### 3. مثال على Workflow

```json
{
  "nodes": [
    {
      "type": "@n8n/n8n-nodes-langchain.openAi",
      "parameters": {
        "model": "n8n-expert-pipeline",
        "messages": {
          "values": [
            {
              "role": "user",
              "content": "صمم workflow لإرسال تقرير يومي عبر البريد الإلكتروني"
            }
          ]
        }
      }
    }
  ]
}
```

---

## إعداد متغيرات البيئة للـ Pipelines

في ملف `.env` في مجلد `D:\SaleHSaaS3`:

```env
# API Key لـ Open WebUI (يُستخدم من الـ Pipelines)
OPENWEBUI_API_KEY=sk-your-api-key-here

# عنوان Open WebUI الداخلي (للـ Pipelines داخل Docker)
OPENWEBUI_BASE_URL=http://open-webui:8080
```

في `docker-compose.yml`، تأكد من وجود هذا في خدمة `pipelines`:

```yaml
pipelines:
  environment:
    - OPENWEBUI_API_KEY=${OPENWEBUI_API_KEY}
    - OPENWEBUI_BASE_URL=http://open-webui:8080
```

---

## بنية الـ Pipeline

كل Pipeline تتبع نفس البنية:

```python
class Pipeline:
    class Valves(BaseModel):
        # إعدادات قابلة للتعديل من واجهة Open WebUI
        OPENWEBUI_BASE_URL: str = "http://open-webui:8080"
        OPENWEBUI_API_KEY: str = os.getenv("OPENWEBUI_API_KEY", "")
        EXPERT_MODEL_ID: str = "expert-model-name"

    def __init__(self):
        self.name = "اسم الـ Pipeline"
        self.id = "pipeline-id"

    def pipe(self, user_message, model_id, messages, body):
        # 1. حقن السياق المتخصص
        # 2. إرسال الطلب لـ Open WebUI
        # 3. إعادة الرد مع دعم Streaming
```

---

## الـ Orchestrator — المنسق الذكي

الـ **Orchestrator Pipeline** يحلل الطلب تلقائياً ويوجهه للخبير المناسب:

| الكلمات المفتاحية | الخبير الموجَّه |
|------------------|----------------|
| n8n، workflow، أتمتة | 🔄 n8n Expert |
| قانون، نظام، امتثال | ⚖️ Legal Expert |
| مالي، محاسبة، ضريبة | 💰 Financial Expert |
| موارد بشرية، راتب، إجازة | 👥 HR Expert |
| أمن، سيبراني، ثغرة | 🛡️ Cybersecurity Expert |
| تويتر، محتوى، تسويق | 📱 Social Media Expert |

---

## استكشاف الأخطاء

### المشكلة: الـ Pipeline لا تظهر في القائمة

```bash
# تحقق من سجلات خدمة pipelines
docker-compose logs pipelines --tail=50
```

### المشكلة: خطأ في الاتصال بـ Open WebUI

تأكد من:
1. أن `OPENWEBUI_API_KEY` مضبوط في متغيرات البيئة
2. أن `OPENWEBUI_BASE_URL` صحيح (`http://open-webui:8080` داخل Docker)

### المشكلة: النموذج الخبير غير موجود

```bash
# تحقق من النماذج في Ollama
curl http://localhost:11434/api/tags

# ثم أنشئ النماذج الخبيرة
python create_expert_models.py
```

---

## التطوير والتحسين

لإضافة Pipeline جديدة:

1. انسخ أي Pipeline موجودة كقالب
2. عدّل `self.name`، `self.id`، والـ `EXPERT_MODEL_ID`
3. عدّل دالة `_inject_*_context()` لحقن السياق المناسب
4. ارفع الملف عبر `install_pipelines.py`

---

*آخر تحديث: مارس 2026 — SaleHSaaS v4.0*
