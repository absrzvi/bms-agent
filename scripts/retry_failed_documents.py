#!/usr/bin/env python3
"""
Retry Processing for Failed Documents
Specifically targets the 4 missing POC evaluation documents
"""

import sys
import shutil
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "bms-agent" / "scr"))

from enhanced_document_processor import EnhancedDocumentProcessor, ProcessingConfig, ProcessingProfile
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
import uuid

def retry_single_document(file_path: Path, processor, qdrant_client):
    """Retry processing a single failed document"""
    print(f"\n{'='*80}")
    print(f"Processing: {file_path.name}")
    print(f"{'='*80}")
    
    try:
        # Process document (Enhanced Processor v4.0 handles Qdrant storage automatically)
        print(f"  📄 Reading file...")
        result = processor.process_document(
            file_path=str(file_path),
            document_id=file_path.stem  # Use filename without extension as ID
        )
        
        if not result.get('processing_success', False):
            errors = result.get('errors', ['Unknown error'])
            print(f"  ❌ Processing failed: {errors}")
            return False
        
        # Get processing stats
        chunks = result.get('chunks', [])
        quality_report = result.get('quality_report', {})
        avg_quality = quality_report.get('average_quality', 0.0)
        processing_time = result.get('processing_time', 0.0)
        
        print(f"  ✅ Processing successful!")
        print(f"     - Chunks: {len(chunks)}")
        print(f"     - Quality: {avg_quality:.3f}")
        print(f"     - Processing time: {processing_time:.2f}s")
        
        # NOTE: Enhanced Document Processor v4.0 automatically stores chunks in Qdrant
        # No manual upload needed
        print(f"  ✅ Chunks automatically stored in Qdrant by processor")
        
        # Move to processed directory
        processed_dir = Path('/workspace/bms_data/processed') / file_path.suffix[1:]  # Remove leading dot
        processed_dir.mkdir(parents=True, exist_ok=True)
        dest_path = processed_dir / file_path.name
        shutil.copy2(file_path, dest_path)
        print(f"  📁 Moved to: {dest_path}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("="*80)
    print("RETRY PROCESSING FOR 4 MISSING POC EVALUATION DOCUMENTS")
    print("="*80)
    print("\nTarget Documents:")
    print("  1. BMS-HUMR-FOR-005 Employee Referral Form.doc")
    print("  2. BMS-HUMR-FOR-018 Driver Declaration Form.doc")
    print("  3. BMS-ISEC-FOR-015 Information Security Management Plan Template.docx")
    print("  4. BMS-QHSE-FOR-029 Safety Bulletin.docx")
    print()
    
    # Initialize processor
    print("Initializing Enhanced Document Processor v4.0...")
    config = ProcessingConfig(
        chunk_size=2000,
        chunk_overlap=400,
        quality_threshold=0.70,
        enable_quality_validation=True,
        enable_contextual_retrieval=True,
        enable_late_chunking=True,
        processing_profile=ProcessingProfile.RAILWAY,
        use_gpu=True
    )
    processor = EnhancedDocumentProcessor(config)
    
    # Initialize Qdrant client
    print("Connecting to Qdrant...")
    qdrant_client = QdrantClient(host="localhost", port=6333)
    print("✅ Connected\n")
    
    # Define failed document paths
    failed_docs = [
        Path("/workspace/bms_data/failed/doc/BMS-HUMR-FOR-005 Employee Referral Form.doc"),
        Path("/workspace/bms_data/failed/doc/BMS-HUMR-FOR-018 Driver Declaration Form.doc"),
        Path("/workspace/bms_data/failed/docx/BMS-ISEC-FOR-015 Information Security Management Plan Template.docx"),
        Path("/workspace/bms_data/failed/docx/BMS-QHSE-FOR-029 Safety Bulletin.docx"),
    ]
    
    # Track results
    results = {
        "success": [],
        "failed": []
    }
    
    # Process each document
    for doc_path in failed_docs:
        if not doc_path.exists():
            print(f"\n⚠️  File not found: {doc_path.name}")
            results["failed"].append(doc_path.name)
            continue
        
        success = retry_single_document(doc_path, processor, qdrant_client)
        
        if success:
            results["success"].append(doc_path.name)
        else:
            results["failed"].append(doc_path.name)
    
    # Print summary
    print("\n" + "="*80)
    print("RECOVERY SUMMARY")
    print("="*80)
    print(f"\n✅ Successfully Recovered: {len(results['success'])}/4")
    for doc in results['success']:
        print(f"   - {doc}")
    
    if results['failed']:
        print(f"\n❌ Failed to Recover: {len(results['failed'])}/4")
        for doc in results['failed']:
            print(f"   - {doc}")
    
    print("\n" + "="*80)
    
    # Return exit code
    if len(results['success']) == 4:
        print("🎉 ALL 4 DOCUMENTS RECOVERED!")
        return 0
    elif len(results['success']) > 0:
        print(f"⚠️  PARTIAL RECOVERY: {len(results['success'])}/4 documents")
        return 1
    else:
        print("❌ NO DOCUMENTS RECOVERED")
        return 2

if __name__ == "__main__":
    sys.exit(main())
