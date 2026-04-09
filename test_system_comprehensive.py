#!/usr/bin/env python3
"""
Comprehensive System Health and Functionality Test
فحص شامل لصحة النظام والعمليات الأساسية
"""
import os
import requests
import json
import time
import subprocess
from datetime import datetime
from typing import Dict, List, Tuple

# Configuration
ENDPOINTS = {
    "chromadb": "http://localhost:8010",
    "n8n": "http://localhost:5678",
    "open_webui": "http://localhost:3000",
    "pipelines": "http://localhost:9099",
    "data_pipeline": "http://localhost:8001",
}

TEST_QUERIES = {
    "ar": "ما هي حقوق العامل في نظام العمل السعودي؟",
    "general": "نظام العمل السعودي",
}

class SystemTester:
    def __init__(self):
        self.results = {}
        self.start_time = datetime.now()
    
    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        icon_map = {
            "INFO": "ℹ️ ",
            "SUCCESS": "✅ ",
            "ERROR": "❌ ",
            "WARNING": "⚠️ ",
            "TEST": "🧪 "
        }
        icon = icon_map.get(level, "→ ")
        print(f"{icon} [{timestamp}] {message}")
    
    def print_section(self, title: str):
        print(f"\n{'='*70}")
        print(f"  {title}")
        print(f"{'='*70}\n")
    
    # ==================== Service Health Checks ====================
    
    def test_service_health(self) -> bool:
        self.print_section("🔍 SERVICE HEALTH CHECKS")
        
        all_healthy = True
        health_results = {}
        
        for service_name, url in ENDPOINTS.items():
            try:
                self.log(f"Checking {service_name}...", "TEST")
                response = requests.get(f"{url}/health", timeout=5)
                
                if response.status_code == 200:
                    self.log(f"{service_name}: Online ✓", "SUCCESS")
                    health_results[service_name] = {"status": "online", "code": 200}
                else:
                    self.log(f"{service_name}: Responded ({response.status_code}) but not healthy", "WARNING")
                    health_results[service_name] = {"status": "online", "code": response.status_code}
                    all_healthy = False
            except requests.exceptions.ConnectError:
                self.log(f"{service_name}: OFFLINE ✗", "ERROR")
                health_results[service_name] = {"status": "offline", "error": "Connection refused"}
                all_healthy = False
            except requests.exceptions.Timeout:
                self.log(f"{service_name}: Timeout", "ERROR")
                health_results[service_name] = {"status": "timeout"}
                all_healthy = False
            except Exception as e:
                self.log(f"{service_name}: Error - {str(e)}", "ERROR")
                health_results[service_name] = {"status": "error", "error": str(e)}
                all_healthy = False
        
        self.results["service_health"] = health_results
        return all_healthy
    
    # ==================== ChromaDB Tests ====================
    
    def test_chromadb(self) -> bool:
        self.print_section("📚 CHROMADB TESTS")
        
        try:
            self.log("Checking ChromaDB collections...", "TEST")
            response = requests.get(f"{ENDPOINTS['chromadb']}/api/v1/collections", timeout=10)
            
            if response.status_code != 200:
                self.log(f"ChromaDB API error: {response.status_code}", "ERROR")
                return False
            
            collections = response.json()
            self.log(f"Found {len(collections)} collection(s)", "SUCCESS")
            
            for coll in collections:
                print(f"    • {coll['name']} ({coll['metadata'].get('hnsw:space', 'unknown')} space)")
            
            # Test with saleh_knowledge collection
            self.log("Testing saleh_knowledge collection...", "TEST")
            
            # Get collection count
            response = requests.get(
                f"{ENDPOINTS['chromadb']}/api/v1/collections/saleh_knowledge/count",
                timeout=10
            )
            
            if response.status_code == 200:
                count = response.json()
                self.log(f"saleh_knowledge has {count} vectors", "SUCCESS")
                self.results["chromadb"] = {"status": "ok", "collections": len(collections), "vectors": count}
                return True
            else:
                self.log(f"Failed to count vectors: {response.status_code}", "ERROR")
                return False
        
        except Exception as e:
            self.log(f"ChromaDB test error: {str(e)}", "ERROR")
            return False
    
    # ==================== RAG Retrieval Test ====================
    
    def test_rag_retrieval(self) -> bool:
        self.print_section("🧠 RAG RETRIEVAL TEST")
        
        try:
            self.log("Testing RAG pipeline...", "TEST")
            self.log(f"Query: {TEST_QUERIES['ar']}", "INFO")
            
            # Test using pipelines API (n8n_controller)
            headers = {"Authorization": f"Bearer {os.environ.get('PIPELINES_API_KEY', '')}"}
            
            payload = {
                "collection": "saleh_knowledge",
                "query": TEST_QUERIES["ar"],
                "top_k": 5,
                "embedding_model": "nomic-embed-text:latest"
            }
            
            response = requests.post(
                f"{ENDPOINTS['pipelines']}/api/v1/pipelines/call/n8n_controller",
                json=payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                self.log(f"RAG returned {len(result.get('results', []))} results", "SUCCESS")
                
                if result.get("results"):
                    for i, doc in enumerate(result["results"][:3], 1):
                        distance = doc.get("distance", "N/A")
                        content = doc.get("documents", [""])[0][:100]
                        print(f"    {i}. [Distance: {distance}] {content}...")
                
                self.results["rag_retrieval"] = {"status": "ok", "results_count": len(result.get("results", []))}
                return True
            else:
                self.log(f"RAG test failed: {response.status_code}", "ERROR")
                self.log(f"Response: {response.text[:500]}", "ERROR")
                return False
        
        except Exception as e:
            self.log(f"RAG test error: {str(e)}", "ERROR")
            return False
    
    # ==================== n8n Workflows Test ====================
    
    def test_n8n_workflows(self) -> bool:
        self.print_section("⚙️  N8N WORKFLOWS TEST")
        
        try:
            self.log("Checking n8n workflows status...", "TEST")
            
            # Query database directly
            cmd = [
                "docker", "exec", "salehsaas_postgres",
                "psql", "-U", "salehsaas", "-d", "salehsaas", "-t",
                "-c", "SELECT id, name, active FROM workflow_entity WHERE active = true;"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 and result.stdout:
                active_workflows = []
                for line in result.stdout.strip().split('\n'):
                    if line.strip() and '|' in line:
                        parts = [p.strip() for p in line.split('|')]
                        if len(parts) >= 3:
                            active_workflows.append({
                                "id": parts[0],
                                "name": parts[1],
                                "active": True
                            })
                
                self.log(f"Found {len(active_workflows)} active workflow(s)", "SUCCESS")
                for wf in active_workflows:
                    print(f"    • {wf['name']}")
                
                self.results["n8n_workflows"] = {"status": "ok", "active_count": len(active_workflows)}
                return len(active_workflows) > 0
            else:
                self.log("Failed to fetch workflows", "ERROR")
                return False
        
        except Exception as e:
            self.log(f"n8n test error: {str(e)}", "ERROR")
            return False
    
    # ==================== Web Search Test ====================
    
    def test_web_search(self) -> bool:
        self.print_section("🔍 WEB SEARCH TEST (SearXNG)")
        
        try:
            self.log("Testing SearXNG web search...", "TEST")
            
            # Direct query to SearXNG from host
            params = {
                "q": "السعودية القانون",
                "format": "json"
            }
            
            response = requests.get(
                "http://localhost:8080/search",
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                results = response.json()
                result_count = len(results.get("results", []))
                self.log(f"SearXNG returned {result_count} results", "SUCCESS")
                
                if result_count > 0:
                    for i, res in enumerate(results["results"][:3], 1):
                        print(f"    {i}. {res.get('title', 'N/A')[:80]}")
                
                self.results["web_search"] = {"status": "ok", "result_count": result_count}
                return True
            else:
                self.log(f"SearXNG error: {response.status_code}", "ERROR")
                return False
        
        except Exception as e:
            self.log(f"Web search test error: {str(e)}", "ERROR")
            return False
    
    # ==================== Docker Services Test ====================
    
    def test_docker_services(self) -> bool:
        self.print_section("🐳 DOCKER SERVICES TEST")
        
        try:
            self.log("Checking Docker containers...", "TEST")
            
            cmd = ["docker", "ps", "-f", "name=salehsaas", "--format", "table {{.Names}}\t{{.Status}}"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                containers = []
                for line in result.stdout.strip().split('\n')[1:]:  # Skip header
                    if line.strip():
                        parts = line.split('\t')
                        if len(parts) == 2:
                            containers.append({
                                "name": parts[0],
                                "status": parts[1]
                            })
                
                self.log(f"Found {len(containers)} container(s)", "SUCCESS")
                
                all_running = True
                for cont in containers:
                    is_running = "Up" in cont["status"]
                    status_icon = "✓" if is_running else "✗"
                    print(f"    {status_icon} {cont['name']}: {cont['status']}")
                    if not is_running:
                        all_running = False
                
                self.results["docker_services"] = {"status": "ok", "containers": len(containers), "all_running": all_running}
                return all_running
            else:
                self.log("Failed to check Docker", "ERROR")
                return False
        
        except Exception as e:
            self.log(f"Docker test error: {str(e)}", "ERROR")
            return False
    
    # ==================== Run All Tests ====================
    
    def run_all_tests(self):
        self.print_section("🚀 SYSTEM COMPREHENSIVE TEST SUITE")
        
        print("Start time:", self.start_time.strftime("%Y-%m-%d %H:%M:%S\n"))
        
        # Run tests in order
        test_results = {
            "Services Health": self.test_service_health(),
            "Docker Services": self.test_docker_services(),
            "ChromaDB": self.test_chromadb(),
            "n8n Workflows": self.test_n8n_workflows(),
            "RAG Retrieval": self.test_rag_retrieval(),
            "Web Search": self.test_web_search(),
        }
        
        # Final Report
        self.print_section("📊 TEST RESULTS SUMMARY")
        
        passed = sum(1 for v in test_results.values() if v)
        total = len(test_results)
        
        print(f"Passed: {passed}/{total}\n")
        
        for test_name, result in test_results.items():
            icon = "✅" if result else "❌"
            print(f"  {icon} {test_name}")
        
        # Overall status
        print(f"\n{'='*70}")
        if passed == total:
            print("✅ ALL TESTS PASSED - System is healthy!")
        elif passed >= total * 0.8:
            print("⚠️  MOST TESTS PASSED - Minor issues detected")
        else:
            print("❌ CRITICAL ISSUES - System needs attention")
        print(f"{'='*70}\n")
        
        # Duration
        duration = datetime.now() - self.start_time
        print(f"Test duration: {duration.total_seconds():.2f} seconds")
        
        # Save results
        self.save_results()
    
    def save_results(self):
        """Save detailed results to JSON"""
        output_file = "test_results.json"
        results_json = {
            "timestamp": self.start_time.isoformat(),
            "duration": str(datetime.now() - self.start_time),
            "tests": self.results
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results_json, f, ensure_ascii=False, indent=2)
        
        self.log(f"Results saved to {output_file}", "SUCCESS")

if __name__ == "__main__":
    tester = SystemTester()
    tester.run_all_tests()
