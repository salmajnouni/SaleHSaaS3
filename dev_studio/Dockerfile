# SaleH Dev Studio - Dockerfile
# يبني صورة تحتوي على كل ما يلزم لبيئة تطوير متكاملة

FROM codercom/code-server:latest

# 1. تثبيت Python والحزم الأساسية
RUN sudo apt-get update && \
    sudo apt-get install -y --no-install-recommends \
        python3-pip \
        python3-venv \
        git \
    && sudo rm -rf /var/lib/apt/lists/*

# 2. تثبيت حزم Python لـ RAG والذكاء الاصطناعي
RUN sudo python3 -m pip install --no-cache-dir --break-system-packages \
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

# 3. تثبيت امتدادات VS Code الأساسية
RUN code-server --install-extension ms-python.python && \
    code-server --install-extension ms-python.vscode-pylance && \
    code-server --install-extension ms-toolsai.jupyter && \
    code-server --install-extension esbenp.prettier-vscode && \
    code-server --install-extension dbaeumer.vscode-eslint && \
    code-server --install-extension continue.continue
