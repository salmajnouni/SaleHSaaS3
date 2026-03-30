# 📚 فهرس الملفات الجديدة - مرحلة خدمات المكاتب الهندسية
## Complete File Index - Engineering Services Initiative

**تاريخ الإنشاء:** 30 مارس 2026  
**حالة المشروع:** جاهز للإطلاق - 1 أبريل 2026

---

## 🆕 ملفات أتمتة التسويق الفردي

ملاحظة تشغيلية حالية: التركيز الحالي على تطوير الخدمة وتسليمها فنيا، وليس على التوسع التسويقي.

### 1. agents/social_media/omnichannel_marketing_agent.py
```
الهدف: وكيل موحد لتوليد محتوى LinkedIn + TikTok + YouTube + Email
الحالة: جاهز ويولد ملفات pending_approval
```

### 2. scripts/marketing/run_daily_marketing_agent.py
```
الهدف: تشغيل يومي سريع لإنتاج حملة متعددة القنوات
الأمر: python scripts/marketing/run_daily_marketing_agent.py
المخرجات: data/marketing/queue/campaign_*.json
```

### 3. scripts/marketing/build_outreach_emails.py
```
الهدف: توليد مسودات إيميل مخصصة من ملف العملاء المحتملين
الأمر: python scripts/marketing/build_outreach_emails.py
المخرجات: data/marketing/outreach/email_drafts_*.json
```

### 4. config/marketing/accounts.example.json
```
الهدف: قالب إعداد حساباتك التسويقية
ملاحظة: انسخه إلى accounts.json مع القيم الفعلية
```

### 5. data/marketing/leads.csv
```
الهدف: قاعدة بيانات مبسطة للعملاء المحتملين
ملاحظة: أضف المكاتب المستهدفة قبل تشغيل بناء رسائل الإيميل
```

### 6. docs/guides/SOLO_MARKETING_AUTOMATION.md
```
الهدف: دليل التشغيل اليومي الفردي (بدون فريق)
```

### 7. docs/guides/ACCOUNT_AUTOMATION_ONBOARDING.md
```
الهدف: دليل ربط LinkedIn/TikTok/YouTube/Gmail بشكل آمن
```

### 8. docs/guides/LINKEDIN_PAGE_SETUP_AND_PLAYBOOK.md
```
الهدف: إنشاء صفحة لينكدإن للشركة وتشغيلها بجانب الحساب الشخصي
```

### 9. docs/sales/CLIENT_OFFER_STACK_AR.md
```
الهدف: تعريف واضح لما نقدمه للعميل (المشكلة، القيمة، الباقات، التسليم)
```

### 10. docs/sales/CLIENT_SCENARIOS_AND_PACKAGES_AR.md
```
الهدف: مطابقة نوع المكتب الهندسي مع الباقة الأنسب في الاجتماع
```

### 11. docs/sales/DISCOVERY_MEETING_CHECKLIST_AR.md
```
الهدف: قائمة تشخيص احتياج العميل وإغلاق خطوة المتابعة بعد الاجتماع
```

### 12. docs/sales/HOTEL_QUOTATION_MODEL_AR.md
```
الهدف: نموذج عرض سعر مخصص لتصميم الفنادق حسب الحجم والتعقيد
```

### 13. docs/services/SERVICE_CATALOG_AR.md
```
الهدف: تعريف الخدمات الفنية بشكل تشغيلي (مدخلات/مخرجات/معايير قبول)
```

### 14. docs/services/SERVICE_DELIVERY_WORKFLOW_AR.md
```
الهدف: توحيد سير تسليم الخدمة من تعريف النطاق حتى الإغلاق
```

### 15. docs/services/SERVICE_SCOPE_TEMPLATE_AR.md
```
الهدف: نموذج موحد لتحديد نطاق كل خدمة لكل مشروع
```

---

## 📋 الملفات الإستراتيجية

### 1. ACTION_PLAN_ENGINEERING_4WEEKS.md
```
الموقع: c:\saleh26\salehsaas\SaleHSaaS3\
الحجم: ~8 KB
الهدف: خطة عمل شاملة 4 أسابيع

المحتوى:
  ✓ أسبوع 1: التحضيرات التقنية (RAG, UI, APIs, QA)
  ✓ أسبوع 2: المحتوى والموارد (تدريب, بيانات, عقود)
  ✓ أسبوع 3: Beta Launch (5 عملاء تجريبيين)
  ✓ أسبوع 4: الإطلاق الرسمي

الاستخدام:
  - مرجع للفريق الكامل
  - تتبع التقدم أسبوعياً
  - توزيع المهام على الأفراد
```

### 2. PROGRESS_TRACKING_ENGINEERING.md
```
الموقع: c:\saleh26\salehsaas\SaleHSaaS3\
الحجم: ~10 KB
الهدف: تتبع التقدم يومي وأسبوعي

المحتوى:
  ✓ جدول الحالة (4 أسابيع)
  ✓ تفاصيل كل مهمة
  ✓ معايير القبول لكل مهمة
  ✓ KPIs وأهداف الأسابيع
  ✓ جدول تتبع المشاكل والمخاطر

الاستخدام:
  - تحديث يومي من قبل Product Manager
  - مرجع سريع لحالة المشروع
  - جدول بيانات/Notion محدث
```

### 3. IMMEDIATE_ACTIONS_LAUNCH.md
```
الموقع: c:\saleh26\salehsaas\SaleHSaaS3\
الحجم: ~6 KB
الهدف: خطوات الإطلاق الفورية (اليوم والغد)

المحتوى:
  ✓ مهام اليوم (30 مارس): 4 أشياء فورية
  ✓ خطوات غداً (1 أبريل): تفاصيل ساعة بساعة
  ✓ قائمة فريق التطوير النهائية
  ✓ معايير نجاح الأسبوع الأول

الاستخدام:
  - بدء الفريق صباح غداً
  - قائمة مراجعة قبل الاجتماع الأول
  - تحضير الأدوات والموارد
```

---

## 📊 الملفات الاستراتيجية الموجودة

### من المرحلة السابقة (28-30 مارس):

#### 1. docs/guides/ENGINEERING_OFFICES_SERVICES.md
```
الموقع: docs/guides/
الحجم: 9 KB
الموضوع: نظرة عامة على 7 خدمات هندسية

المحتوى الرئيسي:
  • خدمات المكاتب الهندسية (7 خدمات):
    1. Smart Code Assistant (مساعد الأكواس الذكي)
    2. Regulations Platform (منصة الأنظمة والتشريعات)
    3. Data Extraction Tool (أداة استخراج البيانات)
    4. Engineering Calculator (الآلة الحاسبة الهندسية)
    5. Project Management (إدارة المشاريع)
    6. Legal Consulting (الاستشارات القانونية)
    7. Training & Certification (التدريب والشهادات)
  
  • نماذج التسعير (4 مستويات):
    - Bronze: 500 ريال/شهر
    - Silver: 2,000 ريال/شهر
    - Gold: 5,000 ريال/شهر
    - Platinum: 10,000+ ريال/شهر
  
  • الجدول الزمني (6 أشهر)
  • المؤشرات الرئيسية (KPIs)

الاستخدام:
  - عرض توضيحي للعملاء
  - مرجع للفريق التقني
  - نقاط بيع قوية
```

#### 2. docs/guides/TECHNICAL_ROADMAP_ENGINEERING.md
```
الموقع: docs/guides/
الحجم: 8 KB
الموضوع: خريطة الطريق التقنية والجدول الزمني

المحتوى الرئيسي:
  • حالة الجاهزية الحالية:
    - مؤشر الجاهزية: 75%
    - ChromaDB: ✅ جاهز
    - Data Pipeline: ✅ جاهز
    - RAG Retrieval: ⚠️ يحتاج تحسين (query endpoint 404)
    - Engineering Data: ✅ متوفر (20 سؤال benchmark)
  
  • جاهزية الخدمات:
    - MVP (Smart Code): 90% جاهز
    - Advanced (Regulations): 60% جاهز
    - Project Mgmt: 40% جاهز
    - Data Extraction: 50% جاهز
    - Training: 0% (لم يبدأ)
    - Legal Consulting: 30% جاهز
  
  • المراحل الثلاث:
    Phase 1 (6 أسابيع): MVP + 2 خدمات أساسية
    Phase 2 (8 أسابيع): 3 خدمات إضافية
    Phase 3 (12 أسبوع): 2 خدمة متقدمة

الاستخدام:
  - مرجع تقني للفريق
  - تتبع الجاهزية
  - جدول زمني واقعي
```

#### 3. EXECUTIVE_SUMMARY_ENGINEERING.md
```
الموقع: 
الحجم: 8 KB
الموضوع: ملخص تنفيذي شامل

المحتوى الرئيسي:
  • تحليل السوق:
    - حجم السوق: 240-600 مليون ريال سنوياً
    - عدد المكاتب الهندسية: 800-1,200
    - نسبة الاختراق المستهدفة: 5-10% (50-120 عميل)
    - الفرصة الأولى: لا منافسين برامج SBC-AI بالعربية
  
  • الإسقاطات المالية:
    - السنة 1: 20 مليون ريال عائد (50 عميل × 400K)
    - السنة 2: 60 مليون ريال
    - السنة 3: 120 مليون ريال
    
    - العائد على الاستثمار: 1,400-2,000% في السنة الأولى
    - نقطة التعادل: 3-4 أشهر
    - صافي الربح السنة الأولى: 18 مليون ريال
  
  • المكونات الاستثمارية:
    - التطوير: 400K-600K
    - التسويق: 200K-300K
    - العمليات والإدارة: 300K-400K
    - الإجمالي: 900K-1.3M ريال
  
  • KPIs:
    - SaaS ARR: 20M → 60M → 120M
    - عدد العملاء: 50 → 150 → 300
    - Net Retention: 90-95%
    - NPS: 75 → 85 → 90

الاستخدام:
  - عرض إدارة/مستثمرون
  - قرارات استثمارية
  - تبرير الميزانية
```

#### 4. DETAILED_SERVICES_BREAKDOWN.md
```
الموقع: 
الحجم: 12 KB
الموضوع: تفاصيل كل خدمة بالميزات والمعادلات

المحتوى الرئيسي:
  • 9 خدمات موسعة (بدل 7):
    - Smart Code Assistant (HVAC, Plumbing, Fire)
    - Regulations Platform
    - Data Extraction
    - Engineering Calculator
    - Project Management
    - Legal Consulting
    - Training & Certification
  
  • 4 مستويات سعرية:
    Bronze (500 ريال)
    Silver (2,000 ريال)
    Gold (5,000 ريال)
    Platinum (10,000+ ريال)
  
  • جدول المميزات:
    - عدد المشاريع المسموح
    - التخزين والبيانات
    - أولويات الدعم
    - عدد المستخدمين
    - الواجهات البرمجية (APIs)
  
  • المعادلات والحسابات:
    - حمل التبريد الحسي (Sensible Load)
    - حمل التبريد الكامن (Latent Load)
    - وحدات التصريف (DFU)
    - خروجات الحريق وعرض الممرات

الاستخدام:
  - عرض تفصيلي للعملاء
  - مرجع تقني للفريق
  - معايير الخدمة الدقيقة
```

#### 5. QUICK_REFERENCE_ENGINEERING.md
```
الموقع: 
الحجم: 4 KB
الموضوع: ملخص سريع لجميع الخدمات

المحتوى:
  • خدمات الأساسية (5 خدمات)
  • التسعير السريع
  • الفوائد الرئيسية:
    - توفير 30-40% من وقت الامتثال
    - خفض الأخطاء بـ 90%
    - دعم 24/7 بالعربية
  
  • بيان مختصر للعرض الفريد:
    "الملحق الوحيد للأكواس السعودية (SBC) بالذكاء الاصطناعي"

الاستخدام:
  - بطاقة عمل رقمية
  - pitch سريع (2 دقيقة)
  - قائمة الأسعار الأساسية
```

---

## 🧪 ملفات الاختبار والجودة

### test_engineering_readiness.py
```
الموقع: c:\saleh26\salehsaas\SaleHSaaS3\
الحجم: ~500+ سطر
الهدف: اختبار جاهزية نظام الخدمات الهندسية

المتضمن:
  ✓ Test 1: ChromaDB Connectivity (✅ PASS)
  ✓ Test 2: Data Pipeline Status (✅ PASS)
  ✓ Test 3: RAG Retrieval (❌ FAIL - 404 error)
  ✓ Test 4: Engineering Domain Coverage (❌ FAIL - 0/9)
  ✓ Test 5: Benchmark Questions (✅ PASS - 20 loaded)

النتيجة:
  - جاهزية الإجمالية: 75%
  - حالة الجاهزية: ⚠️ PARTIALLY READY
  - المسائل الحرجة: 1 (RAG query endpoint)

الآلية:
  python test_engineering_readiness.py

الملاحظات:
  - يتطلب ChromaDB جاهزاً
  - يستخدم 20 سؤال من benchmark
  - يقيس 3 domains (HVAC, Plumbing, Fire)
```

---

## 🗂️ البيانات الموجودة (MEP Engineering)

### موقع البيانات: data/mep_rag/

```
البيانات الجاهزة:
  ✓ benchmark_questions_mep.json (20 سؤال)
    - 8 أسئلة HVAC
    - 6 أسئلة Plumbing
    - 6 أسئلة Fire Safety
  
  ✓ source_register.csv (5 معايير)
    - SBC-501 (Mechanical/HVAC)
    - SBC-701 (Plumbing)
    - SBC-801 (Fire Safety)
    - ASHRAE-62.1
    - NFPA-13
  
  ✓ summary_cards/ (قوالب الملخصات)
    - قوالب مخصصة للإجابات
    - تجنب انتهاكات الحقوق
    - استشهادات صحيحة
  
  ✓ Vector Database (ChromaDB):
    - Collection: saleh_knowledge
    - عدد الـ vectors: 11,597
    - البعد: 768
    - النموذج: nomic-embed-text:latest
```

---

## 🔗 الملفات المتعلقة الموجودة

### في السياق الأوسع للمشروع:

```
n8n Workflows (نشط):
  ✓ Daily Backup
  ✓ Saudi Legal Scraper v2
  ✓ UQN Gazette Monitor
  ✓ Saudi Laws Auto-Update
  ✓ Saudi Laws Assistant

ChromaDB Collections:
  ✓ saleh_knowledge (11,597 vectors)
  ✓ saleh_knowledge_qwen3 (11,566 vectors - legacy)

Open WebUI:
  ✓ متاح على localhost:3000
  ✓ جاهز للتخصيص

API Services:
  ✓ Data Pipeline (port 8001)
  ✓ n8n (port 5678)
  ✓ Pipelines (port 9099)
  ✓ ChromaDB (port 8010)
```

---

## 📈 قائمة الجودة قبل الإطلاق

### ما الذي يجب التحقق منه:

```
قبل البدء (1 أبريل):
  [ ] جميع الملفات الجديدة موجودة
  [ ] الفريق يفهم الخطة
  [ ] الأدوات جاهزة (Slack, GitHub, etc)
  [ ] ChromaDB تعمل بكفاءة
  [ ] Open WebUI تعمل
  [ ] جميع APIs responsive

أثناء الأسبوع الأول:
  [ ] RAG accuracy improved to 85%+
  [ ] API endpoints deployed (5/5)
  [ ] UI theme custom
  [ ] QA tests defined
  [ ] Zero critical bugs

نهاية الأسبوع الأول (7 أبريل):
  [ ] جميع الأهداف المذكورة محققة
  [ ] فريق على الجداول الزمنية
  [ ] موافقة من الإدارة للمرحلة الثانية
```

---

## 🎯 الملفات التي يجب قراءتها حسب الدور

### للـ CEO / Founder:
```
Priority:
  1. EXECUTIVE_SUMMARY_ENGINEERING.md (أهم)
  2. ACTION_PLAN_ENGINEERING_4WEEKS.md
  3. IMMEDIATE_ACTIONS_LAUNCH.md (اليوم)
  
وقت القراءة: 30 دقيقة
```

### للـ CTO / Tech Lead:
```
Priority:
  1. TECHNICAL_ROADMAP_ENGINEERING.md
  2. ACTION_PLAN_ENGINEERING_4WEEKS.md (أسبوع 1)
  3. test_engineering_readiness.py (current state)
  
وقت القراءة: 1 ساعة
```

### للـ Product Manager:
```
Priority:
  1. ACTION_PLAN_ENGINEERING_4WEEKS.md (كاملاً)
  2. PROGRESS_TRACKING_ENGINEERING.md
  3. ENGINEERING_OFFICES_SERVICES.md
  4. DETAILED_SERVICES_BREAKDOWN.md
  
وقت القراءة: 2 ساعة
```

### للـ Backend Developer:
```
Priority:
  1. ACTION_PLAN_ENGINEERING_4WEEKS.md (أسابيع 1)
  2. TECHNICAL_ROADMAP_ENGINEERING.md
  3. test_engineering_readiness.py (الخطأ الحالي)
  
وقت القراءة: 1.5 ساعة
```

### للـ Frontend Developer:
```
Priority:
  1. DETAILED_SERVICES_BREAKDOWN.md (UI/UX)
  2. ACTION_PLAN_ENGINEERING_4WEEKS.md (الأسبوع 1)
  3. QUICK_REFERENCE_ENGINEERING.md (للإلهام)
  
وقت القراءة: 1 ساعة
```

### للـ QA Engineer:
```
Priority:
  1. test_engineering_readiness.py (البنية)
  2. ACTION_PLAN_ENGINEERING_4WEEKS.md (الأسبوع 1)
  3. PROGRESS_TRACKING_ENGINEERING.md (المعايير)
  
وقت القراءة: 1.5 ساعة
```

---

## ✅ قائمة التحقق النهائية

```
[ ] جميع 3 ملفات جديدة موجودة (خطة، تتبع، فوري)
[ ] جميع 5 ملفات استراتيجية موجودة (من مرحلة سابقة)
[ ] ملف الاختبار موجود وجاهز (test_engineering_readiness.py)
[ ] بيانات الـ MEP موجودة (20 سؤال + معايير)
[ ] الفريق معروّف و يفهم الدور
[ ] الجدول الزمني واضح (4 أسابيع)
[ ] الأهداف والـ KPIs محددة
[ ] الموارد والأدوات جاهزة
[ ] الإدارة وافقت على الخطة والميزانية
[ ] جاهز للبدء صباح 1 أبريل 2026
```

---

**خريطة الملفات كاملة ✅**

**الفريق جاهز للإطلاق؟ 🚀**
