# n8n as a Universal Tool for All Models and Agents

**الـ n8n أداة عامة متاحة لجميع الـ models والـ agents وليس حكراً على agent واحد**

---

## Table of Contents

1. [Philosophy](#philosophy)
2. [Access Methods](#access-methods)
3. [Python API](#python-api)
4. [Command Line Interface](#command-line-interface)
5. [REST API](#rest-api)
6. [Examples](#examples)
7. [Council-Specific Examples](#council-specific-examples)

---

## Philosophy

n8n is a powerful workflow automation tool that should be accessible to:
- ✅ Any Python script (via `n8n_api` module)
- ✅ Any Agent/Model (via CLI commands)
- ✅ Any service (via REST API webhooks)
- ✅ Any process (via Docker container)

**No AI model should be limited to a single agent. n8n is a shared resource.**

---

## Access Methods

### Method 1: Python API (Recommended for Models)

```python
from scripts.n8n.n8n_api import N8nWebhook, N8nWorkflow, CouncilWorkflow

# أي Python model/agent يمكنه استخدام هذا
webhook = N8nWebhook("council-intake")
result = webhook.trigger({"topic": "test"})
```

### Method 2: Command Line (For Scripts/Automation)

```bash
python scripts/n8n/n8n_cli.py list-workflows
python scripts/n8n/n8n_cli.py webhook --path council-intake --data '{"topic":"..."}'
```

### Method 3: REST API (Direct HTTP)

```bash
curl -X POST http://localhost:5678/webhook/council-intake \
  -H "Content-Type: application/json" \
  -d '{"topic":"...","study_type":"legal"}'
```

### Method 4: Docker Exec (For Container-to-Container)

```bash
docker exec salehsaas_n8n curl -X POST http://localhost:5678/webhook/council-intake ...
```

---

## Python API

### Basic Usage

#### 1. Trigger a Webhook

```python
from scripts.n8n.n8n_api import N8nWebhook

webhook = N8nWebhook(path="council-intake")
result = webhook.trigger(data={
    "topic": "What is the best policy?",
    "study_type": "legal",
    "requested_by": "أحمد"
})

if result["success"]:
    print(f"Webhook triggered successfully: {result['response']}")
else:
    print(f"Error: {result['error']}")
```

#### 2. Execute a Workflow

```python
from scripts.n8n.n8n_api import N8nWorkflow

workflow = N8nWorkflow(workflow_id="CwCounclWbhk001")
result = workflow.execute(data={
    "topic": "Legal opinion request",
    "priority": "high"
})

print(result)
```

#### 3. Get Workflow Executions

```python
workflow = N8nWorkflow(workflow_id="CwCounclWbhk001")
executions = workflow.get_executions(limit=20)

for execution in executions["executions"]:
    print(f"ID: {execution['id']}, Status: {execution['status']}")
```

#### 4. Activate/Deactivate Workflow

```python
workflow = N8nWorkflow(workflow_id="CwCounclWbhk001")

# Activate
workflow.activate()

# Deactivate
workflow.deactivate()
```

### Council-Specific Convenience Class

```python
from scripts.n8n.n8n_api import CouncilWorkflow

# Submit council request
result = CouncilWorkflow.submit_request(
    topic="Should we implement new security policy?",
    study_type="cyber",
    requester="صالح",
    priority="high"
)

# Send Telegram decision
result = CouncilWorkflow.send_telegram_decision(
    session_id="session_123",
    decision="approve",
    notes="Approved with conditions"
)
```

### Health Check

```python
from scripts.n8n.n8n_api import check_n8n_health

health = check_n8n_health()
if health["healthy"]:
    print("n8n is running")
else:
    print(f"n8n error: {health['error']}")
```

---

## Command Line Interface

### List All Workflows

```bash
python scripts/n8n/n8n_cli.py list-workflows
```

Output:
```
ID                  Name                                    Status
CwCounclWbhk001    Advisory Council Webhook Intake         active
CwCounclTele001    Telegram Decision Handler               active
...
```

### Trigger Webhook

```bash
python scripts/n8n/n8n_cli.py webhook \
  --path council-intake \
  --data '{"topic":"test","study_type":"legal","requested_by":"أحمد"}'
```

### Submit Council Request

```bash
python scripts/n8n/n8n_cli.py council \
  --topic "Need legal review" \
  --type legal \
  --requester "صالح"
```

### Activate Workflow

```bash
python scripts/n8n/n8n_cli.py activate --id CwCounclWbhk001
```

### View Logs

```bash
python scripts/n8n/n8n_cli.py logs
```

### Health Check

```bash
python scripts/n8n/n8n_cli.py health
```

---

## REST API

### Trigger Webhook Directly

```bash
curl -X POST http://localhost:5678/webhook/council-intake \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "What is the best approach?",
    "study_type": "legal",
    "requested_by": "أحمد",
    "source": "external"
  }'
```

### Execute Workflow

```bash
curl -X POST http://localhost:5678/rest/workflows/{workflow_id}/execute \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "test"
  }'
```

### Get Health Status

```bash
curl http://localhost:5678/rest/health
```

---

## Examples

### Example 1: Python Script Submitting Council Request

```python
#!/usr/bin/env python3
"""
برنامج Python يقدم طلب مجلس استشاري
Python program submitting council request
"""

import sys
sys.path.insert(0, '/path/to/SaleHSaaS3')

from scripts.n8n.n8n_api import CouncilWorkflow

def main():
    result = CouncilWorkflow.submit_request(
        topic="Should we implement blockchain for contract management?",
        study_type="technical",
        requester="محمد علي",
        priority="high"
    )
    
    if result["success"]:
        print(f"✅ Council request submitted successfully")
        print(f"Response: {result['response']}")
    else:
        print(f"❌ Failed: {result['error']}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

### Example 2: Using n8n in Custom Agent

```python
# Inside any agent's code
from scripts.n8n.n8n_api import N8nWebhook

class MyCustomAgent:
    def process_request(self, request_data):
        # Process locally
        processed = self.my_logic(request_data)
        
        # Then delegate to n8n for workflow automation
        webhook = N8nWebhook("custom-process")
        result = webhook.trigger(processed)
        
        return result
```

### Example 3: Batch Process with n8n

```python
from scripts.n8n.n8n_api import CouncilWorkflow

# Process multiple requests
requests = [
    ("Legal policy review", "legal", "أحمد"),
    ("Budget allocation", "financial", "محمد"),
    ("Security audit", "cyber", "علي"),
]

for topic, req_type, requester in requests:
    result = CouncilWorkflow.submit_request(
        topic=topic,
        study_type=req_type,
        requester=requester
    )
    print(f"{'✅' if result['success'] else '❌'} {topic}")
```

---

## Council-Specific Examples

### Example: Complete Council Workflow

```python
from scripts.n8n.n8n_api import CouncilWorkflow
from datetime import datetime

# 1. Submit request
topic = "Should we migrate to cloud infrastructure?"
result = CouncilWorkflow.submit_request(
    topic=topic,
    study_type="technical",
    requester="صالح",
    priority="high"
)

if result["success"]:
    print(f"✅ Council study initiated: {result['response']}")
    session_id = result['response'].get('session_id')
    
    # 2. Later, when council reviews and votes...
    # Telegram buttons send decision back to n8n
    # This is handled automatically by the Telegram workflow
    
else:
    print(f"❌ Failed to submit: {result['error']}")
```

---

## Integration with Other Services

### Integrating with Custom Services

Any service can call n8n workflows:

```python
import requests

def call_n8n_workflow(workflow_id, data):
    """Universal way to call any n8n workflow"""
    response = requests.post(
        f"http://localhost:5678/rest/workflows/{workflow_id}/execute",
        json=data,
        timeout=30
    )
    return response.json()

# Use it anywhere
result = call_n8n_workflow("CwCounclWbhk001", {"topic": "test"})
```

---

## Configuration

### Environment Variables

```bash
# .env
N8N_URL=http://localhost:5678
N8N_ADMIN_KEY=your_api_key_if_exists
COUNCIL_WEBHOOK_URL=http://localhost:5678/webhook/council-intake
```

### Changing n8n Host

```python
from scripts.n8n.n8n_api import N8nConfig

# Override default
N8nConfig.N8N_URL = "http://remote-n8n-server:5678"
```

---

## Available Workflows

| ID | Name | Type | Purpose |
|---|---|---|---|
| CwCounclWbhk001 | Advisory Council Webhook | trigger | Receive and process council requests |
| CwCounclTele001 | Telegram Decisions | http | Handle Telegram button decisions |

---

## Best Practices

### 1. Always Check Health First

```python
from scripts.n8n.n8n_api import check_n8n_health

if not check_n8n_health()["healthy"]:
    raise Exception("n8n is not available")
```

### 2. Handle Errors Gracefully

```python
result = webhook.trigger(data)
if not result["success"]:
    logger.error(f"Webhook failed: {result['error']}")
    # Implement retry logic or fallback
```

### 3. Include Metadata

```python
webhook.trigger({
    "topic": "...",
    "source": "my_agent",
    "priority": "high",
    "timestamp": datetime.now().isoformat()
})
```

### 4. Use CouncilWorkflow for Council Requests

```python
# Good - uses built-in converters
CouncilWorkflow.submit_request(...)

# Avoid - using generic webhook
N8nWebhook("council-intake").trigger(...)
```

---

## Troubleshooting

### n8n not accessible

```bash
# Check if container is running
docker ps | grep salehsaas_n8n

# Check logs
docker logs salehsaas_n8n --tail 50

# Verify port
netstat -an | grep 5678
```

### Webhook not triggering

```bash
# Test directly
python scripts/n8n/n8n_cli.py webhook --path council-intake --data '{}'

# Check n8n logs for errors
python scripts/n8n/n8n_cli.py logs
```

### Authentication Issues

```bash
# If you have an API key, set it
export N8N_ADMIN_KEY=your_key_here

# Then test
python scripts/n8n/n8n_cli.py list-workflows
```

---

## Summary

**n8n is now available as a universal tool:**

✅ **For Python code**: Import `n8n_api` module  
✅ **For CLI/Scripts**: Use `n8n_cli.py` command  
✅ **For HTTP**: Call REST API directly  
✅ **For any Agent/Model**: Use any of the above methods

**No more limitations. Any system can use n8n workflows.**
