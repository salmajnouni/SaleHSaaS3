#!/usr/bin/env python3
"""
n8n Workflows - Usage Examples
أمثلة بسيطة لاستخدام الـ workflows الموجودة

سجل هنا جميع الـ workflows الفعلية والـ agents يقدر يستخدمها
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.n8n.n8n_api import trigger_webhook, CouncilWorkflow, check_n8n
import json

def print_result(title: str, result: dict):
    """Pretty print result"""
    print(f"\n{'='*60}")
    print(f"✅ {title}" if result.get("success") else f"❌ {title}")
    print(f"{'='*60}")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print()

def example_1_council_request():
    """Example 1: Submit a council study request"""
    print("\n" + "="*60)
    print("EXAMPLE 1: Council Study Request")
    print("="*60)
    
    result = CouncilWorkflow.submit_request(
        topic="Should we implement blockchain for contract management?",
        study_type="technical",
        requester="صالح المجنوني",
        priority="high"
    )
    
    print_result("Council Request Submitted", result)

def example_2_direct_webhook():
    """Example 2: Trigger webhook directly"""
    print("\n" + "="*60)
    print("EXAMPLE 2: Direct Webhook Trigger")
    print("="*60)
    
    result = trigger_webhook("council-intake", {
        "topic": "Legal review needed",
        "study_type": "legal",
        "requested_by": "محمد علي",
        "source": "direct_api"
    })
    
    print_result("Webhook Triggered", result)

def example_3_check_health():
    """Example 3: Check n8n health"""
    print("\n" + "="*60)
    print("EXAMPLE 3: Check n8n Health")
    print("="*60)
    
    result = check_n8n()
    print_result("Health Check", result)

def example_4_batch_requests():
    """Example 4: Batch submit multiple requests"""
    print("\n" + "="*60)
    print("EXAMPLE 4: Batch Council Requests")
    print("="*60)
    
    requests_list = [
        {
            "topic": "Financial policy review",
            "study_type": "financial",
            "requester": "أحمد الثميري"
        },
        {
            "topic": "Cybersecurity assessment",
            "study_type": "cyber",
            "requester": "علي الدوسري"
        },
        {
            "topic": "HR policy update",
            "study_type": "legal",
            "requester": "فاطمة الأحمد"
        }
    ]
    
    for req in requests_list:
        print(f"\n📤 Submitting: {req['topic']} ({req['study_type']})")
        result = CouncilWorkflow.submit_request(**req, priority="normal")
        status = "✅" if result.get("success") else "❌"
        print(f"{status} Result: {result.get('status_code', 'N/A')}")

if __name__ == "__main__":
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║     n8n Workflows - Universal Tool for All Agents         ║
    ║     الـ n8n - أداة متاحة لجميع الـ agents                 ║
    ╚════════════════════════════════════════════════════════════╝
    """)
    
    # Check if n8n is running
    health = check_n8n()
    if not health.get("healthy"):
        print(f"❌ n8n is not responding: {health}")
        sys.exit(1)
    
    print(f"✅ n8n is running at: {health['url']}\n")
    
    # Run examples
    choice = input("""
    Choose an example:
    1. Council Request
    2. Direct Webhook
    3. Health Check
    4. Batch Requests
    5. All Examples
    
    Enter choice (1-5): """).strip()
    
    if choice == "1" or choice == "5":
        example_1_council_request()
    
    if choice == "2" or choice == "5":
        example_2_direct_webhook()
    
    if choice == "3" or choice == "5":
        example_3_check_health()
    
    if choice == "4" or choice == "5":
        example_4_batch_requests()
    
    print("\n" + "="*60)
    print("Examples completed!")
    print("="*60)
