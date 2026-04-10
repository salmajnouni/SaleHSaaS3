# 🕋 SaleH Brain - العقل الذكي لمنصة SaleHSaaS 3.0

نظام مراقبة ذكي يعمل بالذكاء الاصطناعي المحلي (Ollama) لإدارة منصة SaleHSaaS تلقائياً.

## ما يفعله

| القدرة | الوصف |
|--------|-------|
| **مراقبة مستمرة** | يقرأ مقاييس Prometheus كل 5 دقائق |
| **تحليل ذكي** | يُرسل البيانات إلى Ollama للتحليل والتوصية |
| **قرارات تلقائية** | يُعيد تشغيل الخدمات المتوقفة بدون تدخل |
| **إدارة المهام** | يُؤجّل مهام n8n الثقيلة عند ارتفاع الحمل |
| **تقديم المهام** | يُشغّل المهام المؤجلة عند انخفاض الحمل |
| **سجل القرارات** | يحفظ كل قرار في `/app/logs/decisions.jsonl` |

## عتبات التنبيه الافتراضية

| المقياس | التحذير | الحرج |
|---------|---------|-------|
| CPU | > 60% | > 80% |
| الذاكرة | > 70% | > 85% |
| CPU منخفض (تقديم مهام) | < 20% | — |

## الإعداد

### 1. إضافة n8n API Key (اختياري للتحكم الكامل)

```bash
# في ملف .env
N8N_API_KEY=your_n8n_api_key_here
```

للحصول على API Key من n8n:
1. افتح http://localhost:5678
2. اذهب إلى Settings → API
3. انسخ الـ API Key

### 2. تشغيل الخدمة

```powershell
cd D:\SaleHSaaS3
docker-compose up -d saleh_brain
```

### 3. مراقبة السجلات

```powershell
docker logs salehsaas_brain -f
```

## استيراد Workflow في n8n

1. افتح http://localhost:5678
2. اضغط **Import from file**
3. اختر الملف: `saleh_brain/n8n_workflows/saleh_brain_monitor.json`
4. فعّل الـ workflow

## تخصيص العتبات

في ملف `.env`:

```env
CPU_HIGH_THRESHOLD=80
CPU_LOW_THRESHOLD=20
MEMORY_HIGH_THRESHOLD=85
BRAIN_CHECK_INTERVAL=300
```
