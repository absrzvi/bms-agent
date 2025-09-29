#!/usr/bin/env python3
"""
Batch Processing Script for BMS Agent
Process all documents in the uploads directory with optional parallel processing
"""

import sys
import argparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from multiprocessing import cpu_count, set_start_method
import multiprocessing

# Set spawn method for CUDA compatibility
try:
    set_start_method('spawn', force=True)
except RuntimeError:
    pass  # Already set

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "bms-agent" / "scr"))

from enhanced_document_processor import (
    EnhancedDocumentProcessor, 
    ProcessingConfig,
    ProcessingProfile,
    process_directory_distributed
)

def process_single_file(args_tuple):
    """Process a single file - used for thread-based parallel processing"""
    file_path_str, processor = args_tuple
    try:
        result = processor.process_document(file_path_str)
        result['file_path'] = file_path_str
        return result
    except Exception as e:
        return {
            'processing_success': False,
            'file_path': file_path_str,
            'errors': [str(e)]
        }

def main():
    """Run batch processing on all documents"""
    
    parser = argparse.ArgumentParser(description="Batch Processing Script for BMS Agent")
    parser.add_argument("-p", "--parallel", action="store_true", help="Enable parallel processing")
    parser.add_argument("-w", "--workers", type=int, default=4, help="Number of parallel workers (default: 4)")
    args = parser.parse_args()
    
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
    
    # Process all documents
    try:
        print("🔄 Starting batch processing...")
        print(f"📝 Processing {len(all_files)} files...")
        if args.parallel:
            num_workers = min(args.workers, cpu_count())
            print(f"⚡ Parallel mode: {num_workers} workers (max available: {cpu_count()})")
        print()
        
        results = []
        successful = 0
        failed = 0
        total_chunks = 0
        
        if args.parallel:
            # Parallel processing with ThreadPoolExecutor (avoids CUDA forking issues)
            processor = EnhancedDocumentProcessor(config)
            
            with ThreadPoolExecutor(max_workers=num_workers) as executor:
                # Submit all tasks with processor instance
                future_to_file = {
                    executor.submit(process_single_file, (str(file_path), processor)): file_path 
                    for file_path in all_files
                }
                
                # Process completed tasks
                for i, future in enumerate(as_completed(future_to_file), 1):
                    file_path = future_to_file[future]
                    try:
                        result = future.result()
                        print(f"[{i}/{len(all_files)}] {file_path.name}...", end=" ")
                        
                        if result.get('processing_success', False):
                            successful += 1
                            chunks = len(result.get('chunks', []))
                            total_chunks += chunks
                            quality_report = result.get('quality_report', {})
                            quality = quality_report.get('average_quality', 0)
                            print(f"✅ ({chunks} chunks, quality: {quality:.3f})")
                        else:
                            failed += 1
                            errors = result.get('errors', ['Unknown error'])
                            print(f"❌ {errors[0] if errors else 'Unknown error'}")
                        
                        results.append(result)
                    except Exception as e:
                        failed += 1
                        print(f"[{i}/{len(all_files)}] {file_path.name}... ❌ Error: {e}")
                        results.append({'processing_success': False, 'file_path': str(file_path), 'errors': [str(e)]})
        else:
            # Sequential processing
            processor = EnhancedDocumentProcessor(config)
            
            for i, file_path in enumerate(all_files, 1):
                try:
                    print(f"[{i}/{len(all_files)}] Processing: {file_path.name}...", end=" ")
                    
                    # Process document
                    result = processor.process_document(str(file_path))
                    
                    # Check if processing was successful
                    if result.get('processing_success', False):
                        successful += 1
                        chunks = len(result.get('chunks', []))
                        total_chunks += chunks
                        # Get quality from quality_report
                        quality_report = result.get('quality_report', {})
                        quality = quality_report.get('average_quality', 0)
                        print(f"✅ ({chunks} chunks, quality: {quality:.3f})")
                    else:
                        failed += 1
                        errors = result.get('errors', ['Unknown error'])
                        print(f"❌ {errors[0] if errors else 'Unknown error'}")
                    
                    results.append(result)
                    
                except Exception as e:
                    failed += 1
                    print(f"❌ Error: {e}")
                    results.append({'processing_success': False, 'file_path': str(file_path), 'errors': [str(e)]})
        
        print()
        print(f"✅ Batch processing completed!")
        print(f"📊 Processed {len(results)} documents")
        print()
        
        # Calculate average quality
        quality_scores = []
        for r in results:
            if r.get('processing_success', False):
                qr = r.get('quality_report', {})
                if qr and qr.get('average_quality'):
                    quality_scores.append(qr.get('average_quality'))
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
                if not result.get('processing_success', False):
                    file_path = result.get('file_path', result.get('document_id', 'Unknown'))
                    errors = result.get('errors', ['Unknown error'])
                    error = errors[0] if errors else 'Unknown error'
                    print(f"   - {Path(file_path).name if file_path != 'Unknown' else 'Unknown'}: {error}")
        
        print("🎉 All documents processed and ready for search!")
        
    except Exception as e:
        print(f"❌ Batch processing failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
