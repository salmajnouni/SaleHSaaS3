# دليل الـ Pipelines الاحترافي — SaleHSaaS

> **ملاحظة مهمة**: تم إعادة كتابة جميع الـ Pipelines في مارس 2026 لتصحيح خطأ جذري.
> الإصدار الجديد يستدعي **Ollama مباشرة** وليس Open WebUI.

---

## التشخيص: ما كان خاطئاً وما تم تصحيحه

### الخطأ الجذري في الإصدار السابق

كانت الـ Pipelines تستدعي **Open WebUI** للحصول على نماذج لم تكن موجودة:

```
Pipeline → Open WebUI API → "n8n-expert" (غير موجود!) → فشل
```

هذا يخالف الوثائق الرسمية لـ Open WebUI Pipelines التي تنص صراحةً:

> *"Pipes are standalone functions that process inputs and generate responses,
> possibly by invoking one or more LLMs or external services."*
> — [Open WebUI Pipes Documentation](https://docs.openwebui.com/features/extensibility/pipelines/pipes/)

### البنية الصحيحة (المطبّقة الآن)

```
المستخدم
    ↓
Open WebUI (port 3000)
    ↓ يرسل الطلب لـ Pipelines Server
Pipelines Server (port 9099)  ← هنا تعمل الـ Pipeline
    ↓ تستدعي Ollama مباشرة
Ollama (host.docker.internal:11434)
    ↓
النموذج الفعلي (llama3.1:8b أو deepseek-r1:7b)
```

---

## النماذج الخبيرة المتاحة

| الـ Pipeline | الاسم في Open WebUI | النموذج | التخصص |
|---|---|---|---|
| `n8n_expert_pipeline.py` | 🔄 n8n Automation Expert | deepseek-r1:7b | أتمتة n8n، Workflows، JSON |
| `legal_expert_pipeline.py` | ⚖️ Legal Compliance Expert | llama3.1:8b | الأنظمة السعودية، PDPL، NCA |
| `financial_expert_pipeline.py` | 💰 Financial Intelligence Expert | llama3.1:8b | VAT، الزكاة، SOCPA، التحليل المالي |
| `hr_expert_pipeline.py` | 👥 HR & Workforce Expert | llama3.1:8b | نظام العمل، GOSI، نطاقات |
| `cybersecurity_expert_pipeline.py` | 🛡️ Cybersecurity Expert | deepseek-r1:7b | NCA-ECC، ISO 27001، OWASP |
| `social_media_expert_pipeline.py` | 📱 Social Media & Marketing Expert | llama3.1:8b | المحتوى العربي، التسويق الرقمي |
| `orchestrator_pipeline.py` | 🎯 SaleHSaaS Orchestrator | llama3.1:8b | منسق عام لكل المجالات |

---

## خطوات التثبيت على جهازك

### الخطوة 1: سحب آخر تحديث

```powershell
cd D:\SaleHSaaS3
git pull origin salehsaas5
```

### الخطوة 2: التأكد من تشغيل الخدمات

```powershell
docker compose ps
# يجب أن تكون هذه الخدمات running:
# - open-webui
# - pipelines
```

### الخطوة 3: ربط Pipelines Server بـ Open WebUI

افتح Open WebUI في المتصفح (`http://localhost:3000`):
1. اذهب إلى **Admin Panel > Settings > Connections**
2. في قسم **Pipelines**، أدخل: `http://pipelines:9099`
3. اضغط **Save**

### الخطوة 4: رفع الـ Pipelines

لكل ملف من الملفات السبعة:
1. اذهب إلى **Admin Panel > Settings > Pipelines**
2. اضغط **Upload a pipeline** (أيقونة الرفع)
3. ارفع الملف (مثال: `n8n_expert_pipeline.py`)
4. ستظهر في قائمة النماذج فوراً

### الخطوة 5: التحقق من ظهور النماذج

في Open WebUI، اضغط على قائمة النماذج — يجب أن تجد:
- 🔄 n8n Automation Expert
- ⚖️ Legal Compliance Expert
- 💰 Financial Intelligence Expert
- 👥 HR & Workforce Expert
- 🛡️ Cybersecurity Expert
- 📱 Social Media & Marketing Expert
- 🎯 SaleHSaaS Orchestrator

كل نموذج يظهر بعلامة **"External"** بجانبه.

---

## ضبط الـ Valves (الإعدادات)

كل Pipeline تدعم تغيير الإعدادات من واجهة Open WebUI:

1. اذهب إلى **Admin Panel > Settings > Pipelines**
2. اضغط على أيقونة الإعدادات ⚙️ بجانب الـ Pipeline
3. يمكنك تغيير:

| الإعداد | الوصف | القيمة الافتراضية |
|---|---|---|
| `OLLAMA_BASE_URL` | عنوان Ollama | `http://host.docker.internal:11434` |
| `MODEL_ID` | النموذج المستخدم | `llama3.1:8b` أو `deepseek-r1:7b` |
| `TEMPERATURE` | درجة الإبداعية | `0.2` – `0.7` |
| `MAX_TOKENS` | الحد الأقصى للرد | `4096` |
| `ENABLE_EXPERT_CONTEXT` | تفعيل حقن السياق | `true` |

---

## استخدام النماذج من n8n

في عقدة **lmChatOpenAi** في n8n:

```
Credential Type: OpenAI API
Base URL: http://n8n_bridge:3333/v1
API Key: salehsaas-bridge-key
Model: n8n-expert
```

**Pipeline IDs للاستخدام في n8n**:

| النموذج الخبير | الـ ID |
|---|---|
| خبير n8n | `n8n-expert` |
| خبير قانوني | `legal-expert` |
| خبير مالي | `financial-expert` |
| خبير موارد بشرية | `hr-expert` |
| خبير أمن سيبراني | `cybersecurity-expert` |
| خبير وسائل التواصل | `social-media-expert` |
| المنسق العام | `orchestrator` |

---

## الفرق بين المسارات الثلاثة في SaleHSaaS

| المسار | الأداة | الغرض | متى تستخدمه |
|---|---|---|---|
| **Pipeline** | `pipelines/*.py` | منطق Python مخصص + Ollama مباشرة | عندما تحتاج معالجة خاصة للبيانات |
| **Custom Model** | Workspace > Models | System prompt فقط، بدون كود | عندما تريد شخصية محددة بسرعة |
| **n8n Workflow** | n8n + Bridge | أتمتة كاملة مع tools وذاكرة | عندما تحتاج تسلسل خطوات معقد |

---

## استكشاف الأخطاء

### المشكلة: النموذج لا يظهر في القائمة

```powershell
# تحقق من سجلات خدمة pipelines
docker compose logs pipelines --tail=50
```

### المشكلة: "تعذّر الاتصال بـ Ollama"

```powershell
# تحقق من Ollama
curl http://localhost:11434/api/tags

# إذا كنت داخل Docker، العنوان الصحيح هو:
# http://host.docker.internal:11434
```

### المشكلة: "model not found" من Ollama

```powershell
# تحميل النماذج المطلوبة
ollama pull llama3.1:8b
ollama pull deepseek-r1:7b
```

### المشكلة: Pipelines Server لا يستجيب

```powershell
# تحقق من تشغيل الخدمة
docker compose restart pipelines
docker compose logs pipelines --tail=20
```

---

## بنية الـ Pipeline الصحيحة (للمطورين)

```python
class Pipeline:
    class Valves(BaseModel):
        OLLAMA_BASE_URL: str = "http://host.docker.internal:11434"
        MODEL_ID: str = "llama3.1:8b"
        TEMPERATURE: float = 0.3

    def __init__(self):
        self.name = "اسم النموذج"   # يظهر في قائمة النماذج
        self.id = "model-id"         # يُستخدم في API calls

    def pipe(self, user_message, model_id, messages, body):
        # استدعاء Ollama مباشرة (وليس Open WebUI!)
        r = requests.post(
            f"{self.valves.OLLAMA_BASE_URL}/api/chat",
            json={"model": self.valves.MODEL_ID, "messages": messages}
        )
        return r.json()["message"]["content"]
```

---

*آخر تحديث: مارس 2026 — SaleHSaaS v5 — بعد المراجعة الاحترافية الشاملة*
