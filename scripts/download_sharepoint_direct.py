#!/usr/bin/env python3
"""
Direct SharePoint Document Downloader with proper URL handling
Converts Office Online URLs to direct download URLs
"""

import json
import requests
import argparse
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse, parse_qs, unquote
import http.cookiejar as cookielib
from typing import Dict, Optional

def load_cookies(cookies_file: Path) -> requests.Session:
    """Load cookies into a session"""
    session = requests.Session()
    cookie_jar = cookielib.MozillaCookieJar(str(cookies_file))
    try:
        cookie_jar.load(ignore_discard=True, ignore_expires=True)
        session.cookies = cookie_jar
        # Add headers to mimic browser
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        return session
    except Exception as e:
        raise Exception(f"Error loading cookies: {e}")


def convert_to_download_url(url: str) -> tuple[str, str]:
    """Convert SharePoint Office Online URL to direct download URL"""
    
    parsed = urlparse(url)
    
    # Check if it's an Office Online URL (/:x:/, /:p:/, /:w:/ or Doc.aspx)
    if '/_layouts/15/Doc.aspx' in url or '/:x:/' in url or '/:p:/' in url or '/:w:/' in url:
        params = parse_qs(parsed.query)
        
        # Extract filename from 'file' parameter
        if 'file' in params:
            filename = unquote(params['file'][0])
        else:
            filename = 'unknown'
        
        # For Office Online URLs, we need to construct a direct library path
        # The file parameter gives us the filename, but we need the full path
        # Since all files seem to be in /qms/ we'll try that base path
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        
        # Try to extract path from the URL structure
        # Office Online URLs don't contain the full path, so we'll use the filename
        # and try common SharePoint library paths
        encoded_filename = filename.replace(' ', '%20')
        
        # Try multiple common paths
        possible_paths = [
            f"{base_url}/qms/BMS%20System/{encoded_filename}",
            f"{base_url}/qms/{encoded_filename}",
        ]
        
        # For now, return the first path and the filename
        # The download function will handle redirects
        download_url = possible_paths[0]
        return download_url, filename
    
    # If it's already a direct library URL (contains /qms/BMS System/)
    # Extract filename from path
    path_parts = unquote(parsed.path).split('/')
    filename = path_parts[-1].split('?')[0] if path_parts else 'unknown'
    
    # Remove query parameters for cleaner filename
    if '?' in filename:
        filename = filename.split('?')[0]
    
    # For direct library URLs, return as-is
    return url, filename


def download_document(url: str, session: requests.Session, output_dir: Path) -> Dict:
    """Download a single document"""
    result = {
        'url': url,
        'downloaded': False,
        'error': None
    }
    
    try:
        # Convert to download URL
        download_url, filename = convert_to_download_url(url)
        result['filename'] = filename
        result['download_url'] = download_url
        
        print(f"  Downloading: {filename}")
        print(f"  URL: {download_url[:80]}...")
        
        # Download the file
        response = session.get(download_url, allow_redirects=True, timeout=60)
        
        if not response.ok:
            result['error'] = f"HTTP {response.status_code}"
            return result
        
        # Check if we got HTML instead of binary content
        content_type = response.headers.get('Content-Type', '')
        if 'text/html' in content_type and len(response.content) < 500000:
            # Likely an error page
            result['error'] = 'Received HTML instead of document (authentication issue)'
            return result
        
        # Determine file type and create directory
        ext = Path(filename).suffix.lower().lstrip('.')
        if ext in ['pdf', 'docx', 'xlsx', 'pptx', 'doc', 'xls', 'ppt', 'csv', 'txt']:
            file_type = ext
        else:
            file_type = 'other'
        
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
        
        print(f"  ✅ Downloaded: {len(response.content)} bytes")
        
        return result
        
    except Exception as e:
        result['error'] = str(e)
        print(f"  ❌ Error: {e}")
        return result


def main():
    parser = argparse.ArgumentParser(description='Direct SharePoint document downloader')
    parser.add_argument('--cookies', default='/workspace/001-bms-agent/sharepoint_cookies_netscape.txt')
    parser.add_argument('--output', default='/workspace/bms_data/incoming_fixed')
    parser.add_argument('--test', action='store_true', help='Test with first 5 URLs only')
    args = parser.parse_args()
    
    cookies_file = Path(args.cookies)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("🚀 Direct SharePoint Document Downloader")
    print("=" * 70)
    
    # Load cookies
    print(f"\n📝 Loading cookies from: {cookies_file}")
    session = load_cookies(cookies_file)
    print(f"✅ Loaded {len(session.cookies)} cookies")
    
    # Load URLs from CSV
    csv_file = Path('/workspace/001-bms-agent/docs/bms-docs-urls.md')
    print(f"\n📋 Loading URLs from: {csv_file}")
    
    import csv
    urls = []
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('URL'):
                urls.append(row['URL'])
    
    print(f"✅ Found {len(urls)} URLs")
    
    if args.test:
        urls = urls[:5]
        print(f"⚠️  TEST MODE: Processing first 5 URLs only")
    
    # Download documents
    print(f"\n{'='*70}")
    print(f"Starting downloads...")
    print(f"{'='*70}\n")
    
    results = []
    successful = 0
    failed = 0
    
    for i, url in enumerate(urls, 1):
        print(f"[{i}/{len(urls)}]")
        result = download_document(url, session, output_dir)
        results.append(result)
        
        if result['downloaded']:
            successful += 1
        else:
            failed += 1
        
        print()
    
    # Summary
    print(f"{'='*70}")
    print(f"📊 DOWNLOAD SUMMARY:")
    print(f"   Total URLs: {len(urls)}")
    print(f"   ✅ Successful: {successful}")
    print(f"   ❌ Failed: {failed}")
    print(f"   📁 Output: {output_dir}")
    print(f"{'='*70}")
    
    # Save results
    results_file = output_dir / 'download_results.json'
    with open(results_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'total': len(urls),
            'successful': successful,
            'failed': failed,
            'results': results
        }, f, indent=2)
    
    print(f"\n💾 Results saved to: {results_file}")
    
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    exit(main())
