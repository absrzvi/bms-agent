#!/usr/bin/env python3
"""
Re-index All Documents with Enhanced Metadata
Adds document_type_category, is_form, is_template, and is_process fields to all documents in Qdrant
"""

import sys
from pathlib import Path
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue, UpdateStatus

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "bms-agent" / "scr"))

from enhanced_document_processor import EnhancedDocumentProcessor

def main():
    print("=" * 80)
    print("RE-INDEXING ALL DOCUMENTS WITH ENHANCED METADATA")
    print("=" * 80)
    
    # Initialize clients
    qdrant_client = QdrantClient(host="localhost", port=6333)
    collection_name = "nomad_bms_documents"
    processor = EnhancedDocumentProcessor()
    
    # Get all points
    print("\nFetching all documents...")
    all_points = []
    offset = None
    
    while True:
        result = qdrant_client.scroll(
            collection_name=collection_name,
            limit=1000,
            offset=offset,
            with_payload=True
        )
        
        points, offset = result
        all_points.extend(points)
        
        if offset is None:
            break
    
    print(f"Total points: {len(all_points)}")
    
    # Categorize all documents
    stats = {"forms": 0, "templates": 0, "processes": 0, "policies": 0, "manuals": 0, "standard": 0}
    
    print("\nAnalyzing and updating all documents...")
    for i, point in enumerate(all_points, 1):
        try:
            doc_name = point.payload.get("document_name", "")
            content = point.payload.get("content", "")
            
            # Detect category and flags
            category = processor._detect_document_category(doc_name, content)
            is_form = (category == "form_template")
            is_template = processor._is_template(doc_name, content)
            is_process = (category == "process")
            
            # Update metadata
            qdrant_client.set_payload(
                collection_name=collection_name,
                payload={
                    "document_type_category": category,
                    "is_form": is_form,
                    "is_template": is_template,
                    "is_process": is_process
                },
                points=[point.id]
            )
            
            # Update stats
            if is_form:
                stats["forms"] += 1
            if is_template:
                stats["templates"] += 1
            if is_process:
                stats["processes"] += 1
            if category == "policy":
                stats["policies"] += 1
            elif category == "manual":
                stats["manuals"] += 1
            elif category == "standard":
                stats["standard"] += 1
            
            if i % 100 == 0:
                print(f"  Processed {i}/{len(all_points)} documents...")
                
        except Exception as e:
            print(f"  ❌ Error updating {point.payload.get('document_name', 'unknown')}: {e}")
    
    print(f"\n✅ Successfully updated {len(all_points)} documents")
    
    # Show statistics
    print("\n📊 Document Type Statistics:")
    print(f"  Forms: {stats['forms']}")
    print(f"  Templates: {stats['templates']}")
    print(f"  Processes: {stats['processes']}")
    print(f"  Policies: {stats['policies']}")
    print(f"  Manuals/Guides: {stats['manuals']}")
    print(f"  Standard docs: {stats['standard']}")
    
    print("\n" + "=" * 80)
    print("RE-INDEXING COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()
