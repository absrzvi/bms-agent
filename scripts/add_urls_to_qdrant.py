#!/usr/bin/env python3
"""
Add Document URLs to Qdrant Chunks
Matches URLs from bms-docs-urls.md to chunks in Qdrant and adds document_url field
"""

import csv
import requests
import re
from pathlib import Path
from collections import defaultdict

# Configuration
QDRANT_URL = "http://localhost:6333"
COLLECTION_NAME = "nomad_bms_documents"
URLS_FILE = "/workspace/001-bms-agent/docs/bms-docs-urls.md"

def parse_urls_file():
    """Parse the bms-docs-urls.md file to extract document names and URLs"""
    url_mapping = {}
    
    with open(URLS_FILE, 'r', encoding='utf-8') as f:
        # Skip header
        next(f)
        
        for line in f:
            parts = line.strip().split(',')
            if len(parts) >= 4:
                # Format: Sheet,Cell,Display Text,URL,Type
                # Extract display text (document name) and URL
                display_text = parts[2]
                url = parts[3]
                
                # Clean up display text
                display_text = display_text.strip()
                url = url.strip()
                
                if display_text and url and url.startswith('http'):
                    url_mapping[display_text] = url
    
    print(f"✅ Parsed {len(url_mapping)} URLs from file")
    return url_mapping

def extract_document_code(text):
    """Extract BMS document code (e.g., BMS-HUMR-FOR-029) from text"""
    match = re.search(r'(BMS-[A-Z]{4}-[A-Z]{3}-\d{3})', text, re.IGNORECASE)
    if match:
        return match.group(1).upper()
    return None

def match_url_to_document(doc_name, doc_id, url_mapping):
    """Try to match a document to a URL using various strategies"""
    
    # Strategy 1: Direct match by document name (without extension)
    doc_name_clean = doc_name.replace('.pdf', '').replace('.xlsx', '').replace('.docx', '').replace('.pptx', '')
    for url_name, url in url_mapping.items():
        if doc_name_clean.lower() in url_name.lower() or url_name.lower() in doc_name_clean.lower():
            return url
    
    # Strategy 2: Match by document code
    doc_code = extract_document_code(doc_name) or extract_document_code(doc_id)
    if doc_code:
        for url_name, url in url_mapping.items():
            if doc_code in url_name or doc_code in url:
                return url
    
    # Strategy 3: Fuzzy match by document ID
    for url_name, url in url_mapping.items():
        if doc_id.lower() in url_name.lower():
            return url
    
    return None

def get_all_points():
    """Retrieve all points from Qdrant collection"""
    all_points = []
    offset = None
    
    while True:
        payload = {
            "limit": 100,
            "with_payload": True,
            "with_vector": False
        }
        
        if offset:
            payload["offset"] = offset
        
        response = requests.post(
            f"{QDRANT_URL}/collections/{COLLECTION_NAME}/points/scroll",
            json=payload
        )
        
        if response.status_code != 200:
            print(f"❌ Error fetching points: {response.status_code}")
            break
        
        data = response.json()
        points = data.get('result', {}).get('points', [])
        
        if not points:
            break
        
        all_points.extend(points)
        
        # Get next offset
        next_offset = data.get('result', {}).get('next_page_offset')
        if not next_offset:
            break
        offset = next_offset
    
    print(f"✅ Retrieved {len(all_points)} points from Qdrant")
    return all_points

def update_points_with_urls(points, url_mapping):
    """Match points to URLs and update them in Qdrant"""
    
    # Group points by document to minimize updates
    doc_to_points = defaultdict(list)
    for point in points:
        doc_name = point['payload'].get('document_name', '')
        doc_to_points[doc_name].append(point)
    
    print(f"\n📊 Found {len(doc_to_points)} unique documents")
    
    matched = 0
    unmatched = 0
    updated_points = 0
    
    # Match URLs
    doc_url_map = {}
    for doc_name in doc_to_points.keys():
        doc_id = doc_to_points[doc_name][0]['payload'].get('document_id', '')
        url = match_url_to_document(doc_name, doc_id, url_mapping)
        
        if url:
            doc_url_map[doc_name] = url
            matched += 1
        else:
            unmatched += 1
    
    print(f"\n✅ Matched URLs: {matched}/{len(doc_to_points)} documents ({matched/len(doc_to_points)*100:.1f}%)")
    print(f"❌ Unmatched: {unmatched} documents")
    
    # Update points by document (all points for a document get the same URL)
    print(f"\n🔄 Updating points in Qdrant...")
    
    for doc_name, points_list in doc_to_points.items():
        url = doc_url_map.get(doc_name)
        if not url:
            continue
        
        # Get all point IDs for this document
        point_ids = [p['id'] for p in points_list]
        
        # Update all points for this document with the same URL
        response = requests.post(
            f"{QDRANT_URL}/collections/{COLLECTION_NAME}/points/payload",
            json={"points": point_ids, "payload": {"document_url": url}}
        )
        
        if response.status_code == 200:
            updated_points += len(point_ids)
            print(f"  ✅ Updated {updated_points} points ({len(doc_url_map)} docs)...", end='\r')
        else:
            print(f"\n  ❌ Error updating {doc_name}: {response.status_code} - {response.text[:100]}")
    
    print(f"\n✅ Updated {updated_points} points with URLs")
    
    return matched, unmatched, updated_points

def show_sample_matches(points, url_mapping, limit=5):
    """Show sample URL matches for verification"""
    print(f"\n📋 Sample URL Matches (first {limit}):")
    print("="*80)
    
    shown = 0
    for point in points:
        if shown >= limit:
            break
        
        doc_name = point['payload'].get('document_name', '')
        doc_id = point['payload'].get('document_id', '')
        url = match_url_to_document(doc_name, doc_id, url_mapping)
        
        if url:
            print(f"\nDocument: {doc_name}")
            print(f"ID: {doc_id}")
            print(f"URL: {url[:80]}...")
            shown += 1
    
    print("="*80)

def verify_updates():
    """Verify that URLs were added successfully"""
    response = requests.post(
        f"{QDRANT_URL}/collections/{COLLECTION_NAME}/points/scroll",
        json={"limit": 5, "with_payload": True, "with_vector": False}
    )
    
    if response.status_code == 200:
        data = response.json()
        points = data.get('result', {}).get('points', [])
        
        print(f"\n🔍 Verification - Checking first 5 points:")
        print("="*80)
        
        for point in points:
            doc_name = point['payload'].get('document_name', 'N/A')
            has_url = 'document_url' in point['payload']
            url = point['payload'].get('document_url', 'N/A')[:60] if has_url else 'N/A'
            
            status = "✅" if has_url else "❌"
            print(f"{status} {doc_name}")
            if has_url:
                print(f"   URL: {url}...")
        
        print("="*80)

def main():
    print("="*80)
    print("🔗 Adding Document URLs to Qdrant")
    print("="*80)
    
    # Parse URLs file
    url_mapping = parse_urls_file()
    
    # Get all points from Qdrant
    points = get_all_points()
    
    if not points:
        print("❌ No points found in Qdrant")
        return
    
    # Show sample matches
    show_sample_matches(points, url_mapping)
    
    # Ask for confirmation
    print(f"\n⚠️  About to update {len(points)} points in Qdrant")
    response = input("Continue? (yes/no): ")
    
    if response.lower() != 'yes':
        print("❌ Aborted by user")
        return
    
    # Update points with URLs
    matched, unmatched, updated = update_points_with_urls(points, url_mapping)
    
    # Verify updates
    verify_updates()
    
    # Summary
    print(f"\n{'='*80}")
    print("📊 SUMMARY")
    print("="*80)
    print(f"URLs in file: {len(url_mapping)}")
    print(f"Documents matched: {matched}")
    print(f"Documents unmatched: {unmatched}")
    print(f"Points updated: {updated}")
    print(f"Match rate: {matched/(matched+unmatched)*100:.1f}%")
    print("="*80)
    
    if unmatched > 0:
        print(f"\n💡 TIP: {unmatched} documents couldn't be matched.")
        print("   This is normal if the URLs file doesn't cover all documents.")

if __name__ == "__main__":
    main()
