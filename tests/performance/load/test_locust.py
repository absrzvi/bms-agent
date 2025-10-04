"""
Locust Performance Test Suite for BMS Agent
POC DECISION: Baseline performance measurement only - no pass/fail criteria
"""

import json
import random
import tempfile
from pathlib import Path
from locust import HttpUser, task, between, events
from locust.runners import MasterRunner, WorkerRunner
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BMSAgentUser(HttpUser):
    """Simulated user for BMS Agent performance testing"""
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks
    
    def on_start(self):
        """Initialize user session"""
        self.document_ids = []
        self.test_queries = [
            "How to configure VLAN settings for railway network?",
            "R4600-2Ax CCU technical specifications",
            "EN50155 compliance requirements",
            "Network topology configuration",
            "Railway connectivity standards",
            "VLAN 101 configuration guide",
            "CCU maintenance procedures",
            "Ethernet switch settings",
            "WiFi network setup railway",
            "IP addressing scheme railway"
        ]
        
        # Create test documents for upload
        self.create_test_documents()
    
    def create_test_documents(self):
        """Create sample documents for testing"""
        self.test_docs = []
        
        # Railway technical document
        railway_content = f"""
        Railway Network Configuration Manual - Test Document {random.randint(1000, 9999)}
        
        Section 1: VLAN Configuration
        The R4600-2Ax CCU supports VLAN 101 with 1Gbps throughput.
        Configure the network settings according to EN50155 standards.
        
        Section 2: Network Components
        - CCU (Central Control Unit): Manages train communication
        - VLAN 101: Primary data network for passenger services
        - VLAN 102: Secondary network for maintenance systems
        
        Section 3: Standards Compliance
        This system complies with EN50155, EN50121, and TSI specifications.
        
        Technical Specifications:
        - Frequency: 2.4 GHz and 5 GHz dual-band
        - Power: 12V DC, max 2.5A
        - Temperature: -40°C to +70°C
        - IP rating: IP65
        
        Configuration Steps:
        1. Connect to CCU management interface
        2. Set VLAN ID to 101
        3. Configure IP range 192.168.101.0/24
        4. Enable QoS for passenger services
        5. Test connectivity and performance
        """
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(railway_content)
            self.test_docs.append(('railway_manual.txt', Path(f.name), 'railway'))
        
        # General network guide
        general_content = f"""
        Network Infrastructure Guidelines - Document {random.randint(1000, 9999)}
        
        This document provides general guidelines for network setup.
        
        Basic Configuration:
        1. Set up IP addressing scheme
        2. Configure routing protocols  
        3. Implement security policies
        4. Monitor network performance
        
        Best Practices:
        - Use standardized configurations
        - Document all changes
        - Regular security audits
        - Performance monitoring
        
        Network Architecture:
        - Core layer: High-speed backbone
        - Distribution layer: Policy enforcement
        - Access layer: End-device connectivity
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(general_content)
            self.test_docs.append(('network_guide.txt', Path(f.name), 'general'))
    
    def on_stop(self):
        """Cleanup when user session ends"""
        # Clean up test documents
        for _, doc_path, _ in self.test_docs:
            if doc_path.exists():
                doc_path.unlink()
    
    @task(1)
    def upload_document(self):
        """Upload a document for processing (5% of tasks per Q8 spec)"""
        if not self.test_docs:
            return
            
        # Select random document
        doc_name, doc_path, profile = random.choice(self.test_docs)
        
        try:
            with open(doc_path, 'rb') as f:
                files = {'file': (doc_name, f, 'text/plain')}
                data = {'profile': profile}
                
                with self.client.post(
                    "/api/v1/documents/upload",
                    files=files,
                    data=data,
                    catch_response=True,
                    name="upload_document"
                ) as response:
                    if response.status_code == 200:
                        try:
                            result = response.json()
                            if result.get('status') == 'success':
                                self.document_ids.append(result.get('document_id'))
                                response.success()
                            else:
                                response.failure(f"Upload failed: {result.get('error', 'Unknown error')}")
                        except json.JSONDecodeError:
                            response.failure("Invalid JSON response")
                    else:
                        response.failure(f"HTTP {response.status_code}")
                        
        except Exception as e:
            logger.error(f"Upload error: {e}")
    
    @task(12)
    def semantic_search(self):
        """Perform semantic search (60% of tasks per Q8 spec - primary read operation)"""
        query = random.choice(self.test_queries)
        
        payload = {
            "query": query,
            "limit": random.choice([5, 10, 15]),
            "filters": {
                "processing_profile": random.choice(["railway", "general", "technical"])
            }
        }
        
        with self.client.post(
            "/api/v1/search/semantic",
            json=payload,
            catch_response=True,
            name="semantic_search"
        ) as response:
            if response.status_code == 200:
                try:
                    result = response.json()
                    if result.get('status') == 'success':
                        results_count = len(result.get('results', []))
                        search_time = result.get('search_metadata', {}).get('search_time_ms', 0)
                        
                        # Log performance metrics
                        logger.info(f"Semantic search: {results_count} results, {search_time}ms")
                        response.success()
                    else:
                        response.failure(f"Search failed: {result.get('error', 'Unknown error')}")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"HTTP {response.status_code}")
    
    @task(6)
    def hybrid_search(self):
        """Perform hybrid search (30% of tasks per Q8 spec)"""
        query = random.choice(self.test_queries)
        
        payload = {
            "query": query,
            "limit": random.choice([3, 5, 8]),
            "vector_weight": random.choice([0.3, 0.5, 0.7]),
            "keyword_weight": random.choice([0.3, 0.5, 0.7]),
            "filters": {
                "processing_profile": "railway",
                "has_context": True
            }
        }
        
        # Ensure weights sum to 1.0
        total_weight = payload["vector_weight"] + payload["keyword_weight"]
        if total_weight != 1.0:
            payload["vector_weight"] = 0.6
            payload["keyword_weight"] = 0.4
        
        with self.client.post(
            "/api/v1/search/hybrid",
            json=payload,
            catch_response=True,
            name="hybrid_search"
        ) as response:
            if response.status_code == 200:
                try:
                    result = response.json()
                    if result.get('status') == 'success':
                        results_count = len(result.get('results', []))
                        search_time = result.get('search_metadata', {}).get('search_time_ms', 0)
                        
                        # Log performance metrics
                        logger.info(f"Hybrid search: {results_count} results, {search_time}ms")
                        response.success()
                    else:
                        response.failure(f"Hybrid search failed: {result.get('error', 'Unknown error')}")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"HTTP {response.status_code}")
    
    @task(1)
    def health_check(self):
        """Check system health (10% of tasks)"""
        with self.client.get(
            "/health",
            catch_response=True,
            name="health_check"
        ) as response:
            if response.status_code == 200:
                try:
                    result = response.json()
                    if result.get('status') == 'healthy':
                        response.success()
                    else:
                        response.failure(f"System unhealthy: {result.get('error', 'Unknown error')}")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"HTTP {response.status_code}")

# Performance metrics collection
performance_stats = {
    'upload_times': [],
    'semantic_search_times': [],
    'hybrid_search_times': [],
    'health_check_times': [],
    'error_count': 0,
    'total_requests': 0
}

@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, context, **kwargs):
    """Collect performance statistics"""
    global performance_stats
    
    performance_stats['total_requests'] += 1
    
    if exception:
        performance_stats['error_count'] += 1
        logger.error(f"Request failed: {name} - {exception}")
    else:
        # Collect response times by endpoint
        if name == "upload_document":
            performance_stats['upload_times'].append(response_time)
        elif name == "semantic_search":
            performance_stats['semantic_search_times'].append(response_time)
        elif name == "hybrid_search":
            performance_stats['hybrid_search_times'].append(response_time)
        elif name == "health_check":
            performance_stats['health_check_times'].append(response_time)

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Generate performance report when test completes"""
    global performance_stats
    
    if isinstance(environment.runner, MasterRunner) or isinstance(environment.runner, WorkerRunner):
        return  # Only generate report on standalone or master
    
    logger.info("=" * 60)
    logger.info("BMS AGENT PERFORMANCE BASELINE REPORT")
    logger.info("=" * 60)
    
    # Calculate statistics
    def calc_percentiles(times):
        if not times:
            return {"count": 0, "avg": 0, "p50": 0, "p95": 0, "p99": 0, "min": 0, "max": 0}
        
        times.sort()
        count = len(times)
        return {
            "count": count,
            "avg": sum(times) / count,
            "p50": times[int(count * 0.5)],
            "p95": times[int(count * 0.95)] if count > 20 else times[-1],
            "p99": times[int(count * 0.99)] if count > 100 else times[-1],
            "min": min(times),
            "max": max(times)
        }
    
    # Generate report
    report = {
        "test_summary": {
            "total_requests": performance_stats['total_requests'],
            "error_count": performance_stats['error_count'],
            "error_rate": (performance_stats['error_count'] / performance_stats['total_requests'] * 100) 
                         if performance_stats['total_requests'] > 0 else 0
        },
        "upload_performance": calc_percentiles(performance_stats['upload_times']),
        "semantic_search_performance": calc_percentiles(performance_stats['semantic_search_times']),
        "hybrid_search_performance": calc_percentiles(performance_stats['hybrid_search_times']),
        "health_check_performance": calc_percentiles(performance_stats['health_check_times'])
    }
    
    # Log summary
    logger.info(f"Total Requests: {report['test_summary']['total_requests']}")
    logger.info(f"Error Rate: {report['test_summary']['error_rate']:.2f}%")
    logger.info("")
    
    for endpoint, stats in [
        ("Document Upload", report['upload_performance']),
        ("Semantic Search", report['semantic_search_performance']),
        ("Hybrid Search", report['hybrid_search_performance']),
        ("Health Check", report['health_check_performance'])
    ]:
        if stats['count'] > 0:
            logger.info(f"{endpoint}:")
            logger.info(f"  Count: {stats['count']}")
            logger.info(f"  Average: {stats['avg']:.2f}ms")
            logger.info(f"  P50: {stats['p50']:.2f}ms")
            logger.info(f"  P95: {stats['p95']:.2f}ms")
            logger.info(f"  P99: {stats['p99']:.2f}ms")
            logger.info(f"  Min: {stats['min']:.2f}ms")
            logger.info(f"  Max: {stats['max']:.2f}ms")
            logger.info("")
    
    # Save detailed report to file
    try:
        report_path = Path("performance_baseline_report.json")
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Detailed report saved to: {report_path}")
    except Exception as e:
        logger.error(f"Failed to save report: {e}")
    
    logger.info("=" * 60)
    logger.info("POC BASELINE MEASUREMENT COMPLETE")
    logger.info("Note: This is baseline data collection only.")
    logger.info("No performance targets or pass/fail criteria applied.")
    logger.info("=" * 60)

# Test configuration classes for different load scenarios
class LightLoadUser(BMSAgentUser):
    """Light load testing - simulates 1-10 users"""
    wait_time = between(2, 5)

class MediumLoadUser(BMSAgentUser):
    """Medium load testing - simulates 10-50 users"""
    wait_time = between(1, 3)

class HeavyLoadUser(BMSAgentUser):
    """Heavy load testing - simulates 50+ users"""
    wait_time = between(0.5, 2)

if __name__ == "__main__":
    # This allows running the test directly for development
    import subprocess
    import sys
    
    print("BMS Agent Locust Performance Test")
    print("Usage examples:")
    print("  locust -f test_locust.py --host=http://localhost:8000")
    print("  locust -f test_locust.py --host=http://localhost:8000 -u 10 -r 2 -t 60s")
    print("")
    print("Load scenarios:")
    print("  Light:  locust -f test_locust.py BmsAgentUser --host=http://localhost:8000 -u 5 -r 1")
    print("  Medium: locust -f test_locust.py BmsAgentUser --host=http://localhost:8000 -u 25 -r 5") 
    print("  Heavy:  locust -f test_locust.py BmsAgentUser --host=http://localhost:8000 -u 100 -r 10")
