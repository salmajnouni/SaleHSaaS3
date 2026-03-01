FROM ghcr.io/open-webui/mcpo:main

# python3 في هذه الصورة هو /app/.venv/bin/python3
# نثبت requests مباشرة فيه
RUN /app/.venv/bin/python3 -m pip install --no-cache-dir requests

# نسخ أدوات MCP
COPY tools/mcp/ /tools/mcp/
