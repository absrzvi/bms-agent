#!/usr/bin/env python3
"""
Update Quality Scores for Existing Documents in Qdrant
Calculates quality scores without re-processing documents
"""

import sys
from pathlib import Path
from typing import Dict, List
import time

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, UpdateStatus

def calculate_quality_score(content: str, metadata: Dict) -> float:
    """
    Calculate quality score based on content characteristics
    Mimics RAGAS quality metrics without full re-processing
    """
    if not content:
        return 0.0
    
    score = 0.0
    max_score = 10.0
    
    # 1. Length check (1 point)
    if len(content) >= 100:
        score += 1.0
    elif len(content) >= 50:
        score += 0.5
    
    # 2. No fragmentation (2 points)
    if not any(frag in content.lower() for frag in ['...', '…', '..', 'page', 'section']):
        score += 2.0
    elif content.count('.') > 2:  # Has sentences
        score += 1.0
    
    # 3. Proper capitalization (1 point)
    words = content.split()
    if words and any(w[0].isupper() for w in words if w):
        score += 1.0
    
    # 4. No excessive whitespace (1 point)
    if '   ' not in content and '\n\n\n' not in content:
        score += 1.0
    
    # 5. Has context (1 point)
    if metadata.get('has_context', False) or '<context>' in content:
        score += 1.0
    
    # 6. Good chunk size (1 point)
    chunk_size = len(content)
    if 500 <= chunk_size <= 3000:
        score += 1.0
    elif 200 <= chunk_size <= 4000:
        score += 0.5
    
    # 7. Processing version (1 point)
    if metadata.get('processing_version') == 'v4.0_enhanced':
        score += 1.0
    
    # 8. Sentence structure (1 point)
    sentence_endings = content.count('.') + content.count('!') + content.count('?')
    if sentence_endings >= 2:
        score += 1.0
    elif sentence_endings >= 1:
        score += 0.5
    
    # 9. No artifacts (1 point)
    artifacts = ['NaN', 'Unnamed', 'null', 'undefined', '###', '***']
    if not any(art in content for art in artifacts):
        score += 1.0
    
    # Normalize to 0-1 range
    normalized_score = score / max_score
    
    # Adjust based on document type
    doc_type = metadata.get('document_type', '')
    if doc_type == 'xlsx':
        normalized_score = min(normalized_score + 0.1, 1.0)  # Boost for clean spreadsheets
    elif doc_type == 'pdf':
        normalized_score = min(normalized_score * 0.95, 1.0)  # Slight penalty for PDF complexity
    
    return round(normalized_score, 3)

def update_quality_scores(
    collection_name: str = "nomad_bms_documents",
    batch_size: int = 50,
    dry_run: bool = False
):
    """
    Update quality scores for all points in the collection
    """
    print("🔧 Quality Score Update Tool")
    print("=" * 70)
    print(f"Collection: {collection_name}")
    print(f"Batch size: {batch_size}")
    print(f"Dry run: {dry_run}")
    print()
    
    # Connect to Qdrant
    client = QdrantClient(host="localhost", port=6333)
    
    # Get collection info
    try:
        collection_info = client.get_collection(collection_name)
        total_points = collection_info.points_count
        print(f"📊 Total points in collection: {total_points}")
    except Exception as e:
        print(f"❌ Error accessing collection: {e}")
        return 1
    
    # Scroll through all points
    print(f"\n🔍 Scanning and updating quality scores...")
    print()
    
    offset = None
    processed = 0
    updated = 0
    skipped = 0
    errors = 0
    
    start_time = time.time()
    
    while True:
        # Fetch batch
        try:
            result = client.scroll(
                collection_name=collection_name,
                limit=batch_size,
                offset=offset,
                with_payload=True,
                with_vectors=False
            )
            
            points, next_offset = result
            
            if not points:
                break
            
            # Process each point
            for point in points:
                processed += 1
                
                try:
                    payload = point.payload
                    content = payload.get('content', '')
                    current_quality = payload.get('quality_score', 0.0)
                    
                    # Calculate new quality score
                    new_quality = calculate_quality_score(content, payload)
                    
                    # Skip if already has good quality score
                    if current_quality > 0.5:
                        skipped += 1
                        if processed % 50 == 0:
                            print(f"   [{processed}/{total_points}] Skipped (already has quality)")
                        continue
                    
                    # Update payload
                    if not dry_run:
                        client.set_payload(
                            collection_name=collection_name,
                            payload={"quality_score": new_quality},
                            points=[point.id]
                        )
                    
                    updated += 1
                    
                    # Progress update
                    if processed % 50 == 0:
                        elapsed = time.time() - start_time
                        rate = processed / elapsed if elapsed > 0 else 0
                        eta = (total_points - processed) / rate if rate > 0 else 0
                        print(f"   [{processed}/{total_points}] Updated: {updated} | "
                              f"Rate: {rate:.1f} pts/s | ETA: {eta/60:.1f}m")
                
                except Exception as e:
                    errors += 1
                    if errors <= 5:  # Only show first 5 errors
                        print(f"   ⚠️  Error processing point {point.id}: {e}")
            
            # Check if we're done
            if next_offset is None:
                break
            
            offset = next_offset
        
        except Exception as e:
            print(f"❌ Error during scroll: {e}")
            break
    
    # Summary
    elapsed_time = time.time() - start_time
    
    print()
    print("=" * 70)
    print("📊 UPDATE SUMMARY")
    print("=" * 70)
    print(f"Total processed:  {processed}")
    print(f"✅ Updated:       {updated}")
    print(f"⏭️  Skipped:       {skipped}")
    print(f"❌ Errors:        {errors}")
    print(f"⏱️  Time:          {elapsed_time:.1f}s")
    print(f"📈 Rate:          {processed/elapsed_time:.1f} points/sec")
    
    if dry_run:
        print()
        print("ℹ️  DRY RUN - No changes were made")
        print("   Run without --dry-run to apply updates")
    else:
        print()
        print("✅ Quality scores updated successfully!")
    
    print("=" * 70)
    
    return 0 if errors == 0 else 1

def verify_quality_scores(collection_name: str = "nomad_bms_documents"):
    """
    Verify quality scores after update
    """
    print("\n🔍 Verifying Quality Scores...")
    print("=" * 70)
    
    client = QdrantClient(host="localhost", port=6333)
    
    # Sample some points
    result = client.scroll(
        collection_name=collection_name,
        limit=10,
        with_payload=True,
        with_vectors=False
    )
    
    points, _ = result
    
    print("\nSample Quality Scores:")
    for i, point in enumerate(points, 1):
        payload = point.payload
        doc_name = payload.get('document_name', 'Unknown')[:50]
        quality = payload.get('quality_score', 0.0)
        doc_type = payload.get('document_type', 'unknown')
        print(f"{i}. {doc_name}")
        print(f"   Type: {doc_type} | Quality: {quality:.3f}")
    
    # Calculate statistics
    all_qualities = []
    offset = None
    
    while len(all_qualities) < 100:  # Sample 100 points
        result = client.scroll(
            collection_name=collection_name,
            limit=20,
            offset=offset,
            with_payload=True,
            with_vectors=False
        )
        
        points, next_offset = result
        if not points:
            break
        
        for point in points:
            quality = point.payload.get('quality_score', 0.0)
            all_qualities.append(quality)
        
        if next_offset is None:
            break
        offset = next_offset
    
    if all_qualities:
        avg_quality = sum(all_qualities) / len(all_qualities)
        min_quality = min(all_qualities)
        max_quality = max(all_qualities)
        above_threshold = sum(1 for q in all_qualities if q >= 0.7)
        
        print()
        print("📊 Quality Statistics (sample of 100):")
        print(f"   Average: {avg_quality:.3f}")
        print(f"   Min: {min_quality:.3f}")
        print(f"   Max: {max_quality:.3f}")
        print(f"   Above 0.7: {above_threshold}/100 ({above_threshold}%)")
    
    print("=" * 70)

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Update quality scores in Qdrant")
    parser.add_argument("--collection", default="nomad_bms_documents", help="Collection name")
    parser.add_argument("--batch-size", type=int, default=50, help="Batch size for processing")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without making changes")
    parser.add_argument("--verify", action="store_true", help="Verify quality scores after update")
    
    args = parser.parse_args()
    
    # Update quality scores
    result = update_quality_scores(
        collection_name=args.collection,
        batch_size=args.batch_size,
        dry_run=args.dry_run
    )
    
    # Verify if requested
    if args.verify and not args.dry_run:
        verify_quality_scores(args.collection)
    
    return result

if __name__ == "__main__":
    sys.exit(main())
