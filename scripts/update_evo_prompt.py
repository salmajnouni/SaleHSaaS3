import os
import requests
import json

WEBUI_API_KEY = os.getenv("WEBUI_API_KEY")
if not WEBUI_API_KEY:
    raise ValueError("WEBUI_API_KEY environment variable is required")

h = {"Authorization": f"Bearer {WEBUI_API_KEY}", "Content-Type": "application/json"}

# Get current model state
r = requests.get('http://localhost:3000/api/models', headers=h)
data = r.json()
models = data.get('data', data.get('models', data if isinstance(data, list) else []))
evo = None
for m in models:
    if m.get('id') == 'evo':
        evo = m
        break

info = evo['info']
meta = info.get('meta', {})

SYSTEM_PROMPT = """أنت الرئيس — المستشار الذكي الشخصي لصالح المجنوني في منصة SaleH SaaS.

## المجالس الاستشارية
لديك 3 مجالس استشارية متخصصة. يجب استدعاؤها عبر الأدوات (Tools) المتاحة:

1. **مجلس الابتكار** (ask_innovation_council) — لتقييم الأفكار والمشاريع الجديدة.
2. **مجلس الحوكمة التقنية** (ask_tech_governance_council) — لتقييم القرارات التقنية.
3. **مجلس المراجعة القانونية** (ask_legal_review_council) — لمراجعة التوافق النظامي.

### قاعدة صارمة:
إذا ذكر المستخدم كلمة "مجلس" أو "استشر" أو "council" → يجب أن تستدعي الأداة (tool call) فوراً.
لا تبحث في الويب. لا تجب من عندك. استدعِ الأداة مباشرة.

## القواعد العامة:
- تحدث بالعربية بشكل طبيعي.
- كن مباشراً ومختصراً.
- لا تدّعِ قدرات لا تملكها."""

# Restore full capabilities
meta['system'] = SYSTEM_PROMPT
meta['toolIds'] = ['councils_advisory']
meta['skillIds'] = ['step-back-prompting', 'self-consistency', 'chain-of-thought', 'react-agent']
meta['capabilities'] = {
    'file_context': True,
    'vision': True,
    'file_upload': True,
    'web_search': True,
    'image_generation': True,
    'code_interpreter': True,
    'citations': True,
    'status_updates': True,
    'usage': True,
    'builtin_tools': True,
    'tools': True,
}
meta['defaultFeatureIds'] = ['web_search', 'image_generation', 'code_interpreter']
meta['builtinTools'] = {
    'time': True,
    'memory': True,
    'chats': True,
    'notes': True,
    'knowledge': True,
    'channels': True,
    'web_search': True,
    'image_generation': True,
    'code_interpreter': True,
}

payload = {
    'id': 'evo',
    'name': info['name'],
    'meta': meta,
    'params': info.get('params', {}),
    'base_model_id': info.get('base_model_id'),
}

r2 = requests.post('http://localhost:3000/api/v1/models/model/update', headers=h, json=payload)
print('Update status:', r2.status_code)
if r2.status_code == 200:
    updated = r2.json()
    print('toolIds:', updated.get('meta', {}).get('toolIds', []))
    print('capabilities:', json.dumps(updated.get('meta', {}).get('capabilities', {}), indent=2))
    print('system prompt length:', len(updated.get('meta', {}).get('system', '')))
else:
    print('Error:', r2.text[:300])
