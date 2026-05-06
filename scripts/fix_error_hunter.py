"""Fix Error Hunter workflow: final_response + search query."""
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
    "http://localhost:5678/api/v1/workflows/ErrSltnHntrV2", headers=h
)
wf = r.json()
nodes = wf.get("nodes", [])

# Fix final_response to include report text and handle missing build_report
FINAL_CODE = """const fail = $('normalize_input').first().json || {};
if (fail.skip === true) {
  return [{ json: { status: 'rejected', message: fail.reason } }];
}
let inp = {};
try { inp = $('build_report').first().json || {}; } catch(e) { inp = {}; }
const runId = inp.runId || 'unknown';
const reportPath = inp.filepath || '';
const refs = inp.refs ?? 0;
const report = inp.report || '';
const writeErr = inp.error ? (typeof inp.error === 'object' ? (inp.error.message || JSON.stringify(inp.error)) : String(inp.error)) : '';
const status = writeErr ? 'partial_success' : 'success';
const message = writeErr ? 'Search and report build succeeded, file write failed: ' + writeErr : 'Workflow executed successfully';
return [{ json: { status, message, runId, reportPath, refs, report } }];"""

# Fix build_report to include report text in JSON output
BUILD_PATCH = True

changes = []
for n in nodes:
    name = n.get("name", "")

    if name == "search_searxng":
        params = n["parameters"]["queryParameters"]["parameters"]
        for p in params:
            if p["name"] == "q":
                p["value"] = "={{ $json.problemText }}"
        # Add engines parameter to force working engines (bing, github)
        has_engines = any(p["name"] == "engines" for p in params)
        if not has_engines:
            params.append({"name": "engines", "value": "bing,github"})
        else:
            for p in params:
                if p["name"] == "engines":
                    p["value"] = "bing,github"
        changes.append("search_searxng: fixed query + forced bing,github engines")

    if name == "build_report":
        old_code = n["parameters"]["jsCode"]
        # Add report to JSON output
        new_code = old_code.replace(
            "json: { runId: base.runId, filepath, refs: results.length }",
            "json: { runId: base.runId, filepath, refs: results.length, report }"
        )
        if new_code != old_code:
            n["parameters"]["jsCode"] = new_code
            changes.append("build_report: added report text to JSON")
        else:
            changes.append("build_report: already has report (no change needed)")

    if name == "final_response":
        n["parameters"]["jsCode"] = FINAL_CODE
        changes.append("final_response: includes report in output")

payload = {
    "name": wf["name"],
    "nodes": nodes,
    "connections": wf["connections"],
    "settings": wf.get("settings", {}),
}
r = requests.put(
    "http://localhost:5678/api/v1/workflows/ErrSltnHntrV2",
    headers=h,
    json=payload,
)
print("Update:", r.status_code)

r2 = requests.post(
    "http://localhost:5678/api/v1/workflows/ErrSltnHntrV2/activate", headers=h
)
print("Activate:", r2.status_code)

for c in changes:
    print("  ✓", c)

# Verify $() syntax preserved
wf2 = requests.get("http://localhost:5678/api/v1/workflows/ErrSltnHntrV2", headers=h).json()
for n in wf2["nodes"]:
    if n["name"] == "final_response":
        code = n["parameters"]["jsCode"]
        ok = "$('normalize_input')" in code and "$('build_report')" in code
        print(f"  Verify $() syntax preserved: {ok}")
        if not ok:
            print("  WARNING: $() stripped! First 200 chars:", code[:200])
        break
