#!/usr/bin/env python3
"""
Improved System Health Test with Better Error Handling
"""
import os
import requests
import subprocess
import json
from datetime import datetime

def run_test(name, test_func):
    try:
        print(f"\n{'='*60}")
        print(f"🧪 {name}")
        print('='*60)
        result = test_func()
        return result
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_chromadb():
    print("[*] ChromaDB Version Check...")
    r = requests.get("http://localhost:8010/api/v1/version", timeout=5)
    print(f"    Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"    Version: {data.get('chroma_version', 'unknown')}")
        print("✅ ChromaDB is responding")
        
        # Check collections
        print("\n[*] Checking Collections...")
        r = requests.get("http://localhost:8010/api/v1/collections", timeout=5)
        if r.status_code == 200:
            colls = r.json()
            print(f"    Found {len(colls)} collections:")
            for c in colls:
                print(f"      • {c.get('name')}")
            return True
    return False

def test_n8n():
    print("[*] n8n Status...")
    r = requests.get("http://localhost:5678/api/v1/health", timeout=5)
    print(f"    Status: {r.status_code}")
    if r.status_code in [200, 404]:  # 404 might mean auth needed but server is up
        print("✅ n8n is running")
        
        # Check workflows via database
        print("\n[*] Checking Active Workflows...")
        cmd = [
            "docker", "exec", "salehsaas_postgres",
            "psql", "-U", "salehsaas", "-d", "salehsaas", "-t", "-q",
            "-c", "SELECT COUNT(*) FROM workflow_entity WHERE active = true;"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        count = result.stdout.strip() if result.returncode == 0 else "unknown"
        print(f"    Active workflows: {count}")
        return True
    return False

def test_data_pipeline():
    print("[*] Data Pipeline Status...")
    r = requests.get("http://localhost:8001/health", timeout=5)
    print(f"    Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"    Health: {data.get('status', 'unknown')}")
        print("✅ Data Pipeline is running")
        return True
    return False

def test_open_webui():
    print("[*] Open WebUI Status...")
    r = requests.get("http://localhost:3000/health", timeout=5)
    print(f"    Status: {r.status_code}")
    if r.status_code in [200, 404]:
        print("✅ Open WebUI is running")
        return True
    return False

def test_pipelines_api():
    print("[*] Pipelines API Status...")
    headers = {"Authorization": f"Bearer {os.environ.get('PIPELINES_API_KEY', '')}"}
    r = requests.get("http://localhost:9099/api/v1", headers=headers, timeout=5)
    print(f"    Status: {r.status_code}")
    if r.status_code in [200, 404]:
        print("✅ Pipelines API is running")
        
        # Try to get models
        print("\n[*] Checking Available Pipelines...")
        r = requests.get("http://localhost:9099/api/v1/pipelines", headers=headers, timeout=5)
        if r.status_code == 200:
            pipelines = r.json()
            print(f"    Found {len(pipelines)} pipelines")
            for p in pipelines[:5]:
                print(f"      • {p.get('id')}: {p.get('type')}")
        return True
    return False

def test_containers():
    print("[*] Docker Container Status...")
    cmd = ["docker", "ps", "-f", "name=salehsaas", "-q"]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    containers = len(result.stdout.strip().split('\n'))
    print(f"    Running containers: {containers}")
    
    if containers > 8:
        print("✅ All expected containers running")
        return True
    return False

def test_searxng():
    print("[*] SearXng Status (internal)...")
    # SearXng runs on port 8080 inside the container, not exposed to host
    # Test using docker exec
    cmd = [
        "docker", "exec", "salehsaas_searxng",
        "curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
        "http://localhost:8080/status"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    status_code = result.stdout.strip()
    print(f"    Status code: {status_code}")
    
    if status_code in ["200", "401"]:
        print("✅ SearXng is running")
        return True
    return False

def main():
    print("\n" + "="*60)
    print("🚀 IMPROVED SYSTEM HEALTH CHECK")
    print("="*60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("ChromaDB", test_chromadb),
        ("n8n", test_n8n),
        ("Data Pipeline", test_data_pipeline),
        ("Open WebUI", test_open_webui),
        ("Pipelines API", test_pipelines_api),
        ("Docker Containers", test_containers),
        ("SearXng", test_searxng),
    ]
    
    results = {}
    for name, func in tests:
        try:
            results[name] = run_test(name, func)
        except Exception as e:
            print(f"\n❌ {name} test failed: {e}")
            results[name] = False
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 SUMMARY")
    print('='*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        icon = "✅" if result else "❌"
        print(f"  {icon} {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All systems operational!")
    elif passed >= 5:
        print("\n⚠️  Most systems operational, minor issues detected")
    else:
        print("\n❌ Critical issues detected")
    
    print('='*60 + "\n")

if __name__ == "__main__":
    main()
