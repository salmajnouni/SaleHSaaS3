FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# إنشاء المجلدات الافتراضية
RUN mkdir -p /data/incoming /data/processed /data/failed /data/lora_queue static /app/glossary

# نسخ ملفات المعجم وطبقة الترجمة (موجودة داخل مجلد saleh_dashboard/glossary)
RUN if [ -d /app/glossary ] && [ "$(ls -A /app/glossary 2>/dev/null)" ]; then echo "Glossary files found"; else echo "No glossary files"; fi

EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--reload"]
