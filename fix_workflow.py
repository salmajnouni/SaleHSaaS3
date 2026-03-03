import requests
import json
import sys

N8N_URL = "http://localhost:5678"
API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2MzM4ZjBkYi1kOTIwLTRmMGItOTE3Yi0xZjg3MDAyMDdiNjgiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwianRpIjoiNjkxNDA2MDctZTQ0MC00ZDZiLTk3NjktOWJiNmFhNjkxMTliIiwiaWF0IjoxNzcyNTIwMTYzLCJleHAiOjE3NzUwNzcyMDB9.sET4Cp57eYI5y_w9gfmFiPY260YolvUh9sVIglp7muA"

HEADERS = {
    "X-N8N-API-KEY": API_KEY,
    "Content-Type": "application/json"
}

FIXED_CODE = (
    '// Fixed: parse Ollama response correctly\n'
    'const rawInput = $input.first().json;\n'
    'const ollamaResponse = (rawInput && rawInput.data) ? rawInput.data : rawInput;\n'
    'const contextData = $("\U0001F4DA \u062a\u062c\u0647\u064a\u0632 \u0627\u0644\u0633\u064a\u0627\u0642 \u0627\u0644\u0642\u0627\u0646\u0648\u0646\u064a").first().json;\n'
    'let answer = "";\n'
    'try {\n'
    '  const msgObj = (ollamaResponse && ollamaResponse.message) ? ollamaResponse.message : {};\n'
    '  answer = (msgObj && msgObj.content) ? msgObj.content : "";\n'
    '  if (!answer) { answer = (ollamaResponse && ollamaResponse.response) ? ollamaResponse.response : ""; }\n'
    '} catch(e) { answer = ""; }\n'
    'if (!answer || answer.trim() === "") {\n'
    '  answer = "\u0639\u0630\u0631\u0627\u064b\u060c \u0644\u0645 \u0623\u062a\u0645\u0643\u0646 \u0645\u0646 \u062a\u0648\u0644\u064a\u062f \u0625\u062c\u0627\u0628\u0629. \u064a\u0631\u062c\u0649 \u0627\u0644\u0645\u062d\u0627\u0648\u0644\u0629 \u0645\u0631\u0629 \u0623\u062e\u0631\u0649.";\n'
    '}\n'
    'if (contextData && contextData.hasContext && contextData.sources && contextData.sources.length > 0) {\n'
    '  answer += "\\n\\n---\\n\U0001F4DA **\u0627\u0644\u0645\u0635\u0627\u062f\u0631:** " + contextData.sources.join("\u060c ");\n'
    '}\n'
    'return [{ json: { output: answer } }];'
)

print("Step 1: Getting workflows...")
try:
    resp = requests.get(f"{N8N_URL}/api/v1/workflows", headers=HEADERS)
except Exception as e:
    print(f"ERROR: Cannot connect to n8n: {e}")
    sys.exit(1)

if resp.status_code != 200:
    print(f"ERROR: {resp.status_code} - {resp.text[:200]}")
    sys.exit(1)

workflows = resp.json().get("data", [])
print(f"Found {len(workflows)} workflows")

target = None
for wf in workflows:
    tags = [t.get("name", "") for t in wf.get("tags", [])]
    if "n8n-openai-bridge" in tags and "chat" in tags:
        target = wf
        print(f"Found: {wf['name']} (ID: {wf['id']})")
        break

if not target:
    for wf in workflows:
        if "Saudi Laws Assistant" in wf.get("name", ""):
            target = wf
            print(f"Found by name: {wf['name']} (ID: {wf['id']})")
            break

if not target:
    print("ERROR: Workflow not found!")
    for wf in workflows:
        print(f"  - {wf['name']}")
    sys.exit(1)

wf_id = target["id"]

print(f"Step 2: Getting workflow details (ID: {wf_id})...")
resp = requests.get(f"{N8N_URL}/api/v1/workflows/{wf_id}", headers=HEADERS)
wf_data = resp.json()
nodes = wf_data.get("nodes", [])
print(f"Nodes: {len(nodes)}")

fixed = False
for i, node in enumerate(nodes):
    name = node.get("name", "")
    if "\u062a\u0646\u0633\u064a\u0642" in name:
        print(f"Found format node: {name}")
        nodes[i]["parameters"]["jsCode"] = FIXED_CODE
        fixed = True
        print("Code updated!")
        break

if not fixed:
    print("ERROR: Format node not found. All nodes:")
    for n in nodes:
        print(f"  - {n.get('name', '')}")
    sys.exit(1)

print("Step 3: Uploading fixed workflow...")
wf_data["nodes"] = nodes
resp = requests.put(
    f"{N8N_URL}/api/v1/workflows/{wf_id}",
    headers=HEADERS,
    json=wf_data
)
if resp.status_code not in [200, 201]:
    print(f"ERROR uploading: {resp.status_code} - {resp.text[:300]}")
    sys.exit(1)
print("Upload done!")

print("Step 4: Activating...")
try:
    resp = requests.post(
        f"{N8N_URL}/api/v1/workflows/{wf_id}/activate",
        headers=HEADERS,
        json={}
    )
    print("Activated!")
except Exception as e:
    print(f"Check activation manually: {e}")

print("")
print("SUCCESS! Test the chat in Open WebUI now.")
