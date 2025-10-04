#!/usr/bin/env python3
"""
Reprocess Sparse Forms with Content Augmentation
Identifies and reprocesses forms with <1000 characters to add semantic-rich descriptions
"""

import sys
from pathlib import Path
import shutil
from qdrant_client import QdrantClient

def main():
    print("=" * 80)
    print("REPROCESSING SPARSE FORMS WITH AUGMENTATION")
    print("=" * 80)
    
    # Initialize Qdrant client
    qdrant_client = QdrantClient(host="localhost", port=6333)
    collection_name = "nomad_bms_documents"
    
    # Get all points with form metadata
    print("\nFetching all forms...")
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
    
    print(f"Total chunks: {len(all_points)}")
    
    # Identify sparse forms (content < 1000 chars)
    sparse_forms = {}  # {document_name: [chunk_ids]}
    
    for point in all_points:
        if point.payload.get("is_form"):
            content = point.payload.get("content", "")
            doc_name = point.payload.get("document_name", "")
            
            # Check if sparse (excluding augmentation prefix if already there)
            if "FORM DESCRIPTION:" in content:
                # Already augmented, skip
                continue
            
            if len(content) < 1000:
                if doc_name not in sparse_forms:
                    sparse_forms[doc_name] = []
                sparse_forms[doc_name].append(point.id)
    
    print(f"\nSparse forms needing augmentation: {len(sparse_forms)}")
    
    if not sparse_forms:
        print("\n✅ No sparse forms found - all forms already augmented or have sufficient content")
        return
    
    # Show sample
    print("\nSample sparse forms:")
    for i, doc_name in enumerate(list(sparse_forms.keys())[:10], 1):
        chunk_count = len(sparse_forms[doc_name])
        print(f"  {i}. {doc_name} ({chunk_count} chunks)")
    if len(sparse_forms) > 10:
        print(f"  ... and {len(sparse_forms) - 10} more")
    
    # Copy files to incoming for reprocessing
    print("\nPreparing files for reprocessing...")
    
    processed_dir = Path('/workspace/bms_data/processed')
    incoming_dir = Path('/workspace/bms_data/incoming/sparse_forms_reprocess')
    incoming_dir.mkdir(parents=True, exist_ok=True)
    
    # Clear incoming directory
    for f in incoming_dir.glob('*'):
        f.unlink()
    
    copied = 0
    for doc_name in sparse_forms.keys():
        # Find file in processed directory
        found = False
        for ext_dir in ['docx', 'xlsx', 'pptx', 'pdf', 'doc', 'xls']:
            source_path = processed_dir / ext_dir / doc_name
            if source_path.exists():
                dest_path = incoming_dir / doc_name
                shutil.copy2(source_path, dest_path)
                copied += 1
                found = True
                break
        
        if not found:
            print(f"  ⚠️  Could not find source file for: {doc_name}")
    
    print(f"\n✅ Copied {copied} files to {incoming_dir}")
    print("\nNext steps:")
    print("1. Run batch processor:")
    print(f"   /workspace/bms-api-venv/bin/python3 scripts/batch_process_incoming.py")
    print("   (Note: Update script to use incoming/sparse_forms_reprocess)")
    print("\n2. Re-run evaluation:")
    print(f"   /workspace/bms-api-venv/bin/python3 scripts/evaluate_retrieval_enhanced.py")
    
    print("\n" + "=" * 80)
    print(f"PREPARED {copied} SPARSE FORMS FOR REPROCESSING")
    print("=" * 80)

if __name__ == "__main__":
    main()
