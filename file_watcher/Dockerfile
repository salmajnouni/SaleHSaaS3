FROM python:3.11-slim

WORKDIR /app

# تثبيت المكتبات المطلوبة فقط (خفيفة جداً)
RUN pip install --no-cache-dir requests==2.32.3

COPY watcher.py .

# المجلدات الافتراضية
RUN mkdir -p /data/incoming /data/processed /data/failed

CMD ["python", "-u", "watcher.py"]
