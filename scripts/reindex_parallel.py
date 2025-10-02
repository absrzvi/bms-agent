#!/usr/bin/env python3
"""
Parallel Re-index Script - Upload documents to Qdrant via API with multiple workers
"""

import sys
import os
from pathlib import Path
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import time
import argparse

# Thread-safe statistics
stats_lock = Lock()
stats = {
    'processed': 0,
    'success': 0,
    'failed': 0,
    'skipped': 0,
    'updated': 0,
    'total_chunks': 0
}

def check_document_exists(filename: str, file_mtime: float) -> tuple[bool, bool]:
    """
    Check if document already exists in Qdrant by filename.
    Returns: (exists, should_update)
    - exists: True if document found in Qdrant
    - should_update: True if file is newer than stored version
    
    Note: document_name in Qdrant has UUID prefix (e.g., "uuid_filename.pdf")
    We need to search for documents where document_name ends with our filename
    """
    try:
        # Get all documents and check if any match our filename
        # (Qdrant doesn't support "ends_with" filter, so we get recent docs and check)
        response = requests.post(
            "http://localhost:6333/collections/nomad_bms_documents/points/scroll",
            json={
                "limit": 100,  # Check last 100 documents
                "with_payload": ["document_name", "processing_timestamp"]
            },
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            points = data.get('result', {}).get('points', [])
            
            # Check if any document matches our filename (ends with it)
            for point in points:
                payload = point.get('payload', {})
                doc_name = payload.get('document_name', '')
                
                # Check if document_name ends with our filename (ignoring UUID prefix)
                if doc_name.endswith(filename) or filename in doc_name:
                    # Found matching document, check if we should update
                    stored_timestamp = payload.get('processing_timestamp', '')
                    
                    if stored_timestamp:
                        try:
                            from datetime import datetime
                            stored_dt = datetime.fromisoformat(stored_timestamp.replace('Z', '+00:00'))
                            file_dt = datetime.fromtimestamp(file_mtime)
                            
                            # If file is newer, we should update
                            should_update = file_dt > stored_dt
                            return True, should_update
                        except:
                            # If timestamp parsing fails, update to be safe
                            return True, True
                    else:
                        # No timestamp stored, don't update
                        return True, False
            
            # No matching document found
            return False, False
        return False, False
    except:
        return False, False


def upload_document(filepath: str, api_url: str, worker_id: int) -> dict:
    """Upload a single document to the API with deduplication and update check"""
    filename = os.path.basename(filepath)
    file_mtime = os.path.getmtime(filepath)
    
    result = {
        'file': filepath,
        'filename': filename,
        'worker_id': worker_id,
        'success': False,
        'chunks': 0,
        'error': None,
        'skipped': False,
        'updated': False
    }
    
    try:
        # Check if document already exists and if it needs updating
        exists, should_update = check_document_exists(filename, file_mtime)
        
        if exists and not should_update:
            result['skipped'] = True
            result['error'] = 'Document already exists (no update needed)'
            return result
        
        if exists and should_update:
            result['updated'] = True
        
        with open(filepath, 'rb') as f:
            files = {'file': (filename, f)}
            response = requests.post(
                f"{api_url}/api/v1/documents/upload",
                files=files,
                timeout=300  # 5 minutes for large files
            )
            
            if response.status_code == 200:
                data = response.json()
                result['success'] = True
                result['document_id'] = data.get('document_id')
                
                # Extract processing result data
                processing_result = data.get('processing_result', {})
                result['chunks'] = processing_result.get('chunks_created', 0)
                result['quality_score'] = processing_result.get('quality_score', 0)
            else:
                result['error'] = f"HTTP {response.status_code}: {response.text[:200]}"
    
    except Exception as e:
        result['error'] = str(e)
    
    return result


def update_stats(result: dict):
    """Update global statistics (thread-safe)"""
    with stats_lock:
        stats['processed'] += 1
        
        if result.get('skipped'):
            stats['skipped'] += 1
        elif result['success']:
            stats['success'] += 1
            stats['total_chunks'] += result.get('chunks', 0)
            if result.get('updated'):
                stats['updated'] += 1
        else:
            stats['failed'] += 1


def get_qdrant_count():
    """Get current point count from Qdrant"""
    try:
        response = requests.get("http://localhost:6333/collections/nomad_bms_documents", timeout=2)
        data = response.json()
        return data.get('result', {}).get('points_count', 0)
    except:
        return 0


def print_progress(current: int, total: int):
    """Print progress update with Qdrant count"""
    with stats_lock:
        pct = (current / total * 100) if total > 0 else 0
        qdrant_count = get_qdrant_count()
        print(f"\r[{current}/{total}] {pct:.1f}% | "
              f"✅ {stats['success']} | "
              f"⏭️  {stats['skipped']} | "
              f"❌ {stats['failed']} | "
              f"📦 {stats['total_chunks']} chunks | "
              f"🗄️  {qdrant_count} in Qdrant", end='', flush=True)


def main():
    parser = argparse.ArgumentParser(description="Parallel document upload to Qdrant")
    parser.add_argument(
        '--input-dir',
        default='/workspace/bms_data/incoming',
        help='Directory with documents to upload'
    )
    parser.add_argument(
        '--api-url',
        default='http://localhost:8000',
        help='API base URL'
    )
    parser.add_argument(
        '--workers',
        type=int,
        default=50,
        help='Number of parallel workers (default: 50)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of documents to process (for testing)'
    )
    
    args = parser.parse_args()
    
    api_url = args.api_url
    upload_dir = args.input_dir
    
    print("🚀 Parallel Document Upload to Qdrant")
    print("=" * 70)
    
    # Check API is available
    try:
        response = requests.get(f"{api_url}/health", timeout=5)
        if response.status_code != 200:
            print(f"❌ API not responding at {api_url}")
            sys.exit(1)
        print(f"✅ API is healthy: {api_url}")
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        sys.exit(1)
    
    # Get all documents (recursive search)
    patterns = ["*.pdf", "*.docx", "*.doc", "*.xlsx", "*.xls", "*.pptx", "*.ppt", "*.csv", "*.txt", "*.md"]
    all_files = []
    upload_path = Path(upload_dir)
    
    for pattern in patterns:
        all_files.extend(upload_path.rglob(pattern))
    
    all_files = [str(f) for f in all_files]
    
    print(f"📁 Found {len(all_files)} documents to process")
    print(f"   Location: {upload_dir}")
    
    if len(all_files) == 0:
        print("⚠️  No documents found")
        return 0
    
    # Show file type breakdown
    type_counts = {}
    for filepath in all_files:
        ext = Path(filepath).suffix.lower().lstrip('.')
        type_counts[ext] = type_counts.get(ext, 0) + 1
    
    print(f"\n📂 Documents by Type:")
    for file_type, count in sorted(type_counts.items()):
        print(f"   {file_type}: {count}")
    
    # Limit for testing
    if args.limit:
        all_files = all_files[:args.limit]
        print(f"\n⚠️  Limited to first {args.limit} documents for testing")
    
    print(f"\n⚙️  Configuration:")
    print(f"   Workers: {args.workers}")
    print(f"   API: {api_url}")
    
    print(f"\n{'═'*70}")
    print(f"Starting parallel upload...")
    print(f"{'═'*70}\n")
    
    start_time = time.time()
    results = []
    
    # Process documents in parallel
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        # Submit all tasks
        futures = {
            executor.submit(
                upload_document,
                filepath,
                api_url,
                i % args.workers
            ): filepath for i, filepath in enumerate(all_files)
        }
        
        # Collect results as they complete
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            update_stats(result)
            print_progress(len(results), len(all_files))
    
    elapsed = time.time() - start_time
    
    # Print final summary
    print(f"\n\n{'═'*70}")
    print(f"🎉 UPLOAD COMPLETE")
    print(f"{'═'*70}")
    print(f"⏱️  Time: {elapsed:.1f}s ({len(all_files)/elapsed:.2f} docs/sec)")
    print(f"📊 Total Processed: {stats['processed']}")
    print(f"✅ Success: {stats['success']} ({stats['updated']} updated)")
    print(f"⏭️  Skipped (duplicates): {stats['skipped']}")
    print(f"❌ Failed: {stats['failed']}")
    print(f"📦 Total Chunks: {stats['total_chunks']}")
    print(f"{'═'*70}")
    
    # Show failed documents if any
    failed_docs = [r for r in results if not r['success']]
    if failed_docs:
        print(f"\n❌ Failed Documents ({len(failed_docs)}):")
        for doc in failed_docs[:20]:  # Show first 20
            print(f"   - {doc['filename']}: {doc['error']}")
        if len(failed_docs) > 20:
            print(f"   ... and {len(failed_docs) - 20} more")
    
    # Check final count in Qdrant
    try:
        response = requests.get(f"http://localhost:6333/collections/nomad_bms_documents")
        data = response.json()
        points = data.get('result', {}).get('points_count', 0)
        print(f"\n📊 Total points in Qdrant: {points}")
    except:
        pass
    
    # Save detailed results
    import json
    results_file = Path(upload_dir).parent / 'upload_results.json'
    with open(results_file, 'w') as f:
        json.dump({
            'stats': stats,
            'elapsed_seconds': elapsed,
            'workers': args.workers,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'results': results
        }, f, indent=2)
    
    print(f"💾 Detailed results saved to: {results_file}")
    
    sys.exit(0 if stats['failed'] == 0 else 0)  # Don't fail on errors, just report


if __name__ == "__main__":
    main()
