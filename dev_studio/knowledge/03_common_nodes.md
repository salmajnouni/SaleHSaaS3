# أهم عقد n8n وإعداداتها

> ملاحظة حاكمة: هذا الملف تعليمي عام لعقد n8n، وليس قائمة بالعقد أو القدرات المضمونة في التشغيل الحالي داخل SaleHSaaS.

## 1. Schedule Trigger

- **الوظيفة**: جدولة سير العمل ليبدأ في وقت محدد.
- **أهم الإعدادات**: `parameters.rule.interval`
- **مثال (كل يوم الساعة 8 صباحاً)**:
  ```json
  "parameters": {
    "rule": {
      "interval": [{"field": "cronExpression", "expression": "0 8 * * *"}]
    }
  }
  ```

## 2. Webhook

- **الوظيفة**: بدء سير العمل عند استقبال طلب HTTP على رابط معين.
- **أهم الإعدادات**: `parameters.httpMethod`, `parameters.path`
- **مثال (استقبال طلب POST على رابط `my-hook`)**:
  ```json
  "parameters": {
    "httpMethod": "POST",
    "path": "my-hook",
    "authentication": "none"
  }
  ```

## 3. Send Email

- **الوظيفة**: إرسال بريد إلكتروني.
- **أهم الإعدادات**: `parameters.fromEmail`, `parameters.toEmail`, `parameters.subject`, `parameters.message`
- **ملاحظة**: يتطلب إعداد بيانات اعتماد SMTP في n8n.

## 4. HTTP Request

- **الوظيفة**: استدعاء API خارجي.
- **أهم الإعدادات**: `parameters.method`, `parameters.url`, `parameters.authentication`, `parameters.body`

## 5. MySQL / PostgreSQL

- **الوظيفة**: تنفيذ استعلامات على قاعدة بيانات.
- **أهم الإعدادات**: `parameters.operation` (executeQuery, insert, update), `parameters.query`

## 6. Code

- **الوظيفة**: كتابة كود JavaScript مخصص لمعالجة البيانات.
- **أهم الإعدادات**: `parameters.jsCode`
- **مثال (إعادة هيكلة البيانات)**:
  ```javascript
  const items = $input.all();
  return items.map(item => {
    return {
      json: {
        newName: item.json.oldName,
        newStatus: 'processed'
      }
    };
  });
  ```

## 7. IF

- **الوظيفة**: توجيه سير العمل بناءً على شرط.
- **أهم الإعدادات**: `parameters.conditions`
- **مثال (إذا كانت قيمة `status` تساوي `completed`)**:
  ```json
  "parameters": {
    "conditions": {
      "string": [
        {
          "value1": "{{ $json.status }}",
          "operation": "equal",
          "value2": "completed"
        }
      ]
    }
  }
  ```

## 8. Set

- **الوظيفة**: إنشاء أو تعديل حقول في البيانات.
- **أهم الإعدادات**: `parameters.values`
- **مثال (إضافة حقل `processedAt` بقيمة الوقت الحالي)**:
  ```json
  "parameters": {
    "values": {
      "string": [
        {
          "name": "processedAt",
          "value": "{{ $now.toISO() }}"
        }
      ]
    },
    "keepOnlySet": false
  }
  ```
