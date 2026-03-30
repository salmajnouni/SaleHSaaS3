# استخدام نسخة Debian من n8n
FROM n8nio/n8n:latest-debian

USER root

# إصلاح مستودعات Debian Buster المنتهية (EOL)
RUN sed -i 's/deb.debian.org/archive.debian.org/g' /etc/apt/sources.list && \
    sed -i 's/security.debian.org/archive.debian.org/g' /etc/apt/sources.list && \
    sed -i '/buster-updates/d' /etc/apt/sources.list

# تثبيت بايثون والمكتبات
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-pandas \
    python3-requests \
    python3-numpy \
    && rm -rf /var/lib/apt/lists/*

RUN ln -sf /usr/bin/python3 /usr/bin/python

# تشغيل الحاوية بصلاحيات root لتفادي خطأ "operation not permitted"
USER root

ENTRYPOINT ["tini", "--", "/docker-entrypoint.sh"]
