# 🚀 دليل تشغيل SaleHSaaS3 مع وحدة الوكلاء (Paperclip AI)

هذا الدليل مخصص لتشغيل النظام المتكامل على جهاز **GMKtec EVO-X2** (بمواصفات 128GB RAM).

---

## 1. المتطلبات المسبقة (تأكد منها أولاً)

1. **Docker Desktop** يعمل في الخلفية.
2. **Ollama** يعمل على Windows (تأكد من وجود أيقونة Ollama في شريط المهام بجوار الساعة).
3. **النماذج محملة في Ollama**:
   افتح PowerShell وشغّل:
   ```powershell
   ollama run deepseek-v3.2:latest
   ```
   *(إذا لم يكن موجوداً، سيقوم بتحميله. بعد التحميل اكتب `/bye` للخروج).*

---

## 2. إعداد ملفات البيئة (.env)

1. افتح مجلد المشروع: `C:\saleh26\salehsaas\SaleHSaaS3`
2. انسخ ملف `.env.example` وأعد تسميته إلى `.env` (إذا لم تكن قد فعلت ذلك مسبقاً).
3. افتح ملف `.env` (يفضل باستخدام VS Code أو Notepad++) وتأكد من وجود هذه القيم:
   ```env
   POSTGRES_USER=salehsaas
   POSTGRES_PASSWORD=your_strong_password_here
   POSTGRES_DB=salehsaas
   OLLAMA_BASE_URL=http://host.docker.internal:11434
   DEFAULT_MODEL=deepseek-v3.2:latest
   ```

---

## 3. تشغيل النظام بالكامل (أمر واحد)

افتح **PowerShell** كمسؤول (Run as Administrator)، وانتقل لمجلد المشروع، ثم نفذ هذا الأمر:

```powershell
cd C:\saleh26\salehsaas\SaleHSaaS3

# هذا الأمر يشغل النظام الأساسي + وحدة الوكلاء معاً
docker compose -f docker-compose.yml -f docker-compose.agents.yml up -d
```

*ملاحظة: في المرة الأولى، قد يستغرق التحميل بضع دقائق لتنزيل صور Paperclip و Unsloth.*

---

## 4. التحقق من عمل النظام

بعد انتهاء الأمر السابق، انتظر 30 ثانية، ثم افتح المتصفح على الروابط التالية:

| الخدمة | الرابط | الوصف |
|---|---|---|
| **SaleHSaaS3 (الأساسي)** | [http://localhost:3000](http://localhost:3000) | واجهة المحادثة الرئيسية |
| **n8n (الأتمتة)** | [http://localhost:5678](http://localhost:5678) | سير العمل (الدخول: admin / كلمة المرور في .env) |
| **Paperclip AI (الوكلاء)** | [http://localhost:8080](http://localhost:8080) | لوحة تحكم الوكلاء الجديدة |

---

## 5. الإعداد الأول داخل Paperclip AI

عند فتح `http://localhost:8080` لأول مرة:

1. **إنشاء الشركة:** سيطلب منك إدخال اسم شركتك (مثلاً: *SaleH AI Solutions*).
2. **ربط النموذج:** 
   - اذهب إلى الإعدادات (Settings) -> Models.
   - اختر مزود الخدمة: **Ollama**.
   - الرابط: `http://host.docker.internal:11434`
   - النموذج الافتراضي: `deepseek-v3.2:latest`
3. **تعيين الوكلاء:**
   - اذهب إلى Agents.
   - أنشئ وكيل جديد (مثلاً: *CTO Agent*).
   - حدد النموذج: `deepseek-v3.2:latest`.
   - في الـ System Prompt، اكتب: *"أنت المدير التقني، مهمتك مراجعة الكود واقتراح تحسينات دون هدم البنية الحالية."*

---

## 6. إيقاف النظام (عند الحاجة)

لإيقاف كل شيء بأمان دون فقدان البيانات:
```powershell
cd C:\saleh26\salehsaas\SaleHSaaS3
docker compose -f docker-compose.yml -f docker-compose.agents.yml down
```
