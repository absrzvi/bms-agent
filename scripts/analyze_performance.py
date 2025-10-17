#!/usr/bin/env python3
"""
Performance Analysis Tool
Analyzes saved performance monitoring data and generates insights
"""

import json
import sys
from pathlib import Path
from datetime import datetime

def analyze_session(json_file):
    """Analyze a performance monitoring session"""
    
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    print("="*80)
    print(f"📊 PERFORMANCE ANALYSIS: {data['session_id']}")
    print("="*80)
    
    # Duration
    duration = data['duration_seconds']
    print(f"\n⏱️  DURATION: {duration:.1f} seconds ({duration/60:.1f} minutes)")
    print(f"📸 SNAPSHOTS: {data['total_snapshots']} (every {duration/data['total_snapshots']:.1f}s)")
    
    # System performance
    summary = data['summary']
    sys_stats = summary['system']
    
    print(f"\n🖥️  SYSTEM PERFORMANCE:")
    print(f"   CPU Usage:")
    print(f"      Average: {sys_stats['cpu_avg']:.1f}%")
    print(f"      Peak:    {sys_stats['cpu_max']:.1f}%")
    print(f"      Minimum: {sys_stats['cpu_min']:.1f}%")
    
    print(f"\n   Memory Usage:")
    print(f"      Average: {sys_stats['memory_avg']:.1f}%")
    print(f"      Peak:    {sys_stats['memory_max']:.1f}%")
    print(f"      Minimum: {sys_stats['memory_min']:.1f}%")
    
    # Process performance
    print(f"\n🔧 PROCESS PERFORMANCE:")
    
    for process_name, stats in summary['processes'].items():
        if stats:
            print(f"\n   {process_name.upper()}:")
            print(f"      CPU: avg={stats['cpu_avg']:.1f}%, peak={stats['cpu_max']:.1f}%")
            print(f"      RAM: avg={stats['memory_avg']:.0f}MB, peak={stats['memory_max']:.0f}MB")
        else:
            print(f"\n   {process_name.upper()}: Not detected")
    
    # Find peak load periods
    print(f"\n🔥 PEAK LOAD ANALYSIS:")
    metrics = data['metrics']
    
    # Find top 3 CPU peaks
    sorted_by_cpu = sorted(metrics, key=lambda x: x['system']['cpu_percent'], reverse=True)[:3]
    print(f"\n   Top 3 CPU Spikes:")
    for i, m in enumerate(sorted_by_cpu, 1):
        print(f"      {i}. {m['elapsed_seconds']:.1f}s: {m['system']['cpu_percent']:.1f}% CPU")
    
    # Find top 3 memory peaks
    sorted_by_mem = sorted(metrics, key=lambda x: x['system']['memory_percent'], reverse=True)[:3]
    print(f"\n   Top 3 Memory Peaks:")
    for i, m in enumerate(sorted_by_mem, 1):
        print(f"      {i}. {m['elapsed_seconds']:.1f}s: {m['system']['memory_percent']:.1f}% RAM")
    
    # Performance classification
    print(f"\n📈 PERFORMANCE RATING:")
    
    avg_cpu = sys_stats['cpu_avg']
    avg_mem = sys_stats['memory_avg']
    
    if avg_cpu < 30 and avg_mem < 50:
        rating = "✅ EXCELLENT - Low resource usage"
    elif avg_cpu < 50 and avg_mem < 70:
        rating = "✅ GOOD - Moderate resource usage"
    elif avg_cpu < 70 and avg_mem < 85:
        rating = "⚠️  ACCEPTABLE - High resource usage"
    else:
        rating = "❌ POOR - Very high resource usage"
    
    print(f"   {rating}")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    
    if sys_stats['cpu_max'] > 80:
        print("   ⚠️  CPU spiked above 80% - consider optimization")
    
    if sys_stats['memory_max'] > 85:
        print("   ⚠️  Memory usage above 85% - risk of swapping")
    
    ollama_stats = summary['processes'].get('ollama')
    if ollama_stats and ollama_stats['cpu_avg'] > 50:
        print("   ⚠️  Ollama CPU usage high - model may be too large")
    
    if ollama_stats and ollama_stats['memory_avg'] > 4000:
        print("   ⚠️  Ollama using >4GB RAM - consider smaller model")
    
    openwebui_stats = summary['processes'].get('openwebui')
    if openwebui_stats and openwebui_stats['memory_avg'] > 1000:
        print("   ℹ️  OpenWebUI using >1GB RAM - normal for active sessions")
    
    print("="*80)


def compare_sessions(json_files):
    """Compare multiple performance sessions"""
    
    sessions = []
    for file in json_files:
        with open(file, 'r') as f:
            sessions.append(json.load(f))
    
    print("="*80)
    print(f"📊 COMPARING {len(sessions)} SESSIONS")
    print("="*80)
    
    print(f"\n{'Session':<20} | {'Duration':<10} | {'CPU Avg':<10} | {'RAM Avg':<10} | {'Rating':<15}")
    print("-"*80)
    
    for session in sessions:
        session_id = session['session_id']
        duration = session['duration_seconds']
        cpu_avg = session['summary']['system']['cpu_avg']
        mem_avg = session['summary']['system']['memory_avg']
        
        if cpu_avg < 30:
            rating = "Excellent"
        elif cpu_avg < 50:
            rating = "Good"
        elif cpu_avg < 70:
            rating = "Acceptable"
        else:
            rating = "Poor"
        
        print(f"{session_id:<20} | {duration:>8.1f}s | {cpu_avg:>8.1f}% | {mem_avg:>8.1f}% | {rating:<15}")
    
    print("="*80)


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Analyze single session: python analyze_performance.py <session.json>")
        print("  Compare sessions:       python analyze_performance.py <session1.json> <session2.json> ...")
        sys.exit(1)
    
    json_files = [Path(f) for f in sys.argv[1:]]
    
    # Check all files exist
    for f in json_files:
        if not f.exists():
            print(f"❌ Error: File not found: {f}")
            sys.exit(1)
    
    if len(json_files) == 1:
        analyze_session(json_files[0])
    else:
        compare_sessions(json_files)


if __name__ == "__main__":
    main()
