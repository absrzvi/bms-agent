#!/usr/bin/env python3
"""
Batch process all documents in /workspace/bms_data/uploads/ using Enhanced Document Processor v4.0
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "bms-agent" / "scr"))

from enhanced_document_processor import (
    EnhancedDocumentProcessor, 
    ProcessingConfig,
    process_directory_distributed
)

def main():
    """Run batch processing on all documents"""
    
    # Configuration for BMS documents
    config = ProcessingConfig(
        chunk_size=2000,
        chunk_overlap=400,
        quality_threshold=0.70,
        enable_quality_filter=True,
        enable_context_preservation=True,
        enable_late_chunking=True,
        processing_profile="railway"  # BMS railway documents
    )
    
    # Input and output directories
    input_dir = Path("/workspace/bms_data/uploads")
    output_dir = Path("/workspace/bms_data/processed")
    
    print("🚀 BMS Agent - Enhanced Document Processor v4.0 Batch Processing")
    print("=" * 70)
    print(f"📁 Input Directory: {input_dir}")
    print(f"📁 Output Directory: {output_dir}")
    print(f"🎯 Quality Threshold: {config.quality_threshold}")
    print(f"📊 Processing Profile: {config.processing_profile}")
    print()
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Count total files
    all_patterns = ["*.pdf", "*.csv", "*.xlsx", "*.xls", "*.txt", "*.md", "*.docx", "*.pptx"]
    total_files = 0
    for pattern in all_patterns:
        total_files += len(list(input_dir.rglob(pattern)))
    
    print(f"📋 Found {total_files} documents to process")
    print()
    
    if total_files == 0:
        print("❌ No documents found in upload directory")
        return
    
    # Process all documents with distributed processing
    try:
        print("🔄 Starting batch processing...")
        results = process_directory_distributed(
            directory=input_dir,
            config=config,
            patterns=all_patterns,
            num_workers=4  # Parallel processing
        )
        
        print(f"✅ Batch processing completed!")
        print(f"📊 Processed {len(results)} documents")
        print()
        
        # Summary statistics
        successful = sum(1 for r in results if r.get('status') == 'success')
        failed = len(results) - successful
        total_chunks = sum(r.get('chunks_created', 0) for r in results)
        avg_quality = sum(r.get('quality_score', 0) for r in results) / len(results) if results else 0
        
        print("📈 Processing Summary:")
        print(f"   ✅ Successful: {successful}")
        print(f"   ❌ Failed: {failed}")
        print(f"   📝 Total Chunks: {total_chunks}")
        print(f"   🎯 Average Quality: {avg_quality:.3f}")
        print()
        
        # Show failed documents if any
        if failed > 0:
            print("❌ Failed Documents:")
            for result in results:
                if result.get('status') != 'success':
                    print(f"   - {result.get('file_path', 'Unknown')}: {result.get('error', 'Unknown error')}")
        
        print("🎉 All documents processed and ready for search!")
        
    except Exception as e:
        print(f"❌ Batch processing failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
