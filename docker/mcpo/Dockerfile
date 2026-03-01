FROM ghcr.io/open-webui/mcpo:main

# تثبيت مكتبة MCP الرسمية وmcpo
RUN pip install --no-cache-dir mcp requests

# نسخ الأدوات
COPY tools/mcp/ /tools/mcp/
