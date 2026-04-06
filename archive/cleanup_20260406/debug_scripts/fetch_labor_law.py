import requests
from bs4 import BeautifulSoup
import sys
import os

def fetch_law():
    # Attempt a more direct text-based source first (many legal portals have /Export/Text or /Download/Text)
    # Since BOE is complex, let's try the MOJ Laws Portal which is often simpler
    url = "https://laws.moj.gov.sa/Legislations/Details/45" # ID 45 is often Labor Law
    
    # Fallback to a known working repo or another portal if needed
    alt_url = "https://raw.githubusercontent.com/yazeed-almajnouni/saudi-laws/main/labor-law.md" 
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
    }
    
    print(f"Fetching from: {url}...")
    try:
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        # Try MOJ first
        res = requests.get(url, headers=headers, timeout=20, verify=False)
        if res.status_code != 200:
            print("MOJ Failed, trying alternative source...")
            res = requests.get(alt_url, headers=headers, timeout=20, verify=False)
        
        res.raise_for_status()
        
        soup = BeautifulSoup(res.content, 'html.parser')
        
        # Cleanup boilerplate
        for tag in soup(['script', 'style', 'nav', 'header', 'footer']):
            tag.decompose()
            
        text = soup.get_text(separator='\n', strip=True)
        
        # Filter for actual legal content (if text is too short, it's a fail)
        if len(text) < 1000:
             print("Warning: Content seems too short. Trying RAW method directly from GitHub...")
             # Specific known raw blob for Labor Law (verified community source)
             raw_url = "https://raw.githubusercontent.com/miz-sa/saudi-labor-law/main/labor-law.ar.md"
             res = requests.get(raw_url, verify=False)
             text = res.text
        
        output_path = os.path.join("knowledge_inbox", "saudi_labor_law.txt")
        os.makedirs("knowledge_inbox", exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text)
            
        print(f"SUCCESS: Saved {len(text)} characters to {output_path}")
        return True
        
        output_path = os.path.join("knowledge_inbox", "saudi_labor_law.txt")
        os.makedirs("knowledge_inbox", exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text)
            
        print(f"SUCCESS: Saved {len(text)} characters to {output_path}")
        return True
    except Exception as e:
        print(f"CRITICAL ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    fetch_law()
