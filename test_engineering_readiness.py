#!/usr/bin/env python3
"""
Quick Testing Script for Engineering Services
سكريبت اختبار سريع لخدمات المكاتب الهندسية
"""
import requests
import json
from datetime import datetime

# Test Configuration
OPEN_WEBUI_URL = "http://localhost:3000"
CHROMADB_URL = "http://localhost:8010"
DATA_PIPELINE_URL = "http://localhost:8001"

# Engineering-specific test queries
HVAC_QUESTIONS = [
    "ما متطلبات الحد الأدنى للتهوية في المباني المكتبية حسب SBC-501؟",
    "كيف يتم حساب حمل التكييف لمبنى إداري؟",
    "ما حدود سرعة الهواء الموصى بها في الدكت؟",
]

PLUMBING_QUESTIONS = [
    "كيف يتم حساب وحدات التصريف (DFU) في المباني السكنية؟",
    "ما اشتراطات أقطار مواسير الصرف الرئيسية؟",
    "ما متطلبات الضغط الثابت في شبكات السباكة؟",
]

FIRE_QUESTIONS = [
    "ما متطلبات نظام الإطفاء التلقائي حسب SBC-801؟",
    "كيف يتم حساب عدد مخارج الطوارئ المطلوبة؟",
    "ما معايير المقاومة النارية للمواد في المباني؟",
]

def test_chromadb():
    """Test ChromaDB connection and data availability"""
    print("\n" + "="*70)
    print("🔍 TEST 1: ChromaDB & Vector Data")
    print("="*70)
    
    try:
        # Get collections
        resp = requests.get(f"{CHROMADB_URL}/api/v1/collections", timeout=5)
        if resp.status_code == 200:
            collections = resp.json()
            print(f"✅ ChromaDB connected - Found {len(collections)} collections\n")
            
            for col in collections:
                print(f"   📚 {col['name']}")
                
                # Get count
                try:
                    count_resp = requests.get(
                        f"{CHROMADB_URL}/api/v1/collections/{col['id']}/count",
                        timeout=5
                    )
                    if count_resp.status_code == 200:
                        count = count_resp.json()
                        print(f"      └─ {count} vectors stored")
                except:
                    pass
            
            return True
        else:
            print(f"❌ ChromaDB error: {resp.status_code}")
            return False
    
    except Exception as e:
        print(f"❌ ChromaDB test failed: {e}")
        return False

def test_data_pipeline():
    """Test data pipeline service"""
    print("\n" + "="*70)
    print("⚙️  TEST 2: Data Pipeline Service")
    print("="*70)
    
    try:
        resp = requests.get(f"{DATA_PIPELINE_URL}/health", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            print(f"✅ Data Pipeline online")
            print(f"   Status: {data.get('status')}")
            return True
        else:
            print(f"❌ Data Pipeline error: {resp.status_code}")
            return False
    
    except Exception as e:
        print(f"❌ Data Pipeline test failed: {e}")
        return False

def test_rag_retrieval():
    """Test RAG retrieval for engineering queries"""
    print("\n" + "="*70)
    print("🧠 TEST 3: RAG Retrieval for Engineering Questions")
    print("="*70)
    
    # Test one HVAC question
    test_question = HVAC_QUESTIONS[0]
    print(f"\n📌 Test Query: {test_question}\n")
    
    try:
        # Try direct ChromaDB query
        payload = {
            "collection_name": "saleh_knowledge",
            "query_texts": [test_question],
            "n_results": 3
        }
        
        headers = {"Content-Type": "application/json"}
        resp = requests.post(
            f"{CHROMADB_URL}/api/v1/query",
            json=payload,
            headers=headers,
            timeout=10
        )
        
        if resp.status_code == 200:
            result = resp.json()
            
            if result.get('ids') and len(result['ids']) > 0:
                print("✅ RAG found relevant documents\n")
                
                for i, doc_id in enumerate(result['ids'], 1):
                    doc_text = result['documents'][0][i-1][:200] if result.get('documents') else "N/A"
                    distance = result.get('distances', [[]])[0][i-1] if result.get('distances') else "N/A"
                    
                    print(f"   {i}. Distance: {distance:.4f}")
                    print(f"      Preview: {doc_text}...")
                    print()
                
                return True
            else:
                print("⚠️  No results found in ChromaDB")
                return False
        else:
            print(f"❌ RAG query failed: {resp.status_code}")
            print(f"   Response: {resp.text[:300]}")
            return False
    
    except Exception as e:
        print(f"❌ RAG retrieval test failed: {e}")
        return False

def test_all_engineering_domains():
    """Test retrieval across all engineering domains"""
    print("\n" + "="*70)
    print("🏗️  TEST 4: Multi-Domain Engineering Coverage")
    print("="*70)
    
    all_questions = {
        "HVAC (SBC-501)": HVAC_QUESTIONS,
        "Plumbing (SBC-701)": PLUMBING_QUESTIONS,
        "Fire Safety (SBC-801)": FIRE_QUESTIONS,
    }
    
    results = {}
    for domain, questions in all_questions.items():
        print(f"\n📋 {domain}")
        domain_pass = 0
        
        for q in questions:
            try:
                payload = {
                    "collection_name": "saleh_knowledge",
                    "query_texts": [q],
                    "n_results": 1
                }
                
                resp = requests.post(
                    f"{CHROMADB_URL}/api/v1/query",
                    json=payload,
                    timeout=10
                )
                
                if resp.status_code == 200 and resp.json().get('ids'):
                    print(f"   ✅ {q[:60]}...")
                    domain_pass += 1
                else:
                    print(f"   ⚠️  {q[:60]}...")
            
            except:
                print(f"   ❌ {q[:60]}...")
        
        results[domain] = f"{domain_pass}/{len(questions)}"
        print(f"   → {domain_pass}/{len(questions)} passed")
    
    return results

def test_benchmark_questions():
    """Test benchmark engineering questions"""
    print("\n" + "="*70)
    print("📊 TEST 5: Benchmark Engineering Questions")
    print("="*70)
    
    try:
        with open("data/mep_rag/benchmark_questions_mep.json", "r", encoding="utf-8") as f:
            benchmark = json.load(f)
        
        total_questions = len(benchmark.get("questions", []))
        domains = benchmark.get("domains", {})
        
        print(f"\n✅ Benchmark file loaded")
        print(f"   Total questions: {total_questions}")
        print(f"\n   Breakdown by domain:")
        for domain, count in domains.items():
            print(f"      • {domain.upper()}: {count} questions")
        
        return True
    
    except Exception as e:
        print(f"❌ Benchmark test failed: {e}")
        return False

def generate_test_report():
    """Generate a test report"""
    print("\n" + "="*70)
    print("📋 TEST REPORT - Engineering Services Readiness")
    print("="*70)
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\nReport Time: {timestamp}\n")
    
    all_passed = True
    
    # Test 1
    chromadb_ok = test_chromadb()
    
    # Test 2
    pipeline_ok = test_data_pipeline()
    
    # Test 3
    rag_ok = test_rag_retrieval()
    
    # Test 4
    domain_results = test_all_engineering_domains()
    
    # Test 5
    benchmark_ok = test_benchmark_questions()
    
    # Summary
    print("\n" + "="*70)
    print("📊 SUMMARY")
    print("="*70)
    
    print(f"\n{'Service':<30} {'Status':<20}")
    print("-" * 50)
    print(f"{'ChromaDB':<30} {'✅ PASS' if chromadb_ok else '❌ FAIL':<20}")
    print(f"{'Data Pipeline':<30} {'✅ PASS' if pipeline_ok else '❌ FAIL':<20}")
    print(f"{'RAG Retrieval':<30} {'✅ PASS' if rag_ok else '⚠️  PARTIAL':<20}")
    print(f"{'Benchmark Data':<30} {'✅ PRESENT' if benchmark_ok else '❌ MISSING':<20}")
    
    print(f"\n{'Engineering Domain Coverage':<30}")
    print("-" * 50)
    for domain, result in domain_results.items():
        print(f"  {domain:<28} {result:<20}")
    
    # Readiness score
    services_ok = sum([chromadb_ok, pipeline_ok, rag_ok, benchmark_ok])
    readiness_score = (services_ok / 4) * 100
    
    print(f"\n🎯 READINESS SCORE: {readiness_score:.0f}%\n")
    
    if readiness_score >= 80:
        print("✅ System READY for MVP launch")
        print("   → Can deploy basic engineer assistant immediately")
        print("   → Recommend 2-3 week polish for UI/UX\n")
    elif readiness_score >= 60:
        print("⚠️  System PARTIALLY READY")
        print("   → Core functionality present")
        print("   → Needs 3-4 weeks development for completeness\n")
    else:
        print("❌ System NOT READY")
        print("   → Requires significant additional work\n")
    
    print("="*70)

if __name__ == "__main__":
    print("\n" + "🚀 "*35)
    print("ENGINEERING SERVICES - READINESS TEST SUITE")
    print("🚀 "*35)
    
    generate_test_report()
