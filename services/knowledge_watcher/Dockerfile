FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir requests watchdog

COPY watcher.py .

CMD ["python", "-u", "watcher.py"]
