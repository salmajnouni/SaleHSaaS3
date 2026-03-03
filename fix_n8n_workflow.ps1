# ============================================================
# إصلاح workflow مساعد القوانين السعودية تلقائياً
# شغّل هذا السكريبت مرة واحدة فقط
# ============================================================

$N8N_URL = "http://localhost:5678"
$API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2MzM4ZjBkYi1kOTIwLTRmMGItOTE3Yi0xZjg3MDAyMDdiNjgiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwianRpIjoiNjkxNDA2MDctZTQ0MC00ZDZiLTk3NjktOWJiNmFhNjkxMTliIiwiaWF0IjoxNzcyNTIwMTYzLCJleHAiOjE3NzUwNzcyMDB9.sET4Cp57eYI5y_w9gfmFiPY260YolvUh9sVIglp7muA"

$HEADERS = @{
    "X-N8N-API-KEY" = $API_KEY
    "Content-Type"  = "application/json"
}

# الكود الصحيح لـ node تنسيق الإجابة
$FIXED_CODE = @'
// تنسيق الإجابة النهائية
const rawInput = $input.first().json;
const ollamaResponse = (rawInput && rawInput.data) ? rawInput.data : rawInput;
const contextData = $('📚 تجهيز السياق القانوني').first().json;

let answer = '';
try {
  const msgObj = (ollamaResponse && ollamaResponse.message) ? ollamaResponse.message : {};
  answer = (msgObj && msgObj.content) ? msgObj.content : '';
  if (!answer) {
    answer = (ollamaResponse && ollamaResponse.response) ? ollamaResponse.response : '';
  }
} catch(e) {
  answer = '';
}

if (!answer || answer.trim() === '') {
  answer = 'عذراً، لم أتمكن من توليد إجابة. يرجى المحاولة مرة أخرى.';
}

if (contextData && contextData.hasContext && contextData.sources && contextData.sources.length > 0) {
  answer += '\n\n---\n📚 **المصادر:** ' + contextData.sources.join('، ');
}

return [{ json: { output: answer } }];
'@

Write-Host "1. جلب قائمة الـ workflows..." -ForegroundColor Cyan
try {
    $resp = Invoke-RestMethod -Uri "$N8N_URL/api/v1/workflows" -Headers $HEADERS -Method GET -UseBasicParsing
} catch {
    Write-Host "❌ فشل الاتصال بـ n8n: $_" -ForegroundColor Red
    exit 1
}

$workflows = $resp.data
Write-Host "   وجدت $($workflows.Count) workflow" -ForegroundColor Green

# البحث عن الـ workflow الصحيح
$targetWf = $null
foreach ($wf in $workflows) {
    $tags = $wf.tags | ForEach-Object { $_.name }
    if ($tags -contains 'n8n-openai-bridge' -and $tags -contains 'chat') {
        $targetWf = $wf
        Write-Host "   ✅ وجدت: $($wf.name) (ID: $($wf.id))" -ForegroundColor Green
        break
    }
}

if (-not $targetWf) {
    foreach ($wf in $workflows) {
        if ($wf.name -like '*Saudi Laws Assistant*' -or $wf.name -like '*مساعد القوانين*') {
            $targetWf = $wf
            Write-Host "   ✅ وجدت بالاسم: $($wf.name) (ID: $($wf.id))" -ForegroundColor Green
            break
        }
    }
}

if (-not $targetWf) {
    Write-Host "❌ لم أجد الـ workflow!" -ForegroundColor Red
    Write-Host "الـ workflows المتاحة:"
    foreach ($wf in $workflows) { Write-Host "   - $($wf.name)" }
    exit 1
}

$wfId = $targetWf.id

Write-Host "`n2. جلب تفاصيل الـ workflow..." -ForegroundColor Cyan
try {
    $wfData = Invoke-RestMethod -Uri "$N8N_URL/api/v1/workflows/$wfId" -Headers $HEADERS -Method GET -UseBasicParsing
} catch {
    Write-Host "❌ فشل: $_" -ForegroundColor Red
    exit 1
}

$nodes = $wfData.nodes
Write-Host "   عدد الـ nodes: $($nodes.Count)" -ForegroundColor Green

# تعديل node تنسيق الإجابة
$fixed = $false
for ($i = 0; $i -lt $nodes.Count; $i++) {
    $name = $nodes[$i].name
    if ($name -like '*تنسيق*' -and $name -like '*الإجابة*') {
        Write-Host "   ✅ وجدت node: $name" -ForegroundColor Green
        $nodes[$i].parameters.jsCode = $FIXED_CODE
        $fixed = $true
        Write-Host "   ✅ تم تعديل الكود" -ForegroundColor Green
        break
    }
}

if (-not $fixed) {
    Write-Host "⚠️ لم أجد node تنسيق الإجابة. الـ nodes:" -ForegroundColor Yellow
    foreach ($n in $nodes) { Write-Host "   - $($n.name)" }
    exit 1
}

Write-Host "`n3. رفع الـ workflow المُعدَّل..." -ForegroundColor Cyan
$wfData.nodes = $nodes
$body = $wfData | ConvertTo-Json -Depth 20 -Compress

try {
    $putResp = Invoke-RestMethod -Uri "$N8N_URL/api/v1/workflows/$wfId" `
        -Headers $HEADERS -Method PUT -Body $body -UseBasicParsing
    Write-Host "   ✅ تم الرفع بنجاح!" -ForegroundColor Green
} catch {
    Write-Host "❌ فشل الرفع: $_" -ForegroundColor Red
    exit 1
}

Write-Host "`n4. تفعيل الـ workflow..." -ForegroundColor Cyan
try {
    $activeBody = '{"active": true}'
    Invoke-RestMethod -Uri "$N8N_URL/api/v1/workflows/$wfId/activate" `
        -Headers $HEADERS -Method POST -Body $activeBody -UseBasicParsing | Out-Null
    Write-Host "   ✅ الـ workflow مفعّل" -ForegroundColor Green
} catch {
    Write-Host "   ⚠️ تحقق من التفعيل يدوياً" -ForegroundColor Yellow
}

Write-Host "`n============================================" -ForegroundColor Green
Write-Host "✅ تم الإصلاح بنجاح!" -ForegroundColor Green
Write-Host "   الـ workflow: $($targetWf.name)" -ForegroundColor Green
Write-Host "   الآن اختبر المحادثة في Open WebUI" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
