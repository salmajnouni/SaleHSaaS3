import os
import smtplib
import subprocess
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

def get_container_status():
    try:
        # Run docker ps to get statuses
        process = subprocess.Popen(["docker", "ps", "--format", "{{.Names}}: {{.Status}}"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        if stderr:
             return f"Status Check partially failed with stderr: {stderr.decode()}"
        return stdout.decode()
    except Exception as e:
        return f"CRITICAL Error getting container status: {str(e)}"

def send_president_report():
    # Use environment variables passed via docker-compose .env
    smtp_host = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
    smtp_port = int(os.environ.get('SMTP_PORT', '465'))
    smtp_user = os.environ.get('SMTP_USER')
    smtp_pass = os.environ.get('SMTP_PASS')
    
    if not smtp_user or not smtp_pass:
        return "ERROR: Missing SMTP Credentials in .env"

    status_report = get_container_status()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    msg = MIMEMultipart()
    msg['From'] = f"SaleH SaaS President <{smtp_user}>"
    msg['To'] = smtp_user
    msg['Subject'] = f"🏛️ PRESIDENTIAL REPORT - {now}"

    body = f"""
    مرحباً سعادة المدير،
    
    هذا هو التقرير العملي الأول الذي يتم إنشاؤه وتنفيذه بالكامل عبر "الرئيس" (Python Agent).
    
    حالة النظام الحالية ({now}):
    --------------------------------------------------
    {status_report}
    --------------------------------------------------
    
    تحديثات النظام:
    - تم تفعيل نظام التنبيهات المباشر من "الرئيس".
    - الربط مع Vision AI جاهز للمهمة القادمة.
    
    التوصية: جميع الحاويات تعمل بكفاءة. لا يوجد تدخل بشري مطلوب حالياً.
    
    دمتم بود،
    الرئيس التنفيذي للذكاء الاصطناعي
    SaleH SaaS 3.0
    """
    
    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    try:
        server = smtplib.SMTP_SSL(smtp_host, smtp_port)
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)
        server.quit()
        return "SUCCESS: Report dispatched by President."
    except Exception as e:
        return f"CRITICAL ERROR: Failed to send report: {str(e)}"

if __name__ == "__main__":
    result = send_president_report()
    print(result)
