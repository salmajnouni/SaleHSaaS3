# SaleHSaaS Multi-Agent System (MCP)
## نظام متعدد الوكلاء مع بروتوكول MCP

---

## البنية المعمارية

```
Open WebUI
    │
    ▼
n8n_bridge (port 3333)
    │
    ▼
┌─────────────────────────────────────────┐
│     Orchestrator Agent (المنسق)          │
│     mcp_orchestrator_agent.json          │
│     Tag: n8n-openai-bridge               │
└──────────────┬──────────────────────────┘
               │ يستدعي عبر Workflow Tool
    ┌──────────┼──────────┬──────────────┐
    ▼          ▼          ▼              ▼
┌────────┐ ┌────────┐ ┌────────┐ ┌──────────┐
│Research│ │Automat.│ │Knowled.│ │  Models  │
│ Agent  │ │ Agent  │ │ Agent  │ │  Agent   │
└───┬────┘ └───┬────┘ └───┬────┘ └────┬─────┘
    │          │          │           │
    │     MCP Client   MCP Client  MCP Client
    │          │          │           │
 Wikipedia  n8n_builder  legal_rag  ollama_mgr
 SearXNG    file_api     ChromaDB   Ollama API
 Weather    Code Tool    Wikipedia
 News RSS
```

---

## ترتيب الاستيراد في n8n

**مهم:** استورد الـ sub-agents أولاً، ثم الـ Orchestrator.

### الخطوة 1: استيراد Sub-Agents (بالترتيب)

```
1. mcp_research_agent.json    → اسم: salehsaas-research-agent
2. mcp_automation_agent.json  → اسم: salehsaas-automation-agent
3. mcp_knowledge_agent.json   → اسم: salehsaas-knowledge-agent
4. mcp_models_agent.json      → اسم: salehsaas-models-agent
```

### الخطوة 2: استيراد الـ Orchestrator

```
5. mcp_orchestrator_agent.json → يظهر في Open WebUI تلقائياً
```

---

## إعداد Credential لـ Ollama

في n8n: **Settings → Credentials → New → Ollama**

```
Name:     Ollama Local
Base URL: http://host.docker.internal:11434
```

---

## ربط Workflow Tool بالـ Sub-Agents

في الـ Orchestrator، كل `toolWorkflow` يحتاج ربطه بـ workflow ID الصحيح:

1. افتح `mcp_orchestrator_agent.json` في n8n
2. انقر على كل tool من الأدوات الأربعة
3. في حقل `Workflow` اختر الـ workflow المقابل بالاسم

---

## متطلبات MCPO

تأكد أن MCPO يعمل على `http://mcpo:8000` مع الـ servers التالية:
- `/n8n_builder/sse`
- `/ollama_model_builder/sse`
- `/saleh_legal_rag/sse`

---

## اختبار النظام

بعد الاستيراد والتفعيل، جرّب في Open WebUI:

| الطلب | الوكيل المتوقع |
|---|---|
| "ما هو الطقس في الرياض؟" | Research Agent |
| "أنشئ workflow لإرسال إيميل يومي" | Automation Agent |
| "ما هو نظام العمل السعودي؟" | Knowledge Agent |
| "اعرض النماذج المتاحة" | Models Agent |
| "ابحث عن الذكاء الاصطناعي ثم أنشئ workflow" | Orchestrator → Research + Automation |
