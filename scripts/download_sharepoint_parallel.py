#!/usr/bin/env python3
"""
Parallel SharePoint Document Downloader

Downloads documents from SharePoint using multiple worker processes for speed.
Uses cookie-based authentication and organizes files by type.

Usage:
    python download_sharepoint_parallel.py --workers 10 --limit 100
"""

import json
import time
import requests
import argparse
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse, parse_qs
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import http.cookiejar as cookielib
from typing import Dict, List, Optional

# Thread-safe statistics
stats_lock = Lock()
stats = {
    'processed': 0,
    'downloaded': 0,
    'skipped': 0,
    'errors': 0,
    'total_size': 0
}


def load_cookies(cookies_file: Path) -> requests.Session:
    """Load cookies into a session"""
    session = requests.Session()
    cookie_jar = cookielib.MozillaCookieJar(str(cookies_file))
    try:
        cookie_jar.load(ignore_discard=True, ignore_expires=True)
        session.cookies = cookie_jar
        return session
    except Exception as e:
        raise Exception(f"Error loading cookies: {e}")


def load_documents_from_csv(csv_file: Path) -> List[Dict]:
    """Load document URLs from CSV file"""
    import csv
    documents = []
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('URL'):
                documents.append({
                    'name': row.get('Display Text', 'Unknown'),
                    'url': row['URL'],
                    'type': row.get('Type', 'Unknown')
                })
    
    return documents


def extract_filename(url: str) -> Optional[str]:
    """Extract filename from SharePoint URL"""
    try:
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        
        if 'file' in params:
            return params['file'][0]
        
        # Fallback: extract from path
        path_parts = parsed.path.split('/')
        for part in reversed(path_parts):
            if '.' in part:
                return part
        
        return None
    except Exception:
        return None


def get_file_type(filename: str) -> str:
    """Get file type from filename"""
    ext = Path(filename).suffix.lower().lstrip('.')
    
    # Normalize extensions
    if ext in ['doc', 'docx']:
        return 'docx'
    elif ext in ['xls', 'xlsx']:
        return 'xlsx'
    elif ext in ['ppt', 'pptx']:
        return 'pptx'
    elif ext in ['pdf', 'csv', 'txt', 'md']:
        return ext
    else:
        return 'other'


def check_file_date(session: requests.Session, url: str, cutoff_date: datetime) -> tuple[bool, Optional[datetime]]:
    """Check if file should be downloaded based on modification date"""
    try:
        response = session.head(url, allow_redirects=True, timeout=10)
        
        if response.ok:
            last_modified = response.headers.get('Last-Modified')
            if last_modified:
                mod_date = datetime.strptime(last_modified, '%a, %d %b %Y %H:%M:%S %Z')
                
                if mod_date <= cutoff_date:
                    return False, mod_date  # Too old, skip
                else:
                    return True, mod_date  # Download
        
        # If no date info, download anyway
        return True, None
    except Exception:
        return True, None  # Download on error


def download_document(doc: Dict, cookies_file: Path, output_dir: Path, cutoff_date: datetime, worker_id: int) -> Dict:
    """Download a single document (worker function)"""
    result = doc.copy()
    result['worker_id'] = worker_id
    result['downloaded'] = False
    result['skipped'] = False
    result['error'] = None
    
    try:
        # Create session for this worker
        session = load_cookies(cookies_file)
        
        # Extract filename
        filename = extract_filename(doc['url'])
        if not filename:
            result['error'] = 'Cannot extract filename'
            result['skipped'] = True
            return result
        
        result['filename'] = filename
        
        # Check modification date
        should_download, mod_date = check_file_date(session, doc['url'], cutoff_date)
        
        if mod_date:
            result['mod_date'] = mod_date.isoformat()
        
        if not should_download:
            result['skipped'] = True
            result['skip_reason'] = 'too_old'
            return result
        
        # Download the file
        response = session.get(doc['url'], allow_redirects=True, timeout=30)
        
        if not response.ok:
            result['error'] = f"HTTP {response.status_code}"
            return result
        
        # Organize by file type
        file_type = get_file_type(filename)
        type_dir = output_dir / file_type
        type_dir.mkdir(parents=True, exist_ok=True)
        
        # Save file
        output_path = type_dir / filename
        
        # Handle duplicates
        if output_path.exists():
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            stem = output_path.stem
            suffix = output_path.suffix
            output_path = type_dir / f"{stem}_{timestamp}{suffix}"
        
        output_path.write_bytes(response.content)
        
        result['downloaded'] = True
        result['size'] = len(response.content)
        result['output_path'] = str(output_path)
        result['file_type'] = file_type
        
        return result
        
    except Exception as e:
        result['error'] = str(e)
        return result


def update_stats(result: Dict):
    """Update global statistics (thread-safe)"""
    with stats_lock:
        stats['processed'] += 1
        
        if result.get('downloaded'):
            stats['downloaded'] += 1
            stats['total_size'] += result.get('size', 0)
        elif result.get('skipped'):
            stats['skipped'] += 1
        elif result.get('error'):
            stats['errors'] += 1


def print_progress(current: int, total: int):
    """Print progress update"""
    with stats_lock:
        pct = (current / total * 100) if total > 0 else 0
        print(f"\r[{current}/{total}] {pct:.1f}% | "
              f"✅ {stats['downloaded']} | "
              f"⏭️  {stats['skipped']} | "
              f"❌ {stats['errors']} | "
              f"💾 {stats['total_size']/1024/1024:.1f} MB", end='', flush=True)


def main():
    parser = argparse.ArgumentParser(
        description='Parallel SharePoint document downloader'
    )
    parser.add_argument(
        '--cookies',
        default='/workspace/001-bms-agent/sharepoint_cookies_netscape.txt',
        help='Path to cookies file (Netscape format)'
    )
    parser.add_argument(
        '--csv',
        default='/workspace/001-bms-agent/docs/bms-docs-urls.md',
        help='Path to CSV file with URLs'
    )
    parser.add_argument(
        '--output',
        default='/workspace/bms_data/incoming',
        help='Output directory for downloaded files'
    )
    parser.add_argument(
        '--cutoff-date',
        default='2023-12-31',
        help='Only download files modified after this date (YYYY-MM-DD)'
    )
    parser.add_argument(
        '--workers',
        type=int,
        default=10,
        help='Number of parallel workers (default: 10)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of documents to process (for testing)'
    )
    
    args = parser.parse_args()
    
    # Parse cutoff date
    cutoff_date = datetime.strptime(args.cutoff_date, '%Y-%m-%d')
    
    # Setup paths
    cookies_file = Path(args.cookies)
    csv_file = Path(args.csv)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("🚀 Parallel SharePoint Document Downloader")
    print("=" * 70)
    
    # Validate cookies
    if not cookies_file.exists():
        print(f"❌ Cookies file not found: {cookies_file}")
        return 1
    
    # Load documents
    print(f"\n📋 Loading documents from: {csv_file}")
    documents = load_documents_from_csv(csv_file)
    print(f"✅ Found {len(documents)} documents")
    
    # Limit for testing
    if args.limit:
        documents = documents[:args.limit]
        print(f"⚠️  Limited to first {args.limit} documents for testing")
    
    print(f"\n⚙️  Configuration:")
    print(f"   Workers: {args.workers}")
    print(f"   Cutoff date: {args.cutoff_date}")
    print(f"   Output: {output_dir}")
    print(f"   Cookies: {len(load_cookies(cookies_file).cookies)} loaded")
    
    print(f"\n{'═'*70}")
    print(f"Starting parallel download...")
    print(f"{'═'*70}\n")
    
    start_time = time.time()
    results = []
    
    # Process documents in parallel
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        # Submit all tasks
        futures = {
            executor.submit(
                download_document,
                doc,
                cookies_file,
                output_dir,
                cutoff_date,
                i % args.workers
            ): doc for i, doc in enumerate(documents)
        }
        
        # Collect results as they complete
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            update_stats(result)
            print_progress(len(results), len(documents))
    
    elapsed = time.time() - start_time
    
    # Print final summary
    print(f"\n\n{'═'*70}")
    print(f"🎉 DOWNLOAD COMPLETE")
    print(f"{'═'*70}")
    print(f"⏱️  Time: {elapsed:.1f}s ({len(documents)/elapsed:.1f} docs/sec)")
    print(f"📊 Total Processed: {stats['processed']}")
    print(f"✅ Downloaded: {stats['downloaded']}")
    print(f"⏭️  Skipped (old): {stats['skipped']}")
    print(f"❌ Errors: {stats['errors']}")
    print(f"💾 Total Size: {stats['total_size']/1024/1024:.2f} MB")
    print(f"📁 Output Directory: {output_dir}")
    print(f"{'═'*70}")
    
    # Show file type breakdown
    type_counts = {}
    for result in results:
        if result.get('downloaded'):
            file_type = result.get('file_type', 'unknown')
            type_counts[file_type] = type_counts.get(file_type, 0) + 1
    
    if type_counts:
        print(f"\n📂 Files by Type:")
        for file_type, count in sorted(type_counts.items()):
            print(f"   {file_type}: {count}")
    
    # Show errors if any
    errors = [r for r in results if r.get('error')]
    if errors:
        print(f"\n❌ Errors ({len(errors)}):")
        for err in errors[:10]:  # Show first 10
            print(f"   - {err['name']}: {err['error']}")
        if len(errors) > 10:
            print(f"   ... and {len(errors) - 10} more")
    
    # Save detailed results
    results_file = output_dir / 'download_results.json'
    with open(results_file, 'w') as f:
        json.dump({
            'stats': stats,
            'elapsed_seconds': elapsed,
            'workers': args.workers,
            'cutoff_date': args.cutoff_date,
            'timestamp': datetime.now().isoformat(),
            'results': results
        }, f, indent=2)
    
    print(f"\n💾 Detailed results saved to: {results_file}")
    
    return 0 if stats['errors'] == 0 else 1


if __name__ == '__main__':
    exit(main())
