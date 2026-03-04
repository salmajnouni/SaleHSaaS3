# أمثلة سير عمل كاملة جاهزة للاستيراد في n8n

## مثال 1: تقرير يومي بالبريد الإلكتروني

سير عمل يُشغَّل كل يوم الساعة 8 صباحاً ويرسل تقريراً بالبريد الإلكتروني.

```json
{
  "name": "Daily Email Report",
  "nodes": [
    {
      "id": "node-1",
      "name": "Schedule Trigger",
      "type": "n8n-nodes-base.scheduleTrigger",
      "typeVersion": 1.1,
      "position": [250, 300],
      "parameters": {
        "rule": {
          "interval": [
            {
              "field": "cronExpression",
              "expression": "0 8 * * *"
            }
          ]
        }
      }
    },
    {
      "id": "node-2",
      "name": "Send Email",
      "type": "n8n-nodes-base.emailSend",
      "typeVersion": 2.1,
      "position": [500, 300],
      "parameters": {
        "fromEmail": "noreply@example.com",
        "toEmail": "admin@example.com",
        "subject": "التقرير اليومي - {{ $now.toFormat('yyyy-MM-dd') }}",
        "message": "مرحباً،\n\nهذا هو التقرير اليومي ليوم {{ $now.toFormat('dd/MM/yyyy') }}.\n\nمع التحية",
        "options": {}
      },
      "credentials": {
        "smtp": {"id": "1", "name": "SMTP Account"}
      }
    }
  ],
  "connections": {
    "Schedule Trigger": {
      "main": [[{"node": "Send Email", "type": "main", "index": 0}]]
    }
  },
  "settings": {"executionOrder": "v1"}
}
```

---

## مثال 2: استقبال Webhook وحفظ البيانات في MySQL

```json
{
  "name": "Webhook to MySQL",
  "nodes": [
    {
      "id": "node-1",
      "name": "Webhook",
      "type": "n8n-nodes-base.webhook",
      "typeVersion": 2,
      "position": [250, 300],
      "parameters": {
        "httpMethod": "POST",
        "path": "save-data",
        "authentication": "none",
        "responseMode": "onReceived",
        "responseData": "firstEntryJson"
      }
    },
    {
      "id": "node-2",
      "name": "MySQL Insert",
      "type": "n8n-nodes-base.mySql",
      "typeVersion": 2.4,
      "position": [500, 300],
      "parameters": {
        "operation": "insert",
        "table": "records",
        "columns": "name, email, created_at",
        "dataMode": "autoMapInputData"
      },
      "credentials": {
        "mySql": {"id": "2", "name": "MySQL Connection"}
      }
    }
  ],
  "connections": {
    "Webhook": {
      "main": [[{"node": "MySQL Insert", "type": "main", "index": 0}]]
    }
  },
  "settings": {"executionOrder": "v1"}
}
```

---

## مثال 3: سير عمل مع شرط IF

```json
{
  "name": "Conditional Workflow",
  "nodes": [
    {
      "id": "node-1",
      "name": "Webhook",
      "type": "n8n-nodes-base.webhook",
      "typeVersion": 2,
      "position": [250, 300],
      "parameters": {"httpMethod": "POST", "path": "check-status"}
    },
    {
      "id": "node-2",
      "name": "Check Status",
      "type": "n8n-nodes-base.if",
      "typeVersion": 2,
      "position": [500, 300],
      "parameters": {
        "conditions": {
          "options": {"caseSensitive": true},
          "conditions": [
            {
              "id": "cond-1",
              "leftValue": "={{ $json.status }}",
              "rightValue": "active",
              "operator": {"type": "string", "operation": "equals"}
            }
          ]
        }
      }
    },
    {
      "id": "node-3",
      "name": "Active Action",
      "type": "n8n-nodes-base.set",
      "typeVersion": 3.4,
      "position": [750, 200],
      "parameters": {
        "assignments": {
          "assignments": [
            {"id": "a1", "name": "result", "value": "تم تفعيل الحساب", "type": "string"}
          ]
        }
      }
    },
    {
      "id": "node-4",
      "name": "Inactive Action",
      "type": "n8n-nodes-base.set",
      "typeVersion": 3.4,
      "position": [750, 400],
      "parameters": {
        "assignments": {
          "assignments": [
            {"id": "a2", "name": "result", "value": "الحساب غير نشط", "type": "string"}
          ]
        }
      }
    }
  ],
  "connections": {
    "Webhook": {
      "main": [[{"node": "Check Status", "type": "main", "index": 0}]]
    },
    "Check Status": {
      "main": [
        [{"node": "Active Action", "type": "main", "index": 0}],
        [{"node": "Inactive Action", "type": "main", "index": 0}]
      ]
    }
  },
  "settings": {"executionOrder": "v1"}
}
```

---

## مثال 4: جلب تقرير التنفيذات عبر n8n Node

```json
{
  "name": "Execution Report",
  "nodes": [
    {
      "id": "node-1",
      "name": "Schedule Trigger",
      "type": "n8n-nodes-base.scheduleTrigger",
      "typeVersion": 1.1,
      "position": [250, 300],
      "parameters": {
        "rule": {"interval": [{"field": "cronExpression", "expression": "0 9 * * 1"}]}
      }
    },
    {
      "id": "node-2",
      "name": "Get Executions",
      "type": "n8n-nodes-base.n8n",
      "typeVersion": 1,
      "position": [500, 300],
      "parameters": {
        "resource": "execution",
        "operation": "getMany",
        "returnAll": false,
        "limit": 50,
        "filters": {"status": "error"}
      },
      "credentials": {
        "n8nApi": {"id": "3", "name": "n8n API"}
      }
    }
  ],
  "connections": {
    "Schedule Trigger": {
      "main": [[{"node": "Get Executions", "type": "main", "index": 0}]]
    }
  },
  "settings": {"executionOrder": "v1"}
}
```
