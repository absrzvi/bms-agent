#!/usr/bin/env python3
"""
Re-index All Documents with Enhanced Metadata - Standalone Version
Adds document_type_category, is_form, is_template, and is_process fields
"""

import sys
from pathlib import Path
from qdrant_client import QdrantClient

def detect_document_category(filename: str, content: str) -> str:
    """
    Detect document category.
    Returns: form_template, process, policy, manual, or standard
    """
    filename_lower = filename.lower()
    content_lower = content[:500].lower() if content else ""
    
    # Extract document type code from BMS naming
    parts = filename.split('-')
    doc_type_code = parts[2].upper() if len(parts) >= 3 and parts[0].upper() == 'BMS' else ""
    
    # Form/Template detection
    form_indicators = [
        'FOR-' in filename.upper(),
        doc_type_code == 'FOR',
        'template' in filename_lower,
        'form' in filename_lower and 'platform' not in filename_lower,
        'checklist' in filename_lower,
        'questionnaire' in filename_lower,
        'declaration' in filename_lower,
        'request form' in content_lower,
        'form template' in content_lower
    ]
    
    if any(form_indicators):
        return "form_template"
    
    # Process document
    if doc_type_code == 'PRO' or 'process' in filename_lower:
        return "process"
    
    # Policy document
    if doc_type_code == 'POL' or 'policy' in filename_lower:
        return "policy"
    
    # Manual/Guide
    if doc_type_code in ['MAN', 'GUI'] or any(word in filename_lower for word in ['manual', 'guide', 'guideline']):
        return "manual"
    
    return "standard"

def is_template(filename: str, content: str) -> bool:
    """Detect if document is a template"""
    filename_lower = filename.lower()
    content_lower = content[:500].lower() if content else ""
    
    template_indicators = [
        'template' in filename_lower,
        'blank' in filename_lower,
        'example' in filename_lower and ('form' in filename_lower or 'template' in filename_lower),
        'sample' in filename_lower and 'form' in filename_lower,
        '[insert' in content_lower or '[enter' in content_lower,
        'fill out' in content_lower or 'complete this' in content_lower,
    ]
    
    return any(template_indicators)

def main():
    print("=" * 80)
    print("RE-INDEXING ALL DOCUMENTS WITH ENHANCED METADATA")
    print("=" * 80)
    
    # Initialize Qdrant client
    qdrant_client = QdrantClient(host="localhost", port=6333)
    collection_name = "nomad_bms_documents"
    
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
            category = detect_document_category(doc_name, content)
            is_form_flag = (category == "form_template")
            is_template_flag = is_template(doc_name, content)
            is_process_flag = (category == "process")
            
            # Update metadata
            qdrant_client.set_payload(
                collection_name=collection_name,
                payload={
                    "document_type_category": category,
                    "is_form": is_form_flag,
                    "is_template": is_template_flag,
                    "is_process": is_process_flag
                },
                points=[point.id]
            )
            
            # Update stats
            if is_form_flag:
                stats["forms"] += 1
            if is_template_flag:
                stats["templates"] += 1
            if is_process_flag:
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
    
    # Show sample forms
    if stats["forms"] > 0:
        print("\nSample forms detected:")
        form_count = 0
        for point in all_points:
            if point.payload.get("is_form"):
                print(f"  • {point.payload.get('document_name', 'unknown')}")
                form_count += 1
                if form_count >= 10:
                    break
        if stats["forms"] > 10:
            print(f"  ... and {stats['forms'] - 10} more")
    
    print("\n" + "=" * 80)
    print("RE-INDEXING COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()
