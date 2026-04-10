FROM python:3.11-slim

WORKDIR /app

# تثبيت Docker CLI للتحكم في الحاويات
RUN apt-get update && apt-get install -y \
    curl \
    docker.io \
    && rm -rf /var/lib/apt/lists/*

# تثبيت المكتبات
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# نسخ السكريبت
COPY agent.py .

# إنشاء مجلد السجلات
RUN mkdir -p /app/logs

CMD ["python", "-u", "agent.py"]
