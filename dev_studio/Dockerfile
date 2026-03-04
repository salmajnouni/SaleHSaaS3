FROM codercom/code-server:latest

USER root

# تثبيت Python وpip وأدوات البناء
RUN apt-get update -qq && \
    apt-get install -y -qq \
        python3 \
        python3-pip \
        python3-venv \
        python3-dev \
        build-essential \
        curl \
        git \
    && rm -rf /var/lib/apt/lists/*

# تثبيت جميع حزم Python المطلوبة لـ RAG والذكاء الاصطناعي
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

# تثبيت امتدادات VS Code
RUN code-server --install-extension ms-python.python --force && \
    code-server --install-extension ms-python.vscode-pylance --force && \
    code-server --install-extension eamodio.gitlens --force && \
    code-server --install-extension esbenp.prettier-vscode --force && \
    code-server --install-extension ms-azuretools.vscode-docker --force || true

USER coder

EXPOSE 8080
