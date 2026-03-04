# واجهة برمجة تطبيقات n8n (REST API)

n8n يوفر REST API للتحكم في سير العمل والتنفيذات برمجياً.

## المصادقة (Authentication)

كل الطلبات يجب أن تحتوي على Header باسم `X-N8N-API-KEY` وقيمته هي مفتاح API الذي تولّده من إعدادات n8n.

```bash
curl -X GET 'https://n8n.example.com/api/v1/workflows' \
  -H 'X-N8N-API-KEY: your-api-key'
```

## أهم نقاط النهاية (Endpoints)

### سير العمل (Workflows)

- **`GET /api/v1/workflows`**: جلب قائمة بكل سير العمل.
- **`POST /api/v1/workflows`**: إنشاء سير عمل جديد من JSON.
- **`GET /api/v1/workflows/{id}`**: جلب سير عمل معين بمعرّفه.
- **`PUT /api/v1/workflows/{id}`**: تحديث سير عمل معين.
- **`DELETE /api/v1/workflows/{id}`**: حذف سير عمل معين.
- **`POST /api/v1/workflows/{id}/activate`**: تفعيل سير عمل (جعله نشطاً).
- **`POST /api/v1/workflows/{id}/deactivate`**: إلغاء تفعيل سير عمل.

### التنفيذات (Executions)

- **`GET /api/v1/executions`**: جلب قائمة بكل التنفيذات.
- **`GET /api/v1/executions?workflowId={id}`**: جلب تنفيذات سير عمل معين.
- **`GET /api/v1/executions/{id}`**: جلب تفاصيل تنفيذ معين.
- **`DELETE /api/v1/executions/{id}`**: حذف تنفيذ معين.

## ترقيم الصفحات (Pagination)

عند جلب قوائم طويلة (مثل التنفيذات)، استخدم `limit` و `cursor` للتنقل بين الصفحات.

- **`limit`**: عدد العناصر في كل صفحة (الافتراضي 250).
- **`cursor`**: معرّف الصفحة التالية الذي تحصل عليه من استجابة الصفحة الحالية.

```bash
# جلب أول 50 تنفيذ
curl '.../api/v1/executions?limit=50'

# جلب الصفحة التالية
curl '.../api/v1/executions?limit=50&cursor=next-page-cursor'
```
