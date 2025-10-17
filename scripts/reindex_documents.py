#!/usr/bin/env python3
"""
Re-index all documents in Qdrant with correct embedding dimensions
"""

import sys
import os
from pathlib import Path
import requests
from glob import glob

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def main():
    """Re-index all documents via API"""
    
    api_url = "http://localhost:8000"
    upload_dir = "/workspace/bms_data/uploads"
    
    # Check API is available
    try:
        response = requests.get(f"{api_url}/health", timeout=5)
        if response.status_code != 200:
            print(f"❌ API not responding at {api_url}")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        sys.exit(1)
    
    # Get all documents
    patterns = ["*.pdf", "*.docx", "*.xlsx", "*.pptx", "*.csv", "*.txt"]
    all_files = []
    for pattern in patterns:
        all_files.extend(glob(f"{upload_dir}/{pattern}"))
    
    print(f"📁 Found {len(all_files)} documents to process")
    print(f"   Location: {upload_dir}")
    print()
    
    # Process each document
    success = 0
    failed = 0
    
    for i, filepath in enumerate(all_files, 1):
        filename = os.path.basename(filepath)
        print(f"[{i}/{len(all_files)}] Processing: {filename[:60]}...")
        
        try:
            with open(filepath, 'rb') as f:
                files = {'file': (filename, f)}
                response = requests.post(
                    f"{api_url}/api/v1/documents/upload",
                    files=files,
                    timeout=120
                )
                
                if response.status_code == 200:
                    data = response.json()
                    chunks = data.get('chunks_created', 0)
                    print(f"   ✅ Success: {chunks} chunks created")
                    success += 1
                else:
                    print(f"   ❌ Failed: {response.status_code} - {response.text[:100]}")
                    failed += 1
        except Exception as e:
            print(f"   ❌ Error: {e}")
            failed += 1
    
    print()
    print("=" * 70)
    print(f"📊 Re-indexing Complete")
    print(f"   Success: {success}/{len(all_files)}")
    print(f"   Failed: {failed}/{len(all_files)}")
    print("=" * 70)
    
    # Check final count
    try:
        response = requests.get(f"http://localhost:6333/collections/nomad_bms_documents")
        data = response.json()
        points = data.get('result', {}).get('points_count', 0)
        print(f"\n📊 Total documents in Qdrant: {points}")
    except:
        pass
    
    sys.exit(0 if failed == 0 else 1)

if __name__ == "__main__":
    main()
