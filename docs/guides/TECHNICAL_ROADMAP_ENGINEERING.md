# الخريطة التقنية والبنية الحالية
## Engineering Services for SaleH SaaS

> تنبيه حاكم: هذه الوثيقة خارطة طريق هندسية/منتجية وليست وصفًا حاكمًا للتشغيل الفعلي الحالي. عند التعارض، يُعتمد `docker-compose.yml` ثم `ARCHITECTURE.md` ثم `الحقائق التشغيلية الحاكمة - v0.1.md`.

---

## 📐 البنية الحالية

### **المكونات الموجودة:**

```
SaleH SaaS 4.0
├── 📚 Vector Database (ChromaDB)
│   ├── saleh_knowledge (768-dim, nomic-embed-text)
│   └── saleh_knowledge_qwen3 (legacy)
│
├── 🧠 AI Models & Embeddings
│   ├── Ollama (nomic-embed-text:latest) - Vector embeddings
│   ├── Open WebUI (v0.8.12) - Chat interface
│   └── Pipelines (OpenWebUI filter stack)
│
├── ⚙️ Automation & Workflows (n8n)
│   ├── Saudi Laws Auto-Update (BOE scraper)
│   ├── UQN Gazette Monitor (regulations tracker)
│   ├── Saudi Laws Chat (assistant)
│   └── Knowledge Ingestion (document processor)
│
├── 📁 Data Pipeline
│   ├── FastAPI Service (port 8001)
│   ├── Tika (document extraction)
│   ├── Chunking & Embedding Service
│   └── ChromaDB Store
│
├── 📖 MEP Engineering Module
│   ├── SBC Codes (501/701/801)
│   ├── Benchmark Questions (20+ engineering Q&A)
│   ├── Summary Cards Generator
│   └── RAG for Engineering
│
└── 🔍 Knowledge Sources
    ├── Saudi Codes (legal corpus)
    ├── BOE Gazette (8,000+ laws)
    ├── UQN Regulations (1,300+ regulations)
    └── MEP Standards (SBC, ASHRAE, NFPA)
```

---

## 🛠️ الخدمات الممكنة الآن (Ready to Deploy)

### **1. مساعد الأكواد الذكي** ✅ 90% جاهز

**الحالة الحالية:**
- ✅ ChromaDB متصل مع ~11,500 chunks من القوانين
- ✅ Embedding model `nomic-embed-text:latest` جاهز
- ✅ RAG pipeline يعمل بـ `top_k=10` للقدرة على إجابة دقيقة
- ✅ Open WebUI متصل كواجهة chat

**ما المفقود:**
- ❌ تدريب خاص على أسئلة HVAC/Plumbing
- ❌ Template responses مخصصة للمهندسين
- ❌ تقارير هندسية تلقائية (PDF generation)

**الخطوات للإطلاق:**
```bash
# 1. إضافة أسئلة benchmark HVAC
python scripts/mep/benchmark_summary_retrieval.py --top-k 10

# 2. اختبار إجابة على أسئلة تقنية
# سؤال تجريبي: "ما متطلبات التهوية للمباني المكتبية في SBC-501؟"

# 3. إنشاء template responses مخصصة
# (يحتاج تطوير إضافي 2-3 أيام)
```

---

### **2. منصة إدارة المشاريع** ⚠️ 40% جاهزة

**الموجود:**
- ✅ نموذج قاعدة بيانات PostgreSQL
- ✅ Web UI framework (Open WebUI)
- ✅ Knowledge watcher (لتتبع الملفات)

**المفقود:**
- ❌ واجهة إدارة المشاريع الكاملة
- ❌ نموذج بيانات للمشاريع والمهام
- ❌ تقارير المشروع الديناميكية

**الاستثمار المطلوب:** 2-3 أسابع تطوير

---

### **3. أداة الحساب الهندسي** 🔄 60% جاهزة

**الموجود:**
- ✅ Benchmark questions with formulas
- ✅ n8n workflow nodes قابلة للتوسع
- ✅ RAG يمكنه الإجابة على أسئلة حسابية

**المفقود:**
- ❌ واجهة مستخدم interactive للحساب
- ❌ Validation logic للمدخلات
- ❌ PDF report generation
- ❌ Unit conversion utilities

**الاستثمار المطلوب:** 1-2 أسبوع تطوير

---

### **4. استخراج البيانات من الملفات** ⚠️ 50% جاهزة

**الموجود:**
- ✅ Tika service للاستخراج
- ✅ Chunking و embedding pipeline
- ✅ Knowledge watcher يراقب incoming files

**المفقود:**
- ❌ OCR للصور والرسومات (Advanced Tika)
- ❌ CAD file parsing (DWG/DXF)
- ❌ Compliance checking logic
- ❌ Diff detection between versions

**الاستثمار المطلوب:** 3-4 أسابع (يشمل تدريب models)

---

### **5. نظام التدريب والشهادات** 🚀 0% (Greenfield)

**ما يحتاج إنشاء:**
- ❌ محتوى تدريبي منظم
- ❌ نموذج الاختبارات
- ❌ نظام الشهادات الرقمية
- ❌ Leaderboards و achievements

**الاستثمار المطلوب:** 4-6 أسابع

---

### **6. الاستشارة القانونية** ⚠️ 30% جاهزة

**الموجود:**
- ✅ SAP legal agent (بهيكل معماري)
- ✅ Legal knowledge corpus
- ✅ n8n trigger patterns

**المفقود:**
- ❌ Specialized RAG للمستندات القانونية
- ❌ Contract analysis logic
- ❌ Risk scoring system
- ❌ Template generation

**الاستثمار المطلوب:** 2-3 أسابع

---

## 📊 نموذج التسليم المقترح

### **Phase 1: MVP (6 أسابيع)**

**الخدمات:**
1. ✅ مساعد الأكواد الذكي (SBC-501 كبداية)
2. ✅ أداة البحث عن الأنظمة
3. ✅ أداة حساب بسيطة (HVAC)

**التسليم:**
- Web interface محسّن للمهندسين
- API لـ integrations
- Pilot program مع 5 مكاتب

**الاستثمار:**
- Dev: 4 أسابع
- QA: 1-2 أسبوع
- Training: 1 أسبوع

---

### **Phase 2: Core Services (8 أسابيع)**

**الخدمات الإضافية:**
1. ✅ إدارة المشاريع المبسطة
2. ✅ PDF report generation
3. ✅ CAD integration (basic)
4. ✅ Multi-code support (SBC-501/701/801)

**الاستثمار:**
- Dev: 5-6 أسابيع
- QA: 1-2 أسبوع

---

### **Phase 3: Advanced Features (12 أسبوع)**

**الخدمات:**
1. ✅ استخراج ذكي من الملفات (OCR + validation)
2. ✅ نظام التدريب والشهادات
3. ✅ Compliance automation
4. ✅ Advanced analytics

**الاستثمار:**
- Dev: 8-10 أسابيع
- ML/training: 2-4 أسابيع
- QA: 1-2 أسبوع

---

## 💻 Tech Stack الموصى به

```yaml
Frontend:
  - React/Vue.js (responsive UI)
  - PDF.js (rendering + annotation)
  - Three.js (3D visualization for MEP)

Backend:
  - FastAPI (existing, extend)
  - PostgreSQL (existing)
  - n8n (existing, for workflows)
  - ChromaDB + RAG (existing)

AI/ML:
  - Ollama + nomic-embed-text (existing)
  - Open WebUI (existing)
  - Fine-tuned LLM (optional for technical responses)

DevOps:
  - Docker Compose (existing)
  - GitHub Actions (CI/CD)
  - Prometheus + Grafana (monitoring)

Integrations:
  - CAD APIs (Autodesk API, LibreOffice API)
  - ERP systems (via n8n connectors)
  - Payment gateway (Stripe/Telr)
```

---

## 🎯 Roadmap التفصيلي

```
Week 1-2:  Prototype UI for Engineer Assistant
Week 3-4:  MVP v1.0 launch + 5 pilot customers
Week 5-6:  Feedback gathering + bug fixes
Week 7-10: Phase 2 features (Projects, Reports)
Week 11-14: Phase 3 features (Training, Compliance)
Week 15+:  Scale + support + expansions (GCC codes)
```

---

## 💼 استراتيجية Go-to-Market

### **Target Customers:**
1. **Small Engineering Offices** (5-20 engineers)
   - Problems: Compliance tracking, code reference
   - Price sensitivity: Medium
   - Approach: Self-service SaaS

2. **Medium Consulting Firms** (20-100)
   - Problems: Project management, quality assurance
   - Price sensitivity: Low-medium
   - Approach: Enterprise plan + support

3. **Large Corporations** (100+)
   - Problems: Compliance at scale, integration
   - Price sensitivity: Low
   - Approach: Custom implementation

### **Sales Channels:**
- Direct (LinkedIn outreach to engineering offices)
- Partnerships (with CAD providers, ERP vendors)
- Events (engineering conferences, seminars)
- Content marketing (technical blogs)

### **Competitive Advantages:**
- ✅ Only AI-powered SBC assistant in Arabic
- ✅ Integrated with multiple codes (SBC, legal, regulations)
- ✅ Automated compliance checking
- ✅ Low cost vs. hiring compliance staff

---

## ✅ المتطلبات الفورية

**للإطلاق الأول (MVP):**
```
- [ ] Improved UI for engineer queries
- [ ] SBC-specific prompt templates
- [ ] Test with 5 pilot engineers
- [ ] Create pricing/billing system
- [ ] Legal terms for engineering services
- [ ] Support documentation
```

**الفريق المطلوب:**
- 1 Senior Backend Developer (FastAPI/n8n)
- 1 Frontend Developer (React/UI)
- 1 Product Manager (engineering domain)
- 1 QA Engineer
- 1 Customer Success Manager

---

## 📞 الخطوة التالية

**هل تريد:**
1. 🚀 البدء الفوري بـ MVP (6 أسابيع)
2. 📋 دراسة جدوى تفصيلية (2 أسبوع)
3. 🎯 عرض توضيحي للعملاء المحتملين
4. 💰 دراسة الأرقام المالية والعائد على الاستثمار

**اختر الخيار وسأساعدك! 🎯**
