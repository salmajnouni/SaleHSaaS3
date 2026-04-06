"""Activate n8n workflow via REST API with session auth."""
import requests
import sys

BASE = "http://localhost:5678"
WF_ID = "CwCounclWbhk001"
API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2MzM4ZjBkYi1kOTIwLTRmMGItOTE3Yi0xZjg3MDAyMDdiNjgiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwianRpIjoiYzJmNWJmYmYtZTNhMi00ZjI0LWJhZDYtYzhmNGNhNDUwMmY5IiwiaWF0IjoxNzcyNDkwMTYzLCJleHAiOjE3NzUwNzcyMDB9.r8pFpuSpx86VH5Gx9Z8WpKpLwdLKxsLrrdhLjoiG6LU"

# Try public API with API key
headers = {"X-N8N-API-KEY": API_KEY}
print("Trying /api/v1/ with API key...")
get_resp = requests.get(f"{BASE}/api/v1/workflows/{WF_ID}", headers=headers)
print(f"GET: {get_resp.status_code} {get_resp.text[:200]}")

if get_resp.status_code == 200:
    activate_resp = requests.patch(f"{BASE}/api/v1/workflows/{WF_ID}", headers=headers, json={"active": True})
    print(f"PATCH: {activate_resp.status_code}")
    if activate_resp.status_code == 200:
        print(f"Active: {activate_resp.json().get('active')}")
    else:
        print(activate_resp.text[:300])
else:
    # Try session auth with manual cookie header
    print("\nTrying session auth with manual cookie...")
    s = requests.Session()
    login_resp = s.post(f"{BASE}/rest/login", json={
        "emailOrLdapLoginId": "salmajnouni@gmail.com",
        "password": "SalehSaaS2026!"
    })
    print(f"Login: {login_resp.status_code}")
    
    # Get the auth token
    token = s.cookies.get("n8n-auth")
    
    # Try with browser-like headers
    browser_headers = {
        "Cookie": f"n8n-auth={token}",
        "Content-Type": "application/json",
        "browser-id": "activate-script"
    }
    get2 = requests.get(f"{BASE}/rest/workflows/{WF_ID}", headers=browser_headers)
    print(f"GET with browser headers: {get2.status_code} {get2.text[:200]}")
    
    if get2.status_code == 200:
        # First deactivate then activate to force re-registration
        print("\nDeactivating first...")
        deact = requests.patch(f"{BASE}/rest/workflows/{WF_ID}", headers=browser_headers,
                              json={"active": False})
        print(f"Deactivate: {deact.status_code}")
        
        print("Activating...")
        act = requests.patch(f"{BASE}/rest/workflows/{WF_ID}", headers=browser_headers,
                            json={"active": True})
        print(f"Activate: {act.status_code}")
        if act.status_code == 200:
            d = act.json()
            print(f"Active: {d.get('data', {}).get('active')}")
        else:
            print(act.text[:500])
print(f"Activate: {activate_resp.status_code}")
if activate_resp.status_code != 200:
    print(activate_resp.text[:500])
else:
    data = activate_resp.json()
    print(f"Active: {data.get('data', {}).get('active', 'unknown')}")
