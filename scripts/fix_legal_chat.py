"""Fix the legal chat workflow: question extraction + Ollama JSON body."""
import requests
import json

env = dict(
    line.strip().split("=", 1)
    for line in open(".env")
    if "=" in line and not line.startswith("#")
)
key = env["N8N_API_KEY"]
h = {"X-N8N-API-KEY": key, "Content-Type": "application/json"}

r = requests.get(
    "http://localhost:5678/api/v1/workflows/heyEz7Msi6myluLX", headers=h
)
wf = r.json()
nodes = wf.get("nodes", [])

# Fix 1: Question extraction — use explicit node reference ($input gets stripped)
JS_CODE = """// استخراج رسالة المستخدم
const data = $('📦 استخراج البيانات').first().json;
const message = data.chatInput || data.message || data.question || data.query || '';
const sessionId = data.sessionId || 'default';

return [{ json: { query: message, sessionId: sessionId, timestamp: new Date().toISOString() } }];"""

# Fix 2: Ollama JSON body — return object directly (not stringify)
# specifyBody=json means n8n needs a JS object, not a string
OLLAMA_BODY = (
    "={{ { "
    "model: 'qwen2.5:7b', "
    "messages: ["
    "{ role: 'system', content: ($json.systemPrompt || '') }, "
    "{ role: 'user', content: ($json.query || '') }"
    "], "
    "stream: false, "
    "options: { temperature: 0.3, num_predict: 2048 }"
    " } }}"
)

changes = []
for n in nodes:
    name = n.get("name", "")

    if name == "📝 استخراج السؤال":
        n["parameters"]["jsCode"] = JS_CODE
        changes.append("Fixed question extraction")

    if name == "🧠 Ollama: توليد الإجابة":
        n["parameters"]["jsonBody"] = OLLAMA_BODY
        n["parameters"]["options"]["timeout"] = 600000  # 10 min for model swap
        changes.append("Fixed Ollama JSON body + timeout 600s")

payload = {
    "name": wf["name"],
    "nodes": nodes,
    "connections": wf["connections"],
    "settings": wf.get("settings", {}),
}
r = requests.put(
    "http://localhost:5678/api/v1/workflows/heyEz7Msi6myluLX",
    headers=h,
    json=payload,
)
print("Update:", r.status_code)

r2 = requests.post(
    "http://localhost:5678/api/v1/workflows/heyEz7Msi6myluLX/activate", headers=h
)
print("Activate:", r2.status_code)

for c in changes:
    print("  ✓", c)
