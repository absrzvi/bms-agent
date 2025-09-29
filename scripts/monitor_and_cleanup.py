#!/usr/bin/env python3
"""
Monitor batch processing and move failed documents
"""

import time
import requests
from pathlib import Path
import shutil

def check_progress():
    """Check Qdrant collection progress"""
    try:
        r = requests.get('http://localhost:6333/collections/nomad_bms_documents')
        data = r.json()
        points = data['result']['points_count']
        return points
    except:
        return 0

def main():
    """Monitor progress"""
    print("🔍 Monitoring batch processing progress...")
    print("=" * 70)
    
    failed_dir = Path("/workspace/bms_data/failed_documents")
    failed_dir.mkdir(parents=True, exist_ok=True)
    
    last_count = 0
    no_change_count = 0
    
    while True:
        current_count = check_progress()
        
        if current_count != last_count:
            print(f"📊 Progress: {current_count} chunks stored in Qdrant")
            last_count = current_count
            no_change_count = 0
        else:
            no_change_count += 1
        
        # If no change for 5 checks (50 seconds), assume done
        if no_change_count >= 5 and current_count > 0:
            print(f"\n✅ Processing appears complete!")
            print(f"📊 Final count: {current_count} chunks in Qdrant")
            break
        
        time.sleep(10)
    
    print("\n🎉 Batch processing monitoring complete!")

if __name__ == "__main__":
    main()
