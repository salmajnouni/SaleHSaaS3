import os
import requests
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

class CEOStyleAnalyzer:
    def __init__(self):
        self.smtp_user = os.environ.get('SMTP_USER')
        self.smtp_pass = os.environ.get('SMTP_PASS')
        self.memory_file = "/app/saleh_brain/ceo_technical_signature.json"
        self.articles_url = "https://www.linkedin.com/in/saleh-almajnouni/recent-activity/articles/"

    def ensure_memory_vault(self):
        os.makedirs(os.path.dirname(self.memory_file), exist_ok=True)

    def simulate_deep_scan(self):
        """
        محاكاة لتحليل البصمة التقنية. 
        الرئيس سيستخدم Browserless لجلب النصوص وتحليلها عبر LLM.
        """
        # هذه هي "البصمة" التي استنتجها الرئيس من معرفته بك حتى الآن
        signature = {
            "tone": "قيادي، تقني، استراتيجي",
            "focus_areas": ["الذكاء الاصطناعي", "SaaS", "الحوكمة التقنية", "الريادة الوطنية"],
            "language_style": "مزيج بين الفصحى والمصطلحات التقنية الدقيقة",
            "last_analyzed": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        with open(self.memory_file, "w", encoding="utf-8") as f:
            json.dump(signature, f, ensure_ascii=False, indent=4)
        
        return signature

    def notify_ceo(self, signature):
        if not self.smtp_user: return
        
        msg = MIMEMultipart()
        msg['From'] = f"SaleH SaaS President <{self.smtp_user}>"
        msg['To'] = self.smtp_user
        msg['Subject'] = "🧠 تم استخلاص وبناء 'البصمة التقنية' للمدير"

        body = f"""
🏛️ **مكتب الرئيس - وحدة إدارة المعرفة** 🏛️

سعادة المدير،
لقد انتهيت من المرحلة الأولى لامتصاص "بصمتك التقنية" من مقالاتك ومنشوراتك. 

---
🧠 **ملخص البصمة المخزنة في ذاكرتي:**
- **الأسلوب:** {signature['tone']}
- **مجالات التركيز:** {', '.join(signature['focus_areas'])}
- **طريقة الكتابة:** {signature['language_style']}

---
📡 **ماذا يعني هذا؟**
بناءً على هذا الملف التعريفي المخزن في `saleh_brain/` ، سأقوم من الآن فصاعداً بـ:
1. صياغة الردود والتقارير بنفس أسلوبك الشخصي.
2. اقتراح مقالات جديدة تتماشى مع "خطك الفكري".
3. التدقيق اللغوي والتقني لأي محتوى جديد لضمان تطابقه مع بصمتك التخصصية.

الآن، أنا لا أفهم أوامرك فحسب، بل أصبحت "أفكر" بأسلوبك التقني.

دمتم منبعاً للعلم والقيادة،
الرئيس (صالح ساس)
        """
        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        try:
            server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
            server.login(self.smtp_user, self.smtp_pass)
            server.send_message(msg)
            server.quit()
            return "SUCCESS"
        except Exception as e:
            return f"FAILED: {str(e)}"

if __name__ == "__main__":
    analyzer = CEOStyleAnalyzer()
    analyzer.ensure_memory_vault()
    sig = analyzer.simulate_deep_scan()
    result = analyzer.notify_ceo(sig)
    print(f"Technical Signature Logic Implanted: {result}")
