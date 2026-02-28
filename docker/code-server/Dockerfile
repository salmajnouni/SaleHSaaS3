FROM codercom/code-server:latest

USER root

# تثبيت Continue.dev من Open VSX (بدون GitHub Marketplace)
RUN code-server --install-extension Continue.continue --force

# إنشاء مجلد إعدادات Continue
RUN mkdir -p /home/coder/.continue && chown -R coder:coder /home/coder/.continue

# إنشاء إعدادات VS Code لإيقاف GitHub Copilot نهائياً
RUN mkdir -p /home/coder/.local/share/code-server/User
COPY settings.json /home/coder/.local/share/code-server/User/settings.json

# نسخ إعداد Continue.dev
COPY continue-config.json /home/coder/.continue/config.json

RUN chown -R coder:coder /home/coder/.local /home/coder/.continue

USER coder
