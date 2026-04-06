import requests
import os

def download_saudi_laws():
    """تحميل الأنظمة السعودية مباشرة من GitHub لتجاوز الحماية."""
    print("🚀 جلب الأنظمة القانونية السعودية لبيئة EVO...")
    
    # قائمة ببعض القوانين الأساسية (روابط مستودعات موثقة أو نسخ Raw)
    laws = {
        "نظام العمل": "https://raw.githubusercontent.com/yazeed-bin-omar/saudi-laws/main/labor-law.txt",
        "نظام التجارة": "https://raw.githubusercontent.com/yazeed-bin-omar/saudi-laws/main/commercial-law.txt"
    }
    
    os.makedirs("data", exist_ok=True)
    
    for name, url in laws.items():
        try:
            print(f"📡 جاري تحميل {name}...")
            res = requests.get(url, timeout=10)
            if res.status_code == 200:
                filename = f"data/{name.replace(' ', '_')}.txt"
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(res.text)
                print(f"✅ تم تحميل وحفظ {name} في {filename}")
            else:
                # نص افتراضي في حال فشل الرابط لضمان عدم توقف EVO
                print(f"⚠️ الرابط غير متاح (404)، جاري إنشاء مسودة لـ {name}...")
                with open(f"data/{name.replace(' ', '_')}_draft.txt", "w", encoding="utf-8") as f:
                    f.write(f"مسودة {name} - تم إنشاؤها في بيئة EVO.\nالمادة 1: يهدف هذا النظام...")
        except Exception as e:
            print(f"❌ خطأ في {name}: {e}")

if __name__ == "__main__":
    download_saudi_laws()
