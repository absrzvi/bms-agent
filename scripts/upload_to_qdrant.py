#!/usr/bin/env python3
"""
Upload Processed Documents to Qdrant
Takes documents from uploads directory and processes them through the API
which properly stores them in Qdrant with embeddings
"""

import sys
import time
import requests
from pathlib import Path

def upload_document(file_path, api_url="http://localhost:8000"):
    """Upload a single document through the API"""
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (file_path.name, f)}
            data = {'profile': 'railway'}
            
            response = requests.post(
                f"{api_url}/api/v1/documents/upload",
                files=files,
                data=data,
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                chunks = result.get('processing_result', {}).get('chunks_created', 0)
                quality = result.get('processing_result', {}).get('quality_score', 0)
                return True, chunks, quality
            else:
                return False, 0, 0
                
    except Exception as e:
        print(f"  Error: {e}")
        return False, 0, 0

def main():
    """Upload all documents to Qdrant via API"""
    
    base_dir = Path("/workspace/bms_data/uploads")
    api_url = "http://localhost:8000"
    
    # Check if API is running
    try:
        response = requests.get(f"{api_url}/health", timeout=5)
        if response.status_code != 200:
            print("❌ API server is not running!")
            print("Start it with: uvicorn api.main:app --host 0.0.0.0 --port 8000")
            return 1
    except:
        print("❌ Cannot connect to API server!")
        print("Start it with: uvicorn api.main:app --host 0.0.0.0 --port 8000")
        return 1
    
    print("🚀 Uploading Documents to Qdrant via API")
    print("=" * 70)
    print()
    
    # Find all documents
    patterns = ["*.pdf", "*.docx", "*.pptx", "*.xlsx", "*.csv", "*.txt"]
    all_files = []
    for pattern in patterns:
        all_files.extend(base_dir.rglob(pattern))
    
    print(f"📋 Found {len(all_files)} documents")
    print()
    
    successful = 0
    failed = 0
    total_chunks = 0
    
    for i, file_path in enumerate(all_files, 1):
        print(f"[{i}/{len(all_files)}] {file_path.name}...", end=" ", flush=True)
        
        success, chunks, quality = upload_document(file_path, api_url)
        
        if success and chunks > 0:
            successful += 1
            total_chunks += chunks
            print(f"✅ ({chunks} chunks, quality: {quality:.0f})")
        elif success and chunks == 0:
            print(f"⚠️  (0 chunks - document too small)")
        else:
            failed += 1
            print(f"❌ Failed")
        
        # Small delay to avoid overwhelming the API
        time.sleep(0.1)
    
    print()
    print("=" * 70)
    print("📊 Upload Summary:")
    print(f"   ✅ Successful: {successful}")
    print(f"   ❌ Failed: {failed}")
    print(f"   📝 Total Chunks in Qdrant: {total_chunks}")
    print()
    
    # Check Qdrant collection
    try:
        response = requests.get("http://localhost:6333/collections/nomad_bms_documents")
        if response.status_code == 200:
            data = response.json()
            points = data['result']['points_count']
            print(f"✅ Qdrant Collection: {points} points stored")
    except:
        pass
    
    print()
    print("🎉 Upload complete! Documents are now searchable.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
