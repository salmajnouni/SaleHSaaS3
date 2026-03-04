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
RUN code-server --install-extension ms-python.python \
 && code-server --install-extension ms-toolsai.jupyter \
 && code-server --install-extension esbenp.prettier-vscode \
 && code-server --install-extension dbaeumer.vscode-eslint
# 4. تثبيت Continue (مساعد AI) من Open VSX - المصدر الرسمي لـ code-server
RUN CONTINUE_VERSION="1.3.32" && \
    curl -fL "https://open-vsx.org/api/Continue/continue/linux-x64/${CONTINUE_VERSION}/file/Continue.continue-${CONTINUE_VERSION}@linux-x64.vsix" \
    -o /tmp/continue.vsix && \
    code-server --install-extension /tmp/continue.vsix && \
    rm /tmp/continue.vsix
# 5. نسخ إعداد Continue الجاهز
COPY config/continue-config.json /home/coder/.continue/config.json
RUN chown -R coder:coder /home/coder/.continue
# 6. حذف config.yaml القديم لإجبار code-server على قراءة PASSWORD من البيئة
RUN rm -f /home/coder/.config/code-server/config.yaml
USER coder
# تشغيل code-server مع قراءة كلمة المرور من متغير البيئة PASSWORD
CMD ["sh", "-c", "exec code-server --bind-addr 0.0.0.0:8080 --auth password --disable-telemetry /home/coder/SaleHSaaS3"]
