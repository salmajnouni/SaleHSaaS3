# تشغيل وكيل التسويق متعدد القنوات (فردي)

هذا الدليل يجعل الوكيل يساعدك في التسويق وجلب العملاء المحتملين عبر:
- LinkedIn
- TikTok
- YouTube Shorts
- Email outreach

## ما الذي يفعله الوكيل الآن

- يولد حزمة محتوى يومية متسقة لكل قناة.
- ينشئ رسالة إيميل Outreach جاهزة.
- يحفظ كل شيء في طابور موافقة محلي قبل النشر.

## لماذا طابور موافقة؟

لأن أفضل ممارسة هي مراجعة المحتوى قبل النشر خاصة في LinkedIn وYouTube وTikTok،
ولتجنب أي مخالفة لسياسات المنصات أو نشر محتوى غير دقيق.

## الملفات المضافة

- agents/social_media/omnichannel_marketing_agent.py
- scripts/marketing/run_daily_marketing_agent.py
- scripts/marketing/build_outreach_emails.py
- scripts/marketing/generate_month_campaign_queue.py
- config/marketing/accounts.example.json
- data/marketing/queue/
- data/marketing/leads.csv
- data/marketing/field_visit_scenarios.json

## الإعداد السريع

1. انسخ ملف الإعداد:
   - من: config/marketing/accounts.example.json
   - إلى: config/marketing/accounts.json

2. تأكد من تشغيل Ollama محلياً وأن النموذج متوفر.

3. شغل السكربت اليومي:

```powershell
python scripts/marketing/run_daily_marketing_agent.py
```

4. راجع ملف الحملة الناتج داخل:

- data/marketing/queue/

## شكل المخرجات

كل حملة تحتوي على:
- نص LinkedIn للحساب الشخصي
- نص LinkedIn لصفحة الشركة
- سكربت TikTok
- سكربت YouTube Short
- عنوان + نص إيميل تواصل
- رسالة متابعة قصيرة
- هاشتاقات + Persona + Lead Magnet

## آلية العمل اليومية المقترحة (30-45 دقيقة)

1. تشغيل السكربت لتوليد الحملة.
2. مراجعة النصوص وتعديل بسيط.
3. نشر يدوي في LinkedIn/TikTok/YouTube.
4. إرسال 5-10 رسائل Email outreach مخصصة.
5. تسجيل العملاء المحتملين في ملف أو CRM بسيط.

## توليد رسائل إيميل للعملاء المحتملين

1. املأ ملف البيانات:

- data/marketing/leads.csv

2. أنشئ مسودات الإيميل المخصصة:

```powershell
python scripts/marketing/build_outreach_emails.py
```

3. راجع المخرجات داخل:

- data/marketing/outreach/

## مرحلة الأتمتة التالية (اختياري)

يمكن ربط الطابور مع n8n بحيث:
- Approved only -> publish queue
- Email follow-up -> schedule queue

لكن يفضل البدء بالموافقة اليدوية حتى تثبت الرسائل التي تعمل أفضل.

## تعبئة 30 يوم دفعة واحدة

إذا كنت مشغولا بالزيارات الميدانية، يمكنك تعبئة الطابور لشهر كامل:

```powershell
python scripts/marketing/generate_month_campaign_queue.py
```

بعدها يصبح لديك مسودات يومية جاهزة للمراجعة والنشر.

## ملاحظة مهمة عن الوصول للحسابات

لا يمكن تشغيل الوكيل للوصول المباشر إلى حساباتك بدون تزويده
OAuth/API credentials عبر إعدادات آمنة.

لا تضع كلمات مرور الحسابات داخل الكود.
استخدم ملفات بيئة محلية أو Credentials manager داخل n8n.
