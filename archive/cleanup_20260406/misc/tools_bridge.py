import os
import sys

def list_project_files():
    """عرض ملفات المشروع للمهندس صالح"""
    print("--- [SaleHSaaS3 AI Bridge] ---")
    print(f"Current Directory: {os.getcwd()}")
    print(f"Python Executable: {sys.executable}")
    
    files = os.listdir('.')
    print("\n[1] Workspace Files:")
    for f in files[:15]:
        print(f" - {f}")
    return files

def check_internet():
    """اختبار بسيط للاتصال بالإنترنت عبر Python"""
    print("\n[2] Internet Connectivity Test:")
    try:
        import urllib.request
        with urllib.request.urlopen('https://github.com', timeout=5) as response:
            print(f"Status: {response.status} (Connection Successful)")
    except Exception as e:
        print(f"Internet Error: {e}")

if __name__ == "__main__":
    list_project_files()
    check_internet()

if __name__ == "__main__":
    print("EVO Helper Tools Ready for Engineer Saleh.")
