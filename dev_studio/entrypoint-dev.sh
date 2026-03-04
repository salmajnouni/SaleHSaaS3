#!/bin/sh
# كتابة كلمة المرور من متغير البيئة PASSWORD في config.yaml
mkdir -p /home/coder/.config/code-server
printf 'bind-addr: 0.0.0.0:8080\nauth: password\npassword: %s\ncert: false\n' "$PASSWORD" \
    > /home/coder/.config/code-server/config.yaml
# تشغيل code-server
exec code-server --config /home/coder/.config/code-server/config.yaml /home/coder/SaleHSaaS3
