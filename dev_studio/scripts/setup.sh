#!/bin/bash
# ------------------------------------------------------------------
# SaleH Dev Studio - سكريبت الإعداد التلقائي
# ------------------------------------------------------------------

# --- الألوان --- 
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# --- المتغيرات ---
COMPOSE_FILE_PATH="../dev_studio/docker-compose.dev-studio.yml"
ENV_FILE_PATH="../.env"
NETWORK_NAME="salehsaas_salehsaas_net"

# --- الدوال ---

# دالة لطباعة الرسائل
function print_message() {
  echo -e "${GREEN}▶ $1${NC}"
}

# دالة لطباعة التحذيرات
function print_warning() {
  echo -e "${YELLOW}⚠ $1${NC}"
}

# دالة للتحقق من وجود ملف .env
function check_env_file() {
  print_message "التحقق من وجود ملف .env..."
  if [ ! -f "$ENV_FILE_PATH" ]; then
    print_warning "ملف .env غير موجود. سيتم إنشاؤه بقيم افتراضية."
    echo "CODE_SERVER_PASSWORD=saleh_dev_2026" > "$ENV_FILE_PATH"
    echo "DEV_STUDIO_PORT=8080" >> "$ENV_FILE_PATH"
    print_message "تم إنشاء ملف .env بنجاح."
  else
    print_message "ملف .env موجود."
  fi
}

# دالة للتحقق من وجود شبكة Docker
function check_docker_network() {
  print_message "التحقق من وجود شبكة Docker ($NETWORK_NAME)..."
  if ! docker network ls | grep -q "$NETWORK_NAME"; then
    print_warning "شبكة Docker ($NETWORK_NAME) غير موجودة. سيتم محاولة إنشائها..."
    docker network create "$NETWORK_NAME"
    print_message "تم إنشاء شبكة Docker بنجاح."
  else
    print_message "شبكة Docker موجودة."
  fi
}

# --- التنفيذ ---

print_message "🚀 بدء إعداد SaleH Dev Studio..."

# الانتقال إلى مجلد السكريبت
cd "$(dirname "$0")"

check_env_file
check_docker_network

print_message "تشغيل حاوية Dev Studio..."
docker compose -f "$COMPOSE_FILE_PATH" up -d

print_message "✅ اكتمل الإعداد بنجاح!"
print_message "يمكنك الآن الوصول إلى Dev Studio عبر: http://localhost:$(grep DEV_STUDIO_PORT $ENV_FILE_PATH | cut -d '=' -f2)"
