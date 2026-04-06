# judicial_ingest.py
import requests
import os
from bs4 import BeautifulSoup

def main():
    # استهداف رابط مباشر أكثر مرونة أو استخدام موقع بديل (مثل عيينة من نظام الإثبات)
    url = "https://laws.boe.gov.sa/BoeLaws/Laws/LawDetails/2529949d-3f5f-4d30-9b37-a9a400ed43d4/1"
    # سنحاول جلب نسخة الـ PDF أو الرابط المباشر للمحتوى الداخلي إذا فشل الـ HTML العادي
    
    print(f"[*] Fetching Legal Content from: {url}")
    
    # رأس طلب (Headers) لمحاكاة متصفح حقيقي وتفادي الحجب
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'ar-SA,ar;q=0.9,en-US;q=0.8,en;q=0.7',
    }
    
    try:
        # تجاوز مشكلة شهادات الـ SSL الشائعة في بعض الأنظمة
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        res = requests.get(url, timeout=20, verify=False, headers=headers)
        
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # استخراج العنوان
        title = soup.title.text.strip() if soup.title else "نظام الإثبات السعودي"
        
        # استخراج النص (أول 5000 حرف كعينة)
        content = soup.get_text()
        
        # تنظيف النص قليلاً
        clean_text = "\n".join([line.strip() for line in content.splitlines() if line.strip()])
        
        # حفظ في مجلد docs
        if not os.path.exists('docs'):
            os.makedirs('docs')
            
        file_path = 'docs/judicial_system.txt'
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"المصدر: {url}\n")
            f.write(f"العنوان: {title}\n")
            f.write("="*30 + "\n\n")
            f.write(clean_text[:10000]) # حفظ أول 10 آلاف حرف
            
        print(f"[+] Success! Legal document saved to: {file_path}")
        print(f"[+] Sample Length: {len(clean_text)} characters.")
        
    except Exception as e:
        print(f"[!] Error fetching data: {str(e)}")

if __name__ == "__main__":
    main()
