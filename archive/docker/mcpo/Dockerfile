# Historical artifact only: mcpo path is cancelled in this project.
# Do not treat this file as an active runtime component.
FROM ghcr.io/open-webui/mcpo:main

# /app/.venv هو venv مبني بـ uv - نثبت requests فيه مباشرة
RUN uv pip install --python /app/.venv/bin/python3 requests

# نسخ أدوات MCP
COPY tools/mcp/ /tools/mcp/
