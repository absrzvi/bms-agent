#!/usr/bin/env python3
"""
BMS Agent Performance Monitor
Tracks OpenWebUI, Ollama, Qdrant, and system performance during queries
"""

import psutil
import time
import json
import requests
from datetime import datetime
from pathlib import Path
import subprocess
import sys

class PerformanceMonitor:
    def __init__(self, output_dir="/workspace/001-bms-agent/logs/performance"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.metrics = []
        self.start_time = None
        
    def get_process_stats(self, process_name):
        """Get CPU and memory stats for a process"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
                if process_name.lower() in proc.info['name'].lower():
                    return {
                        'pid': proc.info['pid'],
                        'cpu_percent': proc.cpu_percent(interval=0.1),
                        'memory_mb': proc.info['memory_info'].rss / 1024 / 1024,
                        'memory_percent': proc.memory_percent()
                    }
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
        return None
    
    def get_ollama_stats(self):
        """Get Ollama API stats"""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            if response.status_code == 200:
                return {
                    'status': 'running',
                    'models': len(response.json().get('models', []))
                }
        except:
            pass
        return {'status': 'unavailable'}
    
    def get_qdrant_stats(self):
        """Get Qdrant stats"""
        try:
            # Collection info
            response = requests.get("http://localhost:6333/collections/bms_documents", timeout=2)
            if response.status_code == 200:
                data = response.json()
                return {
                    'status': 'running',
                    'points_count': data.get('result', {}).get('points_count', 0),
                    'vectors_count': data.get('result', {}).get('vectors_count', 0)
                }
        except:
            pass
        return {'status': 'unavailable'}
    
    def get_bms_api_stats(self):
        """Get BMS API stats"""
        try:
            response = requests.get("http://localhost:8000/health", timeout=2)
            if response.status_code == 200:
                return {
                    'status': 'running',
                    'health': response.json()
                }
        except:
            pass
        return {'status': 'unavailable'}
    
    def get_system_stats(self):
        """Get overall system stats"""
        return {
            'cpu_percent': psutil.cpu_percent(interval=0.1),
            'memory_percent': psutil.virtual_memory().percent,
            'memory_available_gb': psutil.virtual_memory().available / 1024 / 1024 / 1024,
            'disk_usage_percent': psutil.disk_usage('/').percent
        }
    
    def capture_snapshot(self):
        """Capture a complete performance snapshot"""
        timestamp = datetime.now().isoformat()
        elapsed = time.time() - self.start_time if self.start_time else 0
        
        snapshot = {
            'timestamp': timestamp,
            'elapsed_seconds': round(elapsed, 2),
            'system': self.get_system_stats(),
            'processes': {
                'openwebui': self.get_process_stats('open-webui'),
                'ollama': self.get_process_stats('ollama'),
                'qdrant': self.get_process_stats('qdrant'),
                'python': self.get_process_stats('python')  # BMS API
            },
            'services': {
                'ollama': self.get_ollama_stats(),
                'qdrant': self.get_qdrant_stats(),
                'bms_api': self.get_bms_api_stats()
            }
        }
        
        self.metrics.append(snapshot)
        return snapshot
    
    def start_monitoring(self, interval=1.0):
        """Start continuous monitoring"""
        self.start_time = time.time()
        print(f"🔍 Performance monitoring started (Session: {self.session_id})")
        print(f"📊 Capturing snapshots every {interval}s")
        print(f"📁 Output: {self.output_dir}/session_{self.session_id}.json")
        print("\n" + "="*70)
        print(f"{'Time':>8} | {'CPU%':>6} | {'RAM%':>6} | {'OpenWebUI':>12} | {'Ollama':>12} | {'Qdrant':>12}")
        print("="*70)
        
        try:
            while True:
                snapshot = self.capture_snapshot()
                
                # Print live stats
                system = snapshot['system']
                openwebui_cpu = snapshot['processes']['openwebui']['cpu_percent'] if snapshot['processes']['openwebui'] else 0
                ollama_cpu = snapshot['processes']['ollama']['cpu_percent'] if snapshot['processes']['ollama'] else 0
                qdrant_cpu = snapshot['processes']['qdrant']['cpu_percent'] if snapshot['processes']['qdrant'] else 0
                
                print(f"{snapshot['elapsed_seconds']:>7.1f}s | "
                      f"{system['cpu_percent']:>5.1f}% | "
                      f"{system['memory_percent']:>5.1f}% | "
                      f"CPU: {openwebui_cpu:>5.1f}% | "
                      f"CPU: {ollama_cpu:>5.1f}% | "
                      f"CPU: {qdrant_cpu:>5.1f}%")
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n" + "="*70)
            print("🛑 Monitoring stopped by user")
            self.save_results()
    
    def save_results(self):
        """Save monitoring results to file"""
        output_file = self.output_dir / f"session_{self.session_id}.json"
        
        # Calculate summary statistics
        summary = self.generate_summary()
        
        results = {
            'session_id': self.session_id,
            'start_time': self.metrics[0]['timestamp'] if self.metrics else None,
            'end_time': self.metrics[-1]['timestamp'] if self.metrics else None,
            'duration_seconds': self.metrics[-1]['elapsed_seconds'] if self.metrics else 0,
            'total_snapshots': len(self.metrics),
            'summary': summary,
            'metrics': self.metrics
        }
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n📊 Results saved to: {output_file}")
        print("\n📈 SUMMARY STATISTICS:")
        print("="*70)
        print(f"Duration: {results['duration_seconds']:.1f}s")
        print(f"Snapshots: {results['total_snapshots']}")
        print(f"\nSystem CPU: avg={summary['system']['cpu_avg']:.1f}%, max={summary['system']['cpu_max']:.1f}%")
        print(f"System RAM: avg={summary['system']['memory_avg']:.1f}%, max={summary['system']['memory_max']:.1f}%")
        
        if summary['processes']['openwebui']:
            print(f"\nOpenWebUI: avg CPU={summary['processes']['openwebui']['cpu_avg']:.1f}%, "
                  f"avg RAM={summary['processes']['openwebui']['memory_avg']:.0f}MB")
        if summary['processes']['ollama']:
            print(f"Ollama: avg CPU={summary['processes']['ollama']['cpu_avg']:.1f}%, "
                  f"avg RAM={summary['processes']['ollama']['memory_avg']:.0f}MB")
        if summary['processes']['qdrant']:
            print(f"Qdrant: avg CPU={summary['processes']['qdrant']['cpu_avg']:.1f}%, "
                  f"avg RAM={summary['processes']['qdrant']['memory_avg']:.0f}MB")
        
        print("="*70)
    
    def generate_summary(self):
        """Generate summary statistics from metrics"""
        if not self.metrics:
            return {}
        
        # System stats
        cpu_values = [m['system']['cpu_percent'] for m in self.metrics]
        memory_values = [m['system']['memory_percent'] for m in self.metrics]
        
        summary = {
            'system': {
                'cpu_avg': sum(cpu_values) / len(cpu_values),
                'cpu_max': max(cpu_values),
                'cpu_min': min(cpu_values),
                'memory_avg': sum(memory_values) / len(memory_values),
                'memory_max': max(memory_values),
                'memory_min': min(memory_values)
            },
            'processes': {}
        }
        
        # Process stats
        for process_name in ['openwebui', 'ollama', 'qdrant']:
            process_metrics = [m['processes'][process_name] for m in self.metrics if m['processes'][process_name]]
            
            if process_metrics:
                cpu_vals = [p['cpu_percent'] for p in process_metrics]
                mem_vals = [p['memory_mb'] for p in process_metrics]
                
                summary['processes'][process_name] = {
                    'cpu_avg': sum(cpu_vals) / len(cpu_vals),
                    'cpu_max': max(cpu_vals),
                    'memory_avg': sum(mem_vals) / len(mem_vals),
                    'memory_max': max(mem_vals)
                }
            else:
                summary['processes'][process_name] = None
        
        return summary


def main():
    print("="*70)
    print("🚀 BMS Agent Performance Monitor")
    print("="*70)
    print("\nThis tool monitors system performance while you test queries.")
    print("\nPress Ctrl+C to stop monitoring and save results.\n")
    
    # Check if services are running
    monitor = PerformanceMonitor()
    snapshot = monitor.capture_snapshot()
    
    print("📋 Service Status Check:")
    print(f"  OpenWebUI: {'✅' if snapshot['processes']['openwebui'] else '❌'}")
    print(f"  Ollama: {'✅' if snapshot['services']['ollama']['status'] == 'running' else '❌'}")
    print(f"  Qdrant: {'✅' if snapshot['services']['qdrant']['status'] == 'running' else '❌'}")
    print(f"  BMS API: {'✅' if snapshot['services']['bms_api']['status'] == 'running' else '❌'}")
    print()
    
    # Start monitoring
    interval = float(sys.argv[1]) if len(sys.argv) > 1 else 1.0
    monitor.start_monitoring(interval=interval)


if __name__ == "__main__":
    main()
