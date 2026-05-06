@echo off
setlocal

set CLINE_PROXY_HOST=127.0.0.1
set CLINE_PROXY_PORT=4011
set OPENWEBUI_CHAT_URL=http://localhost:3000/api/chat/completions
set WEBUI_API_KEY=sk-YcJBteAjDLbMy5hh9rYlSMjui4PjhNLnafP7BkMbaPE

.venv\Scripts\python.exe cline_openwebui_proxy.py
