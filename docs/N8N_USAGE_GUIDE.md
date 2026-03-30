# n8n as Universal Tool for All Models & Agents

**n8n الأداة المشتركة لجميع الـ models والـ agents - وليس حكراً على agent واحد**

---

## 🎯 الفلسفة (Philosophy)

- ✅ n8n هي أداة قوية لأتمتة المهام
- ✅ يجب أن تكون **متاحة لجميع الـ agents والـ models**
- ✅ لا حدود على عدد الـ workflows أو الـ agents يقدرون يستخدموها
- ✅ واجهة بسيطة وموحدة للتفاعل معها

---

## 🚀 كيفية الاستخدام

### الطريقة 1: Python API (للـ Python Scripts و Agents)

أبسط وأسهل طريقة:

```python
from scripts.n8n.n8n_api import trigger_webhook, CouncilWorkflow

# تقديم طلب مجلس استشاري
result = CouncilWorkflow.submit_request(
    topic="هل يجب علينا تنفيذ سياسة جديدة؟",
    study_type="legal",  # legal, financial, technical, cyber
    requester="صالح",
    priority="high"  # low, normal, high
)

if result["success"]:
    print("✅ تم التقديم بنجاح")
else:
    print(f"❌ حدث خطأ: {result['error']}")
```

### الطريقة 2: Webhook مباشر

للأنظمة الأخرى أو الخدمات الخارجية:

```bash
curl -X POST http://localhost:5678/webhook/council-intake \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "موضوع الدراسة",
    "study_type": "legal",
    "requested_by": "الاسم",
    "source": "external"
  }'
```

### الطريقة 3: Python Scripts المباشرة

```python
from scripts.n8n.n8n_api import trigger_webhook

# Trigger أي webhook
result = trigger_webhook("council-intake", {
    "topic": "الموضوع",
    "study_type": "legal"
})
```

---

## 📋 الـ Workflows الموجودة حالياً

| ID | اسم | الوصف |
|---|---|---|
| `advisory_council.json` | المجلس الاستشاري | معالجة طلبات المجلس |
| `knowledge_ingestion.json` | إدخال المعرفة | استيراد المعارف والمستندات |
| `saleh_approval_gate.json` | بوابة الموافقة | التحكم في الموافقات |
| `saudi_laws_sync.json` | مزامنة القوانين | تحديث القوانين السعودية |
| `saudi_laws_chat.json` | دردشة القوانين | الإجابة على استفسارات القانون |

---

## 💻 أمثلة عملية

### مثال 1: أي Agent يقدر يرسل طلب للمجلس

```python
# داخل أي agent
class MyAgent:
    def get_council_opinion(self, topic):
        from scripts.n8n.n8n_api import CouncilWorkflow
        
        result = CouncilWorkflow.submit_request(
            topic=topic,
            study_type="legal",
            requester=self.name
        )
        
        return result
```

### مثال 2: Service يستدعي n8n

```python
# From any service
import requests

def send_to_knowledge_base(document):
    response = requests.post(
        "http://localhost:5678/webhook/knowledge-ingestion",
        json={"document": document}
    )
    return response.json()
```

### مثال 3: Batch Processing

```python
from scripts.n8n.n8n_api import CouncilWorkflow

# معالجة عدة طلبات دفعة واحدة
topics = [
    ("موضوع 1", "legal"),
    ("موضوع 2", "financial"),
    ("موضوع 3", "cyber")
]

for topic, study_type in topics:
    CouncilWorkflow.submit_request(
        topic=topic,
        study_type=study_type,
        requester="system"
    )
```

---

## 🔧 مزايا استخدام n8n كأداة عامة

1. **لا توازنات (No Bottlenecks)**: جميع الـ agents يقدرون يستخدموها في نفس الوقت
2. **موثوقية عالية**: n8n يتعامل مع الـ retry و error handling
3. **سهولة التوسع**: إضافة workflows جديدة بدون تغيير في الـ agents
4. **مراقبة مركزية**: جميع العمليات تظهر في dashboard واحد
5. **قابلية المشاركة**: Agents مختلفة تستخدم نفس الـ workflows

---

## 📊 الحالة الحالية

| بند | الحالة |
|---|---|
| n8n Container | ✅ يعمل |
| Python API | ✅ جاهز |
| Webhook Integration | ✅ فعال |
| Council Workflow | ✅ موجود |
| عدد الـ Workflows | 5+ |
| Support للـ Agents | ✅ نعم |

---

## 🚀 كيفية البدء

### خطوة 1: تأكد من تشغيل n8n

```bash
docker ps | grep n8n
```

يجب أن يظهر: `salehsaas_n8n` مع حالة `Up`

### خطوة 2: استخدم الـ API

```python
from scripts.n8n.n8n_api import check_n8n

status = check_n8n()
print(f"n8n Status: {status}")
```

### خطوة 3: أرسل طلب

```python
from scripts.n8n.n8n_api import CouncilWorkflow

result = CouncilWorkflow.submit_request(
    topic="اختبر نظام المجلس",
    study_type="legal",
    requester="test"
)
```

---

## 🆘 استكشاف الأخطاء

### n8n لا يرد على الطلبات

```bash
# تحقق من الـ container
docker logs salehsaas_n8n --tail 50

# تحقق من المنفذ
netstat -an | grep 5678
```

### Webhook لا يعمل

```bash
# اختبر مباشرة
curl http://localhost:5678/webhook/council-intake

# إذا أرجع 404, الـ webhook غير مسجل
# قم بـ restart للـ container
docker restart salehsaas_n8n
```

### Python script لا يعمل

```bash
# تحقق من المكتبات
pip install requests

# اختبر الـ import
python -c "from scripts.n8n.n8n_api import trigger_webhook; print('OK')"
```

---

## 📝 ملاحظات هامة

1. **لا توجد حدود على الاستخدام**: أي agent يقدر يستخدم n8n
2. **Workflows مشتركة**: جميع الـ agents يرون نفس البيانات
3. **Async Processing**: الطلبات تُعالج بشكل غير متزامن
4. **Logging**: جميع العمليات محفوظة في n8n dashboard

---

## 🔗 الروابط المهمة

- **n8n Dashboard**: http://localhost:5678
- **API Module**: `scripts/n8n/n8n_api.py`
- **Examples**: `scripts/n8n/examples.py`
- **Workflows**: `n8n/workflows/`

---

## ✅ خلاصة

**n8n الآن أداة عامة متاحة لجميع الـ agents والـ models - لا حاجة للانتظار أو الاعتماد على agent واحد فقط.**

أي agent يقدر يستخدمها في أي وقت، من أي مكان، بأي طريقة (Python, REST, Direct).
