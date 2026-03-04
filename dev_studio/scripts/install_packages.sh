#!/bin/bash
# ═══════════════════════════════════════════════════════════════════
# SaleH Dev Studio - تثبيت جميع الحزم اللازمة للتطوير
# شغّل هذا السكريبت مرة واحدة من Terminal داخل VS Code
# ═══════════════════════════════════════════════════════════════════

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}══════════════════════════════════════════${NC}"
echo -e "${BLUE}   SaleH Dev Studio - تثبيت الحزم الشاملة${NC}"
echo -e "${BLUE}══════════════════════════════════════════${NC}"

# ── 1. تحديث النظام ───────────────────────────────────────────────
echo -e "\n${YELLOW}▶ تحديث النظام...${NC}"
sudo apt-get update -qq

# ── 2. أدوات النظام الأساسية ──────────────────────────────────────
echo -e "\n${YELLOW}▶ تثبيت أدوات النظام...${NC}"
sudo apt-get install -y -qq \
    curl wget git unzip zip \
    build-essential \
    python3 python3-pip python3-venv \
    nodejs npm \
    jq \
    docker.io docker-compose-plugin

# ── 3. حزم Python للـ RAG والذكاء الاصطناعي ──────────────────────
echo -e "\n${YELLOW}▶ تثبيت حزم Python (RAG + AI)...${NC}"
pip3 install --quiet --upgrade pip

pip3 install --quiet \
    # ── RAG والبحث الدلالي ──
    chromadb \
    langchain \
    langchain-community \
    langchain-ollama \
    langchain-chroma \
    sentence-transformers \
    faiss-cpu \
    # ── معالجة الوثائق ──
    pypdf \
    python-docx \
    openpyxl \
    python-pptx \
    beautifulsoup4 \
    lxml \
    # ── واجهات برمجية ──
    fastapi \
    uvicorn[standard] \
    httpx \
    requests \
    aiohttp \
    pydantic \
    python-multipart \
    python-dotenv \
    # ── قواعد البيانات ──
    sqlalchemy \
    alembic \
    psycopg2-binary \
    redis \
    # ── تحليل البيانات ──
    pandas \
    numpy \
    matplotlib \
    # ── أدوات التطوير ──
    black \
    pytest \
    pytest-asyncio \
    ipython

echo -e "${GREEN}  ✅ حزم Python مثبتة${NC}"

# ── 4. حزم Node.js للـ Frontend ───────────────────────────────────
echo -e "\n${YELLOW}▶ تثبيت حزم Node.js...${NC}"
sudo npm install -g --quiet \
    pnpm \
    yarn \
    typescript \
    ts-node \
    nodemon \
    @vitejs/create-app

echo -e "${GREEN}  ✅ حزم Node.js مثبتة${NC}"

# ── 5. امتدادات VS Code ────────────────────────────────────────────
echo -e "\n${YELLOW}▶ تثبيت امتدادات VS Code...${NC}"

code-server --install-extension ms-python.python --force 2>/dev/null
code-server --install-extension ms-python.vscode-pylance --force 2>/dev/null
code-server --install-extension ms-python.black-formatter --force 2>/dev/null
code-server --install-extension eamodio.gitlens --force 2>/dev/null
code-server --install-extension ms-azuretools.vscode-docker --force 2>/dev/null
code-server --install-extension esbenp.prettier-vscode --force 2>/dev/null
code-server --install-extension bradlc.vscode-tailwindcss --force 2>/dev/null
code-server --install-extension PKief.material-icon-theme --force 2>/dev/null
code-server --install-extension Continue.continue --force 2>/dev/null
code-server --install-extension dbaeumer.vscode-eslint --force 2>/dev/null
code-server --install-extension formulahendry.auto-rename-tag --force 2>/dev/null

echo -e "${GREEN}  ✅ امتدادات VS Code مثبتة${NC}"

# ── 6. التحقق النهائي ─────────────────────────────────────────────
echo -e "\n${BLUE}══════════════════════════════════════════${NC}"
echo -e "${GREEN}   ✅ اكتمل التثبيت بنجاح!${NC}"
echo -e "${BLUE}══════════════════════════════════════════${NC}"
echo ""
echo -e "  Python:     $(python3 --version)"
echo -e "  pip:        $(pip3 --version | cut -d' ' -f1-2)"
echo -e "  Node.js:    $(node --version)"
echo -e "  npm:        $(npm --version)"
echo -e "  pnpm:       $(pnpm --version 2>/dev/null || echo 'تحقق يدوياً')"
echo ""
echo -e "${YELLOW}  الآن يمكنك بناء أي تطبيق جديد! 🚀${NC}"
