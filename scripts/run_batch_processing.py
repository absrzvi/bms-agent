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
    ProcessingProfile,
    process_directory_distributed
)

def main():
    """Run batch processing on all documents"""
    
    # Configuration for BMS documents
    config = ProcessingConfig(
        chunk_size=2000,
        chunk_overlap=400,
        quality_threshold=70.0,
        enable_quality_validation=True,
        enable_contextual_retrieval=True,
        enable_late_chunking=True,
        processing_profile=ProcessingProfile.TECHNICAL  # BMS technical documents
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
    
    # Count total files (recursive search)
    all_patterns = ["*.pdf", "*.csv", "*.xlsx", "*.xls", "*.txt", "*.md", "*.docx", "*.pptx"]
    total_files = 0
    all_files = []
    for pattern in all_patterns:
        files = list(input_dir.rglob(pattern))
        all_files.extend(files)
        total_files += len(files)
    
    print(f"📋 Found {total_files} documents to process")
    print()
    
    if total_files == 0:
        print("❌ No documents found in upload directory")
        return
    
    # Process all documents individually (simpler approach)
    try:
        print("🔄 Starting batch processing...")
        print(f"📝 Processing {len(all_files)} files...")
        print()
        
        # Initialize processor
        processor = EnhancedDocumentProcessor(config)
        
        results = []
        successful = 0
        failed = 0
        total_chunks = 0
        
        for i, file_path in enumerate(all_files, 1):
            try:
                print(f"[{i}/{len(all_files)}] Processing: {file_path.name}...", end=" ")
                
                # Process document
                result = processor.process_document(str(file_path))
                
                if result.get('status') == 'success':
                    successful += 1
                    chunks = result.get('chunks_created', 0)
                    total_chunks += chunks
                    quality = result.get('quality_score', 0)
                    print(f"✅ ({chunks} chunks, quality: {quality:.3f})")
                else:
                    failed += 1
                    print(f"❌ {result.get('error', 'Unknown error')}")
                
                results.append(result)
                
            except Exception as e:
                failed += 1
                print(f"❌ Error: {e}")
                results.append({'status': 'error', 'file_path': str(file_path), 'error': str(e)})
        
        print()
        print(f"✅ Batch processing completed!")
        print(f"📊 Processed {len(results)} documents")
        print()
        
        # Calculate average quality
        quality_scores = [r.get('quality_score', 0) for r in results if r.get('status') == 'success' and r.get('quality_score')]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
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
                    file_path = result.get('file_path', 'Unknown')
                    error = result.get('error', 'Unknown error')
                    print(f"   - {Path(file_path).name}: {error}")
        
        print("🎉 All documents processed and ready for search!")
        
    except Exception as e:
        print(f"❌ Batch processing failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
