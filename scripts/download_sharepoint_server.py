#!/usr/bin/env python3
"""
SharePoint Document Downloader - Server-side Script

Downloads documents from SharePoint using browser cookies for authentication.
Filters for files modified after 2023-12-31.

SETUP:
1. Log into SharePoint in your browser
2. Export cookies using a browser extension (e.g., "Get cookies.txt LOCALLY")
3. Save cookies to: /workspace/001-bms-agent/sharepoint_cookies.txt
4. Run this script

No complex OAuth or M365 authentication needed!
"""

import csv
import json
import time
import requests
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse, parse_qs
import http.cookiejar as cookielib

class SharePointDownloader:
    def __init__(self, cookies_file, cutoff_date='2023-12-31', output_dir='/workspace/bms_data/uploads_2024'):
        self.cookies_file = Path(cookies_file)
        self.cutoff_date = datetime.strptime(cutoff_date, '%Y-%m-%d')
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load cookies
        self.session = requests.Session()
        self.load_cookies()
        
        # Stats
        self.stats = {
            'processed': 0,
            'downloaded': 0,
            'skipped': 0,
            'errors': 0,
            'total_size': 0
        }
    
    def load_cookies(self):
        """Load cookies from Netscape format file"""
        if not self.cookies_file.exists():
            print(f"❌ Cookies file not found: {self.cookies_file}")
            print("\n📝 To create cookies file:")
            print("   1. Install browser extension: 'Get cookies.txt LOCALLY'")
            print("   2. Log into SharePoint: https://nomadrail.sharepoint.com")
            print("   3. Click the extension icon")
            print("   4. Click 'Export' and save as 'sharepoint_cookies.txt'")
            print("   5. Move file to: /workspace/001-bms-agent/")
            raise FileNotFoundError("Cookies file required")
        
        # Load cookies using cookielib
        cookie_jar = cookielib.MozillaCookieJar(str(self.cookies_file))
        try:
            cookie_jar.load(ignore_discard=True, ignore_expires=True)
            self.session.cookies = cookie_jar
            print(f"✅ Loaded {len(cookie_jar)} cookies from {self.cookies_file}")
        except Exception as e:
            print(f"❌ Error loading cookies: {e}")
            raise
    
    def extract_file_info(self, url):
        """Extract filename from SharePoint URL"""
        try:
            # Try to get filename from URL parameter
            parsed = urlparse(url)
            params = parse_qs(parsed.query)
            
            if 'file' in params:
                filename = params['file'][0]
                return filename
            
            # Fallback: extract from path
            path_parts = parsed.path.split('/')
            for part in reversed(path_parts):
                if '.' in part:
                    return part
            
            return None
        except Exception as e:
            print(f"   ⚠️  Error extracting filename: {e}")
            return None
    
    def check_file_date(self, url):
        """Check file modification date via HEAD request"""
        try:
            response = self.session.head(url, allow_redirects=True, timeout=10)
            
            if response.ok:
                last_modified = response.headers.get('Last-Modified')
                if last_modified:
                    mod_date = datetime.strptime(last_modified, '%a, %d %b %Y %H:%M:%S %Z')
                    return mod_date
            
            return None
        except Exception as e:
            return None
    
    def download_file(self, doc):
        """Download a single file"""
        try:
            filename = self.extract_file_info(doc['url'])
            if not filename:
                doc['error'] = 'Cannot extract filename'
                doc['skipped'] = True
                return False
            
            print(f"\n📄 {doc['name']}")
            print(f"   File: {filename}")
            
            # Check modification date
            mod_date = self.check_file_date(doc['url'])
            if mod_date:
                print(f"   Last Modified: {mod_date.strftime('%Y-%m-%d %H:%M:%S')}")
                
                if mod_date <= self.cutoff_date:
                    print(f"   ⏭️  SKIPPED (too old)")
                    doc['skipped'] = True
                    doc['skip_reason'] = 'too_old'
                    return False
            else:
                print(f"   ⚠️  Date unknown, downloading anyway...")
            
            # Download the file
            print(f"   ⬇️  Downloading...")
            response = self.session.get(doc['url'], allow_redirects=True, timeout=30)
            
            if not response.ok:
                raise Exception(f"HTTP {response.status_code}: {response.statusText}")
            
            # Save file
            output_path = self.output_dir / filename
            output_path.write_bytes(response.content)
            
            size_kb = len(response.content) / 1024
            print(f"   📦 Size: {size_kb:.2f} KB")
            print(f"   💾 Saved to: {output_path}")
            print(f"   ✅ DOWNLOADED")
            
            doc['downloaded'] = True
            doc['size'] = len(response.content)
            doc['output_path'] = str(output_path)
            self.stats['total_size'] += len(response.content)
            
            return True
            
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            doc['error'] = str(e)
            return False
    
    def process_documents(self, documents, delay=2, max_retries=2):
        """Process all documents"""
        print(f"\n{'═'*70}")
        print(f"Starting download process...")
        print(f"{'═'*70}")
        print(f"📋 Total documents: {len(documents)}")
        print(f"📅 Cutoff date: {self.cutoff_date.strftime('%Y-%m-%d')}")
        print(f"💾 Output directory: {self.output_dir}")
        print(f"⏱️  Delay between downloads: {delay}s")
        print(f"{'═'*70}\n")
        
        for i, doc in enumerate(documents, 1):
            print(f"\n[{i}/{len(documents)}]")
            
            # Try download with retries
            success = False
            for attempt in range(max_retries + 1):
                if attempt > 0:
                    print(f"   🔄 Retry {attempt}/{max_retries}...")
                    time.sleep(3)
                
                success = self.download_file(doc)
                if success or doc.get('skipped'):
                    break
            
            # Update stats
            self.stats['processed'] += 1
            if doc.get('downloaded'):
                self.stats['downloaded'] += 1
            elif doc.get('skipped'):
                self.stats['skipped'] += 1
            elif doc.get('error'):
                self.stats['errors'] += 1
            
            # Progress update
            if i % 10 == 0:
                print(f"\n{'─'*70}")
                print(f"📊 Progress: {self.stats['processed']}/{len(documents)} | "
                      f"✅ {self.stats['downloaded']} | "
                      f"⏭️  {self.stats['skipped']} | "
                      f"❌ {self.stats['errors']}")
                print(f"{'─'*70}")
            
            # Delay between downloads
            if i < len(documents):
                time.sleep(delay)
        
        return self.stats
    
    def print_summary(self, documents):
        """Print final summary"""
        print(f"\n{'═'*70}")
        print("🎉 DOWNLOAD COMPLETE")
        print(f"{'═'*70}")
        print(f"📊 Total Processed: {self.stats['processed']}")
        print(f"✅ Downloaded: {self.stats['downloaded']}")
        print(f"⏭️  Skipped (old): {self.stats['skipped']}")
        print(f"❌ Errors: {self.stats['errors']}")
        print(f"💾 Total Size: {self.stats['total_size'] / 1024 / 1024:.2f} MB")
        print(f"📁 Output Directory: {self.output_dir}")
        print(f"{'═'*70}")
        
        # Show errors
        errors = [d for d in documents if d.get('error') and not d.get('skipped')]
        if errors:
            print(f"\n❌ Failed Downloads ({len(errors)}):")
            for doc in errors[:10]:  # Show first 10
                print(f"   - {doc['name']}: {doc['error']}")
            if len(errors) > 10:
                print(f"   ... and {len(errors) - 10} more")
        
        # Show downloaded files
        downloaded = [d for d in documents if d.get('downloaded')]
        if downloaded:
            print(f"\n✅ Downloaded Files ({len(downloaded)}):")
            for doc in downloaded[:10]:  # Show first 10
                size_kb = doc.get('size', 0) / 1024
                print(f"   - {doc['name']} ({size_kb:.2f} KB)")
            if len(downloaded) > 10:
                print(f"   ... and {len(downloaded) - 10} more")


def load_documents_from_csv(csv_path):
    """Load documents from CSV file"""
    documents = []
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if 'URL' in row and row['URL'].startswith('http'):
                documents.append({
                    'name': row.get('Display Text', '').strip(),
                    'url': row['URL'].strip(),
                    'cell': row.get('Cell', '').strip(),
                    'downloaded': False,
                    'skipped': False,
                    'error': None
                })
    
    return documents


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Download SharePoint documents using browser cookies',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download all documents
  python download_sharepoint_server.py
  
  # Custom cutoff date
  python download_sharepoint_server.py --cutoff-date 2024-01-01
  
  # Custom output directory
  python download_sharepoint_server.py --output /path/to/output
  
  # Faster downloads (less delay)
  python download_sharepoint_server.py --delay 1
        """
    )
    
    parser.add_argument(
        '--cookies',
        default='/workspace/001-bms-agent/sharepoint_cookies.txt',
        help='Path to cookies file (default: sharepoint_cookies.txt)'
    )
    parser.add_argument(
        '--csv',
        default='/workspace/001-bms-agent/docs/bms-docs-urls.md',
        help='Path to CSV file with URLs'
    )
    parser.add_argument(
        '--cutoff-date',
        default='2023-12-31',
        help='Only download files modified after this date (YYYY-MM-DD)'
    )
    parser.add_argument(
        '--output',
        default='/workspace/bms_data/uploads_2024',
        help='Output directory for downloaded files'
    )
    parser.add_argument(
        '--delay',
        type=int,
        default=2,
        help='Delay between downloads in seconds (default: 2)'
    )
    parser.add_argument(
        '--max-retries',
        type=int,
        default=2,
        help='Maximum retry attempts for failed downloads (default: 2)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of documents to process (for testing)'
    )
    
    args = parser.parse_args()
    
    print("🚀 SharePoint Document Downloader")
    print("=" * 70)
    
    # Load documents
    print(f"\n📋 Loading documents from: {args.csv}")
    documents = load_documents_from_csv(args.csv)
    print(f"✅ Found {len(documents)} documents")
    
    # Limit for testing
    if args.limit:
        documents = documents[:args.limit]
        print(f"⚠️  Limited to first {args.limit} documents for testing")
    
    # Initialize downloader
    try:
        downloader = SharePointDownloader(
            cookies_file=args.cookies,
            cutoff_date=args.cutoff_date,
            output_dir=args.output
        )
    except FileNotFoundError:
        return 1
    
    # Process documents
    try:
        downloader.process_documents(
            documents,
            delay=args.delay,
            max_retries=args.max_retries
        )
    except KeyboardInterrupt:
        print("\n\n⚠️  Download interrupted by user")
    
    # Print summary
    downloader.print_summary(documents)
    
    # Save results
    results_file = Path(args.output) / 'download_results.json'
    with open(results_file, 'w') as f:
        json.dump({
            'stats': downloader.stats,
            'documents': documents
        }, f, indent=2)
    print(f"\n💾 Results saved to: {results_file}")
    
    return 0 if downloader.stats['errors'] == 0 else 1


if __name__ == '__main__':
    exit(main())
