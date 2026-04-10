# قاعدة المعرفة — autoresearch Training Knowledge

> تاريخ الإنشاء: 2026-04-10
> Knowledge Base ID: `86c62169-96e8-4d6d-86f4-17fc0f51c258`

---

## نظرة عامة

قاعدة معرفة RAG مخصصة تحتوي على التوثيق الكامل لمشروع autoresearch، مرتبطة بنموذج **Evo2** في Open WebUI حتى يستطيع الإجابة عن أسئلة التدريب والإعداد من سياق حقيقي.

---

## الوثائق (7 ملفات)

المسار: `C:\saleh26\researchai\rag_docs\`

| # | الملف | المحتوى |
|---|-------|---------|
| 01 | `01_project_overview.md` | نظرة عامة على المشروع، العتاد، البرمجيات |
| 02 | `02_code_structure.md` | بنية GPT، الفئات البرمجية، المحسّن |
| 03 | `03_hyperparameters.md` | جميع المعاملات الفائقة مع دليل التعديل |
| 04 | `04_gpu_setup.md` | إعداد AMD ROCm على WSL2، librocdxg، المتغيرات |
| 05 | `05_training_results.md` | نتائج التجارب ونظام النقاط التفتيشية |
| 06 | `06_tools_services.md` | sanirejal API، ar.sh، نماذج Open WebUI |
| 07 | `07_training_workflow.md` | إجراءات التدريب خطوة بخطوة |

---

## البنية التقنية

```
researchai/rag_docs/*.md
        │
        ▼
  Open WebUI Upload API
        │
        ▼
  Knowledge Base (86c62169-96e8-4d6d-86f4-17fc0f51c258)
        │
        ▼
  ChromaDB (فهرسة + تضمينات)
        │
        ▼
  Evo2 Model (knowledgeIds في meta)
        │
        ▼
  المستخدم يسأل → Evo2 يبحث في القاعدة → يجيب بسياق حقيقي
```

---

## الربط بنموذج Evo2

تم ربط قاعدة المعرفة بنموذج Evo2 عبر حقل `knowledgeIds` في meta:

```json
{
  "meta": {
    "knowledgeIds": ["86c62169-96e8-4d6d-86f4-17fc0f51c258"]
  }
}
```

هذا يتيح لـ Evo2 البحث الدلالي في الوثائق السبع عند الإجابة عن أسئلة تتعلق بـ:
- إعداد GPU و ROCm
- المعاملات الفائقة وتعديلها
- تشغيل التدريب وقراءة النتائج
- استكشاف الأخطاء وإصلاحها
- بنية الكود المصدري

---

## تكامل Cline

نموذج Evo2 متاح أيضاً عبر إضافة **Cline** في VS Code:
- API: OpenAI-compatible على `http://localhost:3000/api`
- يستطيع Cline استخدام Evo2 كوكيل برمجة مع وصول كامل لقاعدة المعرفة

---

## تحديث القاعدة

لإضافة وثائق جديدة:
1. أنشئ ملف `.md` في `C:\saleh26\researchai\rag_docs\`
2. ارفعه عبر Open WebUI API:
   ```
   POST http://localhost:3000/api/v1/files/
   ```
3. أضفه لقاعدة المعرفة:
   ```
   POST http://localhost:3000/api/v1/knowledge/{id}/file/add
   ```
