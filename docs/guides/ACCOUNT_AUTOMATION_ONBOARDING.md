# ربط حساباتك للوكيل التسويقي

هذا الدليل يوضح كيف تجعل الوكيل يدير التسويق عملياً مع الحفاظ على الأمان.

## حساباتك الحالية

- LinkedIn: https://www.linkedin.com/in/saleh-al-majnouni/
- Email: salmajnouni@gmail.com
- Link page: https://linktr.ee/salmajnouni

## مهم قبل البدء

- لا تشارك كلمات المرور داخل الكود.
- استخدم tokens وApp Passwords فقط.
- اجعل كل نشر تلقائي يمر بموافقة يدوية في البداية.

## 1) LinkedIn

LinkedIn API يتطلب تطبيق مطور وصلاحيات مناسبة.

خطوات مختصرة:
1. إنشاء LinkedIn Developer App.
2. تفعيل الصلاحيات المطلوبة للنشر.
3. استخراج Access Token.
4. حفظ التوكن داخل n8n Credentials أو ملف بيئة محلي غير مرفوع إلى git.

### صفحة لينكدإن للشركة

للتشغيل المزدوج (حسابك الشخصي + صفحة الشركة):
1. أنشئ صفحة Company Page باسم الخدمة.
2. أضف رابط الصفحة في:
	config/marketing/accounts.json
	داخل الحقل: linkedin_company_page
3. استخدم مخرجات الحملة اليومية كالتالي:
	- linkedin_personal -> للحساب الشخصي
	- linkedin_page -> لصفحة الشركة

## 2) TikTok

يفضل البدء يدويا (رفع الفيديو من السكربت الجاهز)،
ثم الانتقال إلى TikTok API بعد الحصول على الصلاحيات.

خطوات مختصرة:
1. إنشاء Developer App.
2. ربط حساب TikTok Business.
3. استخراج Access Token.
4. تفعيل workflow نشر Approved فقط.

## 3) YouTube

خطوات مختصرة:
1. إنشاء مشروع في Google Cloud.
2. تفعيل YouTube Data API.
3. إعداد OAuth Client.
4. حفظ Refresh Token بشكل آمن.

## 4) Gmail

للاستخدام السريع:
- استخدم Gmail App Password (مع تفعيل 2FA).
- اربط SMTP في n8n أو استخدم مزود إرسال موثوق.

## نموذج التشغيل المقترح

1. تشغيل:
```powershell
python scripts/marketing/run_daily_marketing_agent.py
```

2. مراجعة الحملة في:
- data/marketing/queue/

3. توليد مسودات الإيميل:
```powershell
python scripts/marketing/build_outreach_emails.py
```

4. مراجعة مسودات الإيميل في:
- data/marketing/outreach/

5. نشر يدوي أو نشر آلي Approved-only.

## سياسات المنصات

- تجنب الرسائل الجماعية المزعجة.
- استخدم رسائل مخصصة لكل مكتب.
- حافظ على وتيرة نشر معتدلة وثابتة.
- وثق كل Lead وتاريخ آخر تواصل.
