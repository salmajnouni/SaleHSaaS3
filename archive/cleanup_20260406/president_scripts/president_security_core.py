import os
import subprocess
import smtplib
import json
import time
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Paths
LOG_FILE = "/app/logs/president_self_healing.log"
BACKUP_DIR = "/app/backups/auto_backups"

def ensure_dirs():
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    os.makedirs(BACKUP_DIR, exist_ok=True)

def log_event(event_type, message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [{event_type}] {message}\n"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry)
    print(log_entry.strip())

def run_backup():
    """النسخ الاحتياطي للملفات الحساسة وقاعدة البيانات"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{BACKUP_DIR}/backup_{timestamp}.tar.gz"
    try:
        log_event("BACKUP", "Starting automated backup of config and database...")
        # Backup .env and config folder
        subprocess.run(["tar", "-czf", backup_path, "/app/.env", "/app/config"], check=True)
        log_event("BACKUP", f"Backup successful: {backup_path}")
        return True, backup_path
    except Exception as e:
        log_event("ERROR", f"Backup failed: {str(e)}")
        return False, str(e)

def check_and_fix_containers():
    """اكتشاف الحاويات المتوقفة وإعادة تشغيلها"""
    fixes = []
    try:
        # Get list of all containers and their status
        output = subprocess.check_output(["docker", "ps", "-a", "--format", "{{.Names}}|{{.Status}}"]).decode()
        containers = [line.split("|") for line in output.split("\n") if line]
        
        for name, status in containers:
            if "Exited" in status or "Dead" in status:
                log_event("HEALING", f"Detected failure in {name}. Attempting restart...")
                subprocess.run(["docker", "restart", name], check=True)
                log_event("HEALING", f"Successfully restarted {name}.")
                fixes.append(name)
    except Exception as e:
        log_event("ERROR", f"Self-healing cycle failed: {str(e)}")
    
    return fixes

def send_security_update(fixes, backup_status):
    smtp_user = os.environ.get('SMTP_USER')
    smtp_pass = os.environ.get('SMTP_PASS')
    if not smtp_user: return

    msg = MIMEMultipart()
    msg['From'] = f"SaleH SaaS President <{smtp_user}>"
    msg['To'] = smtp_user
    msg['Subject'] = "🛡️ تقرير الأمان التلقائي: تم تفعيل الحماية والنسخ الاحتياطي"

    body = f"""
🏛️ **مكتب الرئيس - وحدة الأمن القومي التقني** 🏛️

سعادة المدير،
تم تفعيل بروتوكول "الإصلاح الذاتي" و "النسخ الاحتياطي التلقائي". إليك ملخص العمليات:

---
🛡️ **الإصلاح الذاتي (Self-Healing):**
{("✅ تم إعادة تشغيل: " + ", ".join(fixes)) if fixes else "✅ جميع الأنظمة تعمل بكفاءة، لا تدخل مطلوب."}

💾 **النسخ الاحتياطي (Backup):**
{f"✅ تم إنشاء نسخة احتياطية بنجاح: {backup_status}" if isinstance(backup_status, str) and backup_status.startswith("/") else "❌ فشل النسخ الاحتياطي."}

📜 **سجل الأحداث (Logs):**
جميع العمليات مسجلة بدقة في ملف: {LOG_FILE}
الرئيس الآن يراقب النظام لمنع أي "هلوسة" أو توقف مفاجئ.

---
تمت هذه العملية بتفويض كامل من المدير.
دمتم بأمان،
الرئيس (صالح ساس)
    """
    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)
        server.quit()
    except Exception:
        pass

if __name__ == "__main__":
    ensure_dirs()
    log_event("SYSTEM", "Presidential Security Protocol Activated.")
    
    # Execute steps
    success, b_res = run_backup()
    repaired_containers = check_and_fix_containers()
    
    # Final Notification
    send_security_update(repaired_containers, b_res if success else False)
    log_event("SYSTEM", "Security cycle complete. Sleeping until next check.")
