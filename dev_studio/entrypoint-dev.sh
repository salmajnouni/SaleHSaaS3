#!/bin/bash
set -e
# كتابة كلمة المرور من متغير البيئة PASSWORD في config.yaml
mkdir -p /home/coder/.config/code-server
cat > /home/coder/.config/code-server/config.yaml << YAML
bind-addr: 0.0.0.0:8080
auth: password
password: ${PASSWORD}
cert: false
YAML
# تشغيل code-server
exec code-server --config /home/coder/.config/code-server/config.yaml /home/coder/SaleHSaaS3
