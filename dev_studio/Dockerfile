# SaleH Dev Studio - Dockerfile
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

# 3. تثبيت امتدادات VS Code
RUN code-server --install-extension ms-python.python \
 && code-server --install-extension ms-toolsai.jupyter \
 && code-server --install-extension esbenp.prettier-vscode \
 && code-server --install-extension dbaeumer.vscode-eslint

# 4. كتابة entrypoint مباشرة داخل الصورة (بدون COPY لتجنب مشكلة CRLF على Windows)
RUN printf '#!/bin/sh\nmkdir -p /home/coder/.config/code-server\nprintf "bind-addr: 0.0.0.0:8080\\nauth: password\\npassword: %%s\\ncert: false\\n" "$PASSWORD" > /home/coder/.config/code-server/config.yaml\nexec code-server --config /home/coder/.config/code-server/config.yaml /home/coder/SaleHSaaS3\n' > /usr/local/bin/entrypoint-dev.sh \
 && chmod +x /usr/local/bin/entrypoint-dev.sh

USER coder
ENTRYPOINT ["/usr/local/bin/entrypoint-dev.sh"]
