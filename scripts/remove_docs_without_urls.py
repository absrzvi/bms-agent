#!/usr/bin/env python3
"""
Remove documents without URLs from Qdrant
Identifies and deletes all points that don't have a document_url field
"""

import requests
from collections import defaultdict

QDRANT_URL = "http://localhost:6333"
COLLECTION_NAME = "nomad_bms_documents"

def get_all_points():
    """Retrieve all points from Qdrant collection"""
    all_points = []
    offset = None
    
    print("📥 Fetching all points from Qdrant...")
    
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
        print(f"  Retrieved {len(all_points)} points...", end='\r')
        
        # Get next offset
        next_offset = data.get('result', {}).get('next_page_offset')
        if not next_offset:
            break
        offset = next_offset
    
    print(f"\n✅ Retrieved {len(all_points)} total points")
    return all_points

def identify_docs_without_urls(points):
    """Group points by document and identify which don't have URLs"""
    
    doc_to_points = defaultdict(list)
    for point in points:
        doc_name = point['payload'].get('document_name', '')
        doc_to_points[doc_name].append(point)
    
    docs_with_urls = set()
    docs_without_urls = set()
    
    for doc_name, points_list in doc_to_points.items():
        # Check first point of document for URL
        has_url = 'document_url' in points_list[0]['payload']
        
        if has_url:
            docs_with_urls.add(doc_name)
        else:
            docs_without_urls.add(doc_name)
    
    return docs_with_urls, docs_without_urls, doc_to_points

def show_docs_without_urls(docs_without_urls):
    """Display documents that will be removed"""
    print(f"\n📋 Documents WITHOUT URLs ({len(docs_without_urls)}):")
    print("="*80)
    
    for i, doc_name in enumerate(sorted(docs_without_urls)[:20], 1):
        print(f"{i}. {doc_name}")
    
    if len(docs_without_urls) > 20:
        print(f"... and {len(docs_without_urls) - 20} more")
    
    print("="*80)

def delete_points(point_ids, batch_size=100):
    """Delete points from Qdrant in batches"""
    
    total_deleted = 0
    
    for i in range(0, len(point_ids), batch_size):
        batch = point_ids[i:i+batch_size]
        
        response = requests.post(
            f"{QDRANT_URL}/collections/{COLLECTION_NAME}/points/delete",
            json={"points": batch}
        )
        
        if response.status_code == 200:
            total_deleted += len(batch)
            print(f"  🗑️  Deleted {total_deleted}/{len(point_ids)} points...", end='\r')
        else:
            print(f"\n  ❌ Error deleting batch: {response.status_code}")
    
    print(f"\n✅ Deleted {total_deleted} points")
    return total_deleted

def main():
    print("="*80)
    print("🗑️  Remove Documents Without URLs from Qdrant")
    print("="*80)
    
    # Get all points
    points = get_all_points()
    
    if not points:
        print("❌ No points found in Qdrant")
        return
    
    # Identify docs without URLs
    docs_with_urls, docs_without_urls, doc_to_points = identify_docs_without_urls(points)
    
    print(f"\n📊 ANALYSIS:")
    print(f"   Total documents: {len(doc_to_points)}")
    print(f"   ✅ With URLs: {len(docs_with_urls)} documents")
    print(f"   ❌ Without URLs: {len(docs_without_urls)} documents")
    
    if not docs_without_urls:
        print("\n✅ All documents have URLs! Nothing to remove.")
        return
    
    # Show which docs will be removed
    show_docs_without_urls(docs_without_urls)
    
    # Count points to be deleted
    points_to_delete = []
    for doc_name in docs_without_urls:
        for point in doc_to_points[doc_name]:
            points_to_delete.append(point['id'])
    
    print(f"\n⚠️  DELETION PLAN:")
    print(f"   Documents to remove: {len(docs_without_urls)}")
    print(f"   Points to delete: {len(points_to_delete)}")
    print(f"   Documents to keep: {len(docs_with_urls)}")
    
    # Ask for confirmation
    print(f"\n⚠️  WARNING: This will permanently delete {len(points_to_delete)} points from Qdrant!")
    response = input("Type 'DELETE' to confirm: ")
    
    if response != 'DELETE':
        print("❌ Deletion cancelled")
        return
    
    # Delete points
    print(f"\n🗑️  Deleting points...")
    deleted_count = delete_points(points_to_delete)
    
    # Verify deletion
    print(f"\n🔍 Verifying deletion...")
    remaining_points = get_all_points()
    
    remaining_docs_with_urls, remaining_docs_without_urls, _ = identify_docs_without_urls(remaining_points)
    
    print(f"\n{'='*80}")
    print("📊 FINAL SUMMARY")
    print("="*80)
    print(f"Initial points: {len(points)}")
    print(f"Points deleted: {deleted_count}")
    print(f"Remaining points: {len(remaining_points)}")
    print(f"Documents remaining: {len(remaining_docs_with_urls) + len(remaining_docs_without_urls)}")
    print(f"   ✅ With URLs: {len(remaining_docs_with_urls)}")
    print(f"   ❌ Without URLs: {len(remaining_docs_without_urls)}")
    
    if len(remaining_docs_without_urls) == 0:
        print("\n✅ SUCCESS: All remaining documents have URLs!")
    else:
        print(f"\n⚠️  WARNING: {len(remaining_docs_without_urls)} documents still without URLs")
    
    print("="*80)

if __name__ == "__main__":
    main()
