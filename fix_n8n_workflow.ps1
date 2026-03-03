# Fix Saudi Laws Chat Workflow via n8n API
# Run: .\fix_n8n_workflow.ps1

$N8N_URL = "http://localhost:5678"
$API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2MzM4ZjBkYi1kOTIwLTRmMGItOTE3Yi0xZjg3MDAyMDdiNjgiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwianRpIjoiNjkxNDA2MDctZTQ0MC00ZDZiLTk3NjktOWJiNmFhNjkxMTliIiwiaWF0IjoxNzcyNTIwMTYzLCJleHAiOjE3NzUwNzcyMDB9.sET4Cp57eYI5y_w9gfmFiPY260YolvUh9sVIglp7muA"

$HEADERS = @{
    "X-N8N-API-KEY" = $API_KEY
    "Content-Type"  = "application/json"
}

Write-Host "Step 1: Getting workflows..."
try {
    $resp = Invoke-RestMethod -Uri "$N8N_URL/api/v1/workflows" -Headers $HEADERS -Method GET -UseBasicParsing
} catch {
    Write-Host "ERROR: $_"
    exit 1
}

$workflows = $resp.data
Write-Host "Found $($workflows.Count) workflows"

$targetWf = $null
foreach ($wf in $workflows) {
    $tags = $wf.tags | ForEach-Object { $_.name }
    if (($tags -contains "n8n-openai-bridge") -and ($tags -contains "chat")) {
        $targetWf = $wf
        Write-Host "Found: $($wf.name) (ID: $($wf.id))"
        break
    }
}

if (-not $targetWf) {
    foreach ($wf in $workflows) {
        if ($wf.name -like "*Saudi Laws Assistant*") {
            $targetWf = $wf
            Write-Host "Found by name: $($wf.name)"
            break
        }
    }
}

if (-not $targetWf) {
    Write-Host "ERROR: Workflow not found!"
    foreach ($wf in $workflows) { Write-Host "  - $($wf.name)" }
    exit 1
}

$wfId = $targetWf.id
Write-Host "Step 2: Getting workflow (ID: $wfId)..."
$wfData = Invoke-RestMethod -Uri "$N8N_URL/api/v1/workflows/$wfId" -Headers $HEADERS -Method GET -UseBasicParsing
$nodes = $wfData.nodes
Write-Host "Nodes: $($nodes.Count)"

$fixed = $false
for ($i = 0; $i -lt $nodes.Count; $i++) {
    $nodeName = $nodes[$i].name
    if ($nodeName -like "*تنسيق*") {
        Write-Host "Found format node: $nodeName"
        $newCode = @'
// Fixed: parse Ollama response correctly
const rawInput = $input.first().json;
const ollamaResponse = (rawInput && rawInput.data) ? rawInput.data : rawInput;
const contextData = $('📚 تجهيز السياق القانوني').first().json;
let answer = '';
try {
  const msgObj = (ollamaResponse && ollamaResponse.message) ? ollamaResponse.message : {};
  answer = (msgObj && msgObj.content) ? msgObj.content : '';
  if (!answer) { answer = (ollamaResponse && ollamaResponse.response) ? ollamaResponse.response : ''; }
} catch(e) { answer = ''; }
if (!answer || answer.trim() === '') {
  answer = 'عذراً، لم أتمكن من توليد إجابة. يرجى المحاولة مرة أخرى.';
}
if (contextData && contextData.hasContext && contextData.sources && contextData.sources.length > 0) {
  answer += '\n\n---\n📚 **المصادر:** ' + contextData.sources.join('، ');
}
return [{ json: { output: answer } }];
        '@
        $nodes[$i].parameters.jsCode = $newCode
        $fixed = $true
        Write-Host "Code updated!"
        break
    }
}

if (-not $fixed) {
    Write-Host "ERROR: Format node not found. Nodes:"
    foreach ($n in $nodes) { Write-Host "  - $($n.name)" }
    exit 1
}

Write-Host "Step 3: Uploading..."
$wfData.nodes = $nodes
$body = $wfData | ConvertTo-Json -Depth 20 -Compress
Invoke-RestMethod -Uri "$N8N_URL/api/v1/workflows/$wfId" -Headers $HEADERS -Method PUT -Body $body -UseBasicParsing | Out-Null
Write-Host "Upload done!"

Write-Host "Step 4: Activating..."
try {
    Invoke-RestMethod -Uri "$N8N_URL/api/v1/workflows/$wfId/activate" -Headers $HEADERS -Method POST -Body "{}" -UseBasicParsing | Out-Null
    Write-Host "Activated!"
} catch { Write-Host "Check activation in n8n manually" }

Write-Host ""
Write-Host "SUCCESS! Test the chat in Open WebUI now."
