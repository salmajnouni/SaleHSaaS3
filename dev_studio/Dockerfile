# SaleH Dev Studio - Dockerfile
# يبني صورة تحتوي على كل ما يلزم لبيئة تطوير متكاملة
FROM codercom/code-server:latest

USER root

# 1. تثبيت Python والأدوات الأساسية
RUN apt-get update -qq && \
    apt-get install -y -qq \
        python3 \
        python3-pip \
        python3-dev \
        build-essential \
        curl \
        git \
    && rm -rf /var/lib/apt/lists/*

# 2. تثبيت حزم Python لـ RAG والذكاء الاصطناعي
RUN pip3 install --no-cache-dir --break-system-packages \
    chromadb \
    langchain \
    langchain-community \
    langchain-ollama \
    langchain-chroma \
    sentence-transformers \
    fastapi \
    uvicorn \
    httpx \
    requests \
    pydantic \
    python-dotenv \
    python-multipart \
    pypdf \
    python-docx \
    openpyxl \
    sqlalchemy \
    redis \
    pandas \
    numpy \
    rich

# 3. تثبيت امتدادات VS Code المتوافقة مع code-server فقط
# ms-python.vscode-pylance حصري لـ VS Code الرسمي ولا يعمل مع code-server
RUN code-server --install-extension ms-python.python \
 && code-server --install-extension ms-toolsai.jupyter \
 && code-server --install-extension esbenp.prettier-vscode \
 && code-server --install-extension dbaeumer.vscode-eslint

USER coder
