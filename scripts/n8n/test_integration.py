#!/usr/bin/env python3
"""
Quick Integration Test - اختبار التكامل السريع
تحقق من أن الـ workflows الموجودة تعمل بشكل صحيح
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.n8n.n8n_api import trigger_webhook, CouncilWorkflow, check_n8n
import json

def main():
    print("\n" + "="*70)
    print("n8n Integration Test - اختبار التكامل مع الـ Workflows الموجودة")
    print("="*70)
    
    # 1. Health Check
    print("\n[1] Checking n8n health...")
    health = check_n8n()
    
    if not health.get('healthy'):
        print(f"    ❌ n8n not responding: {health}")
        return False
    
    print(f"    ✅ n8n is healthy at {health['url']}")
    
    # 2. Test Council Webhook
    print("\n[2] Testing Council Intake Webhook...")
    result = trigger_webhook("council-intake", {
        "topic": "اختبار تكامل النظام - System Integration Test",
        "study_type": "technical",
        "requested_by": "Automated Tester",
        "source": "n8n_integration_test",
        "priority": "normal"
    })
    
    print(f"    Status: {result.get('status_code')}")
    print(f"    Success: {result.get('success')}")
    
    if result.get('response'):
        print(f"    Response: {json.dumps(result['response'], indent=6)}")
    
    # 3. Test Council Convenience Function
    print("\n[3] Testing CouncilWorkflow Class...")
    result2 = CouncilWorkflow.submit_request(
        topic="اختبار الـ class - Class Test",
        study_type="legal",
        requester="Test Admin",
        priority="high"
    )
    
    print(f"    Success: {result2.get('success')}")
    print(f"    Status Code: {result2.get('status_code')}")
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    test_results = [
        ("n8n Health", health.get('healthy')),
        ("Webhook Trigger", result.get('success')),
        ("Council Function", result2.get('success')),
    ]
    
    for test_name, passed in test_results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} : {test_name}")
    
    all_passed = all(passed for _, passed in test_results)
    
    print("\n" + "="*70)
    if all_passed:
        print("✅ All tests passed! n8n integration is working correctly.")
        print("   You can now use n8n from any agent or model.")
        print("="*70)
        return True
    else:
        print("❌ Some tests failed. Check the logs above.")
        print("="*70)
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
