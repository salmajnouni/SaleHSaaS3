FROM ghcr.io/open-webui/mcpo:main

# تثبيت requests في venv الخاص بـ MCPO باستخدام uv
# uv هو مدير الحزم المستخدم في بناء الصورة الأصلية
RUN uv pip install --system requests

# نسخ أدوات MCP
COPY tools/mcp/ /tools/mcp/
