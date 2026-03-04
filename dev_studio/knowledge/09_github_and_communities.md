# GitHub ومجتمعات المطورين — الدليل الشامل

## GitHub

### ما هو GitHub؟
منصة استضافة الكود الأكثر شيوعاً في العالم، تعتمد على Git لإدارة الإصدارات والتعاون. في مشروع SaleHSaaS يُستخدم كمستودع رئيسي للكود.

- **المستودع الرئيسي:** https://github.com/salmajnouni/SaleHSaaS3
- **المالك:** salmajnouni (صالح المجنوني)

---

## GitHub CLI (gh) — الأوامر الأساسية

### المصادقة
```bash
gh auth login          # تسجيل الدخول
gh auth status         # التحقق من حالة الدخول
```

### إدارة المستودعات
```bash
gh repo clone salmajnouni/SaleHSaaS3    # استنساخ المستودع
gh repo view                             # عرض معلومات المستودع
gh repo list salmajnouni                 # قائمة المستودعات
```

### إدارة الملفات عبر API
```bash
# قراءة ملف
gh api repos/salmajnouni/SaleHSaaS3/contents/README.md --jq '.content' | base64 -d

# رفع/تحديث ملف
CONTENT=$(base64 -w 0 myfile.txt)
SHA=$(gh api repos/salmajnouni/SaleHSaaS3/contents/path/to/file --jq '.sha' 2>/dev/null || echo "")
gh api repos/salmajnouni/SaleHSaaS3/contents/path/to/file \
  -X PUT \
  -f "message=commit message" \
  -f "content=$CONTENT" \
  -f "sha=$SHA"

# حذف ملف
gh api repos/salmajnouni/SaleHSaaS3/contents/path/to/file \
  -X DELETE \
  -f "message=delete file" \
  -f "sha=$SHA"
```

### Issues و Pull Requests
```bash
gh issue list                    # قائمة الـ Issues
gh issue create --title "..." --body "..."
gh pr list                       # قائمة الـ PRs
gh pr create --title "..." --body "..."
```

### GitHub Actions
```bash
gh workflow list                 # قائمة الـ Workflows
gh workflow run workflow_name    # تشغيل workflow يدوياً
gh run list                      # قائمة التشغيلات
```

---

## Git — الأوامر الأساسية

```bash
# الإعداد الأولي
git config --global user.name "صالح المجنوني"
git config --global user.email "email@example.com"

# العمل اليومي
git status                       # حالة الملفات
git add .                        # إضافة كل التغييرات
git add filename                 # إضافة ملف محدد
git commit -m "رسالة الـ commit"
git push origin main             # رفع إلى GitHub
git pull                         # سحب آخر التغييرات

# الفروع (Branches)
git branch                       # قائمة الفروع
git checkout -b feature/new      # إنشاء فرع جديد
git merge feature/new            # دمج فرع
git branch -d feature/new        # حذف فرع

# التاريخ
git log --oneline                # سجل الـ commits
git diff                         # الفرق بين الملفات
git stash                        # حفظ التغييرات مؤقتاً
git stash pop                    # استعادة التغييرات
```

---

## GitHub في سياق SaleHSaaS

### هيكل الفروع
- **main** — الفرع الرئيسي (الإنتاج)
- يُفضّل إنشاء فروع للميزات الجديدة

### ملفات مهمة في المستودع
```
.gitignore          ← يستثني .env والملفات الحساسة
.env.example        ← نموذج متغيرات البيئة (آمن للرفع)
docker-compose.yml  ← تشغيل كل الخدمات
ARCHITECTURE.md     ← المخطط المعماري
CHANGELOG.md        ← سجل التغييرات
INSTALL_GUIDE.md    ← دليل التثبيت
```

### ملفات لا تُرفع أبداً
```
.env                ← كلمات مرور وأسرار
*.pem               ← شهادات SSL
node_modules/       ← حزم Node.js
__pycache__/        ← ملفات Python المُجمَّعة
*.log               ← ملفات السجلات
```

---

## مجتمعات المطورين الرئيسية

### 1. GitHub Community
- **الرابط:** https://github.com/community
- **المنتدى:** https://github.com/orgs/community/discussions
- **الاستخدام:** أسئلة عن GitHub Actions، API، وأفضل الممارسات

### 2. Stack Overflow
- **الرابط:** https://stackoverflow.com
- **الوسوم المهمة:** `n8n`, `docker`, `python`, `openai`, `langchain`
- **الاستخدام:** حل مشاكل برمجية محددة

### 3. Reddit
- **r/selfhosted** — استضافة التطبيقات محلياً
- **r/LocalLLaMA** — نماذج اللغة المحلية وOllama
- **r/n8n** — مجتمع n8n
- **r/docker** — Docker وDocker Compose
- **r/OpenWebUI** — مجتمع OpenWebUI

### 4. Discord Servers
| الخادم | الرابط | الموضوع |
|--------|--------|---------|
| n8n | https://discord.gg/n8n | أتمتة سير العمل |
| OpenWebUI | https://discord.gg/5rJgQTnV4s | واجهة LLM |
| Ollama | https://discord.gg/ollama | نماذج محلية |
| LangChain | https://discord.gg/langchain | RAG والوكلاء |
| Hugging Face | https://discord.gg/huggingface | نماذج AI |

### 5. منتديات المشاريع المفتوحة
- **n8n Community:** https://community.n8n.io
- **Ollama GitHub Discussions:** https://github.com/ollama/ollama/discussions
- **OpenWebUI GitHub:** https://github.com/open-webui/open-webui/discussions
- **ChromaDB Discord:** https://discord.gg/chromadb

### 6. مصادر التعلم
- **n8n Blog:** https://blog.n8n.io — دروس وحالات استخدام
- **n8n Templates:** https://n8n.io/workflows — 1000+ قالب جاهز
- **Hugging Face:** https://huggingface.co — نماذج وأوراق بحثية
- **Papers With Code:** https://paperswithcode.com — أحدث الأبحاث
- **Dev.to:** https://dev.to — مقالات تقنية

---

## GitHub Actions في SaleHSaaS (مستقبلاً)

يمكن إضافة GitHub Actions لـ:
```yaml
# .github/workflows/deploy.yml
name: Deploy SaleHSaaS
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: self-hosted  # على جهازك المحلي
    steps:
      - uses: actions/checkout@v3
      - name: Pull and restart
        run: |
          docker-compose pull
          docker-compose up -d
```

---

## نصائح GitHub للمشروع

1. **استخدم Releases** لتوثيق الإصدارات الكبيرة
2. **أضف Labels للـ Issues** لتنظيم المهام (bug, enhancement, documentation)
3. **استخدم Projects** كلوحة Kanban لتتبع التطوير
4. **فعّل Dependabot** لتحديث التبعيات تلقائياً
5. **أضف README بالعربية** لتوثيق المشروع بشكل احترافي
6. **استخدم .gitignore** لحماية الملفات الحساسة دائماً
