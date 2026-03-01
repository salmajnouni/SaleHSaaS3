FROM ghcr.io/open-webui/mcpo:main

# تثبيت المكتبات المطلوبة داخل venv الخاص بـ MCPO
# MCPO يستخدم /app/.venv وليس Python العادي
RUN /app/.venv/bin/pip install --no-cache-dir requests

# نسخ أدوات MCP
COPY tools/mcp/ /tools/mcp/
