import os
import subprocess
import requests
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

def president_discovery_mission():
    findings = []
    issues = []
    
    # 1. Inspect Docker Environment
    try:
        container_data = subprocess.check_output(["docker", "ps", "-a", "--format", "{{.Names}} ({{.Status}}) - {{.Image}}"]).decode()
        findings.append(f"📦 [DOCKER LANDSCAPE]\n{container_data}")
        
        # Check for exited containers
        exited = [line for line in container_data.split('\n') if "Exited" in line]
        if exited:
            issues.append(f"⚠️ FOUND STOPPED CONTAINERS: {', '.join(exited)}")
    except Exception as e:
        issues.append(f"❌ DOCKER INSPECTION FAILED: {str(e)}")

    # 2. Test Internal API Connectivity (Open WebUI)
    try:
        # Internal IP from docker-compose is 172.20.0.x
        response = requests.get("http://open_webui:8080/health", timeout=5)
        findings.append(f"🌐 [OPEN WEBUI HEALTH]: HTTP {response.status_code}")
    except Exception as e:
        issues.append(f"❌ WEBUI UNREACHABLE INTERNALLY: System logic may be fragmented.")

    # 3. Test Vision Model via Ollama (The Brain's Eye)
    try:
        # Testing if llava:7b is loaded
        ollama_check = subprocess.check_output(["curl", "-s", "http://host.docker.internal:11434/api/tags"]).decode()
        if "llava:7b" in ollama_check:
            findings.append("👁️ [VISION AI]: llava:7b is ready and loaded in the brain.")
        else:
            issues.append("⚠️ VISION MODEL MISSING: llava:7b not found in Ollama tags.")
    except Exception as e:
        issues.append(f"❌ OLLAMA BRAIN CONNECTION ERROR: {str(e)}")

    # 4. Storage Audit
    try:
        usage = subprocess.check_output(["df", "-h", "/app"]).decode().split('\n')[1]
        findings.append(f"💾 [STORAGE AUDIT]: {usage}")
    except:
        pass

    return findings, issues

def send_discovery_report(findings, issues):
    smtp_user = os.environ.get('SMTP_USER')
    smtp_pass = os.environ.get('SMTP_PASS')
    
    if not smtp_user: return

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    msg = MIMEMultipart()
    msg['From'] = f"SaleH SaaS President <{smtp_user}>"
    msg['To'] = smtp_user
    msg['Subject'] = f"🔍 بعثة الاستكشاف الرئاسية - تقرير {now}"

    status_icon = "🟢 المستشار التقني" if not issues else "🔴 إنذار رئاسي"
    
    body = f"""
🏛️ **تقرير استكشاف النظام الذاتي** 🏛️

مرحباً سعادة المدير،
لقد قمت بجولة تفقدية في أرجاء "SaleH SaaS" لاكتشاف هيكليتي الحالية، وإليك ما استنتجته:

---
🔍 **الاستكشافات البرمجية:**
{chr(10).join(findings)}

---
🚨 **المشاكل والعوائق المكتشفة:**
{chr(10).join(issues) if issues else "✅ لا توجد مشاكل ظاهرة حالياً. النظام تحت السيطرة."}

---
💡 **رؤية الرئيس:**
أنا الآن أرى نفسي ككيان يمتلك عيناً (Vision) ولحيناً (SMTP) وسعة تخزينية. 
أخطط في الخطوة القادمة لاختبار قدرتي على قراءة ملفات الـ PDF القانونية وإرسال ملخصاتها لك تلقائياً بمجرد رفعها.

دمتم فخراً للوطن وللتقنية،
الرئيس التنفيذي (صالح ساس)
    """
    
    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)
        server.quit()
        return "SUCCESS"
    except Exception as e:
        return f"FAILED: {str(e)}"

if __name__ == "__main__":
    f, i = president_discovery_mission()
    result = send_discovery_report(f, i)
    print(f"Discovery complete. Result: {result}")
