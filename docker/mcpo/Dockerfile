FROM ghcr.io/open-webui/mcpo:main

# تثبيت requests باستخدام uv (المدير الافتراضي في الصورة)
# أو pip مباشرة مع --break-system-packages
RUN pip install --break-system-packages --no-cache-dir requests || \
    uv pip install --system requests || \
    python3 -m pip install --no-cache-dir requests

# نسخ أدوات MCP
COPY tools/mcp/ /tools/mcp/
