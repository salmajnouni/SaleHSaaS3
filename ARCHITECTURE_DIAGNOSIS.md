# تشخيص المشكلة والحل الصحيح — SaleHSaaS

## أولاً: ما الذي كان مبنياً بشكل خاطئ

### الخطأ الجذري: سوء فهم دور الـ Pipelines

الـ Pipelines التي بُنيت مسبقاً كانت تقوم بشيء مستحيل:

```
Pipeline (على خادم pipelines:9099)
    ↓ تستدعي
Open WebUI API (open-webui:8080/api/chat/completions)
    ↓ لتحصل على
نموذج "n8n-expert" أو "legal-expert"
```

**المشكلة**: هذه النماذج الخبيرة لم تكن موجودة أصلاً في Open WebUI! الـ Pipeline كانت تستدعي نماذج وهمية لا وجود لها.

---

## ثانياً: كيف تعمل البنية فعلياً (من الوثائق الرسمية)

### مسار الطلب الصحيح في SaleHSaaS

```
المستخدم في Open WebUI
    ↓ يختار نموذجاً
Open WebUI (port 3000)
    ↓ إذا كان النموذج من نوع Pipeline
Pipelines Server (port 9099)  ← هنا تعمل الـ Pipeline
    ↓ تستدعي Ollama مباشرة
Ollama (host.docker.internal:11434)
    ↓
النموذج الفعلي (llama3.1:8b أو deepseek-r1:7b)
```

### مسار n8n (المسار الثاني المنفصل)

```
n8n Workflow
    ↓ يستخدم lmChatOpenAi node
n8n Bridge (port 3333)  ← يحوّل workflows إلى نماذج OpenAI
    ↓ يستدعي webhook في n8n
n8n Workflow (Chat Trigger)
    ↓ يستخدم LLM node
Ollama (host.docker.internal:11434)
```

---

## ثالثاً: الحل الصحيح — ثلاثة مسارات مستقلة

### المسار 1: الـ Pipelines في Open WebUI

**الغرض**: إضافة منطق Python مخصص (RAG، فلترة، تحويل) قبل إرسال الطلب لـ Ollama.

**البنية الصحيحة**:
```python
class Pipeline:
    def pipe(self, user_message, model_id, messages, body):
        # 1. حقن السياق المتخصص
        messages = inject_expert_context(messages)
        
        # 2. استدعاء Ollama مباشرة (وليس Open WebUI!)
        response = requests.post(
            "http://host.docker.internal:11434/api/chat",
            json={"model": "llama3.1:8b", "messages": messages}
        )
        return response.json()["message"]["content"]
```

**النتيجة**: تظهر كنموذج "External" في Open WebUI بالاسم المحدد في `self.name`.

### المسار 2: النماذج الخبيرة في Open WebUI (Workspace > Models)

**الغرض**: إنشاء نماذج مخصصة بـ system prompts متخصصة بدون كود.

**الطريقة**: من واجهة Open WebUI:
- Workspace > Models > + New Model
- اختر النموذج الأساسي (llama3.1:8b)
- أضف System Prompt متخصص
- احفظ باسم "n8n-expert" أو "legal-expert"

**النتيجة**: تظهر في قائمة النماذج وفي `/v1/models` وفي n8n Bridge.

### المسار 3: n8n Workflows كنماذج (عبر n8n Bridge)

**الغرض**: استخدام n8n workflows كاملة كـ "نماذج" في Open WebUI وn8n.

**الطريقة**:
1. أنشئ workflow في n8n مع Chat Trigger
2. أضف tag: `n8n-openai-bridge`
3. فعّل الـ workflow
4. يظهر تلقائياً في n8n Bridge

---

## رابعاً: ما يجب بناؤه فعلاً

### للـ Pipelines (المسار 1) — الحل الصحيح

كل Pipeline يجب أن:
1. **تستدعي Ollama مباشرة** (وليس Open WebUI)
2. **تحقن السياق المتخصص** في system message
3. **تدعم Streaming** عبر Ollama API

### للنماذج الخبيرة (المسار 2) — الأبسط والأفضل

لإنشاء "n8n-expert" و"legal-expert" إلخ:
- استخدم `Workspace > Models` في Open WebUI
- أو استخدم Open WebUI API: `POST /api/v1/models/create`

### لـ n8n (المسار 3) — موجود ويعمل

الـ n8n Bridge موجود ومضبوط بشكل صحيح في docker-compose.yml.
المشكلة الوحيدة: الـ workflows لم تُعلَّم بـ `n8n-openai-bridge` tag.
