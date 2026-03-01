# SaleH SaaS 4.0 - سكريبت الإعداد الأولي
# 🕋 صُنع بفخر في مكة المكرمة، المملكة العربية السعودية

# دالة لطباعة الرسائل الملونة
function Write-Host-Color {
    param(
        [string]$Message,
        [string]$Color
    )
    Write-Host $Message -ForegroundColor $Color
}

# ----------------------------------------------------------------------------
# 1. التحقق من Docker
# ----------------------------------------------------------------------------
Write-Host-Color "
[1/5] 🐳 التحقق من تشغيل Docker..." "Cyan"
if (-not (docker info 2>$null)) {
    Write-Host-Color "❌ خطأ: Docker لا يعمل. يرجى تشغيل Docker Desktop والمحاولة مرة أخرى." "Red"
    exit 1
}
Write-Host-Color "✅ Docker يعمل بنجاح." "Green"

# ----------------------------------------------------------------------------
# 2. التحقق من Ollama والنماذج
# ----------------------------------------------------------------------------
Write-Host-Color "
[2/5] 🧠 التحقق من Ollama والنماذج المطلوبة..." "Cyan"
if (-not (ollama list 2>$null | Select-String -Pattern "nomic-embed-text")) {
    Write-Host-Color "⚠️ نموذج nomic-embed-text غير موجود. جاري التحميل..." "Yellow"
    ollama pull nomic-embed-text
    Write-Host-Color "✅ تم تحميل nomic-embed-text بنجاح." "Green"
} else {
    Write-Host-Color "✅ نموذج nomic-embed-text موجود." "Green"
}

if (-not (ollama list 2>$null | Select-String -Pattern "llama3.1")) {
    Write-Host-Color "⚠️ نموذج llama3.1 غير موجود. جاري التحميل..." "Yellow"
    ollama pull llama3.1
    Write-Host-Color "✅ تم تحميل llama3.1 بنجاح." "Green"
} else {
    Write-Host-Color "✅ نموذج llama3.1 موجود." "Green"
}

# ----------------------------------------------------------------------------
# 3. إعداد ملف .env
# ----------------------------------------------------------------------------
Write-Host-Color "
[3/5] ⚙️ إعداد ملف البيئة (.env)..." "Cyan"
if (-not (Test-Path ".\.env")) {
    Write-Host-Color "⚠️ ملف .env غير موجود. سيتم نسخه من .env.example." "Yellow"
    Copy-Item -Path ".\.env.example" -Destination ".\.env"
    Write-Host-Color "🛑 هام جداً: تم إنشاء ملف .env. يرجى فتحه الآن وتغيير كلمات المرور والمفاتيح السرية قبل المتابعة." "Red"
    Read-Host -Prompt "اضغط Enter بعد تعديل ملف .env للمتابعة..."
}
Write-Host-Color "✅ ملف .env موجود." "Green"

# ----------------------------------------------------------------------------
# 4. سحب أحدث الصور
# ----------------------------------------------------------------------------
Write-Host-Color "
[4/5] 📥 سحب أحدث صور Docker..." "Cyan"
docker-compose pull

# ----------------------------------------------------------------------------
# 5. بناء وتشغيل الحاويات
# ----------------------------------------------------------------------------
Write-Host-Color "
[5/5] 🚀 بناء وتشغيل الحاويات..." "Cyan"
docker-compose up -d --build --remove-orphans

# ----------------------------------------------------------------------------
# --- انتهى --- 
# ----------------------------------------------------------------------------
Write-Host-Color "

--- ✅ اكتمل الإعداد بنجاح! --- 
" "White"

Write-Host-Color "الخدمات الأساسية تعمل الآن:
" "White"
Write-Host-Color "- 💬 Open WebUI (الواجهة الرئيسية): http://localhost:3000" "Green"
Write-Host-Color "- 🤖 n8n (الأتمتة والنشر):        http://localhost:5678" "Green"
Write-Host-Color "- 💻 Code Server (بيئة التطوير):   http://localhost:8443" "Green"
Write-Host-Color "- 🧠 ChromaDB (ذاكرة القوانين):    http://localhost:8010" "Green"

Write-Host-Color "
ملاحظات هامة:
- عند تشغيل Open WebUI لأول مرة، أنشئ حساب المدير.
- كلمة مرور Code Server موجودة في ملف .env.
- ابدأ برفع الوثائق القانونية من تبويب 'Documents' في Open WebUI.
" "Yellow"
