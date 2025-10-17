#!/usr/bin/env python3
"""
Upload Excel files directly to Qdrant with Excel-optimized settings
Bypasses API quality validation that's too strict for tabular data
"""

import sys
from pathlib import Path
from datetime import datetime
import subprocess

# Add paths
sys.path.insert(0, str(Path.cwd() / 'bms-agent' / 'scr'))
sys.path.insert(0, str(Path.cwd() / 'api'))

from enhanced_document_processor import (
    EnhancedDocumentProcessor, ProcessingConfig, ProcessingProfile, ChunkingStrategy
)
from processor_wrapper import BMSDocumentProcessor

def find_excel_files(directory: str, cutoff_date: str = "2023-12-31"):
    """Find BMS-*.xlsx files modified after cutoff date"""
    cmd = f'find {directory} -name "BMS-*.xlsx" -newermt "{cutoff_date}" -type f'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    files = [Path(line.strip()) for line in result.stdout.strip().split('\n') if line.strip()]
    return files

def main():
    print("📊 EXCEL FILES TO QDRANT - DIRECT UPLOAD")
    print("=" * 80)
    print("Filter: BMS-*.xlsx files modified after 2023-12-31")
    print("Using Excel-optimized settings (no quality validation)")
    print()
    
    # Find files
    print("🔍 Finding Excel files...")
    excel_dir = "/workspace/bms_data/uploads/xls"
    files = find_excel_files(excel_dir)
    
    print(f"✅ Found {len(files)} Excel files")
    print()
    
    # Initialize processor wrapper with Excel-friendly settings
    print("🚀 Initializing processor with Excel-optimized configuration...")
    wrapper = BMSDocumentProcessor()
    
    # Override config for Excel files
    wrapper.processor_config.chunk_size = 1000
    wrapper.processor_config.min_chunk_size = 150
    wrapper.processor_config.chunk_overlap = 200
    wrapper.processor_config.quality_threshold = 45.0  # Lower for Excel
    wrapper.processor_config.min_quality_score = 35.0  # Lower for Excel
    wrapper.processor_config.enable_quality_validation = False  # Disable for Excel
    wrapper.processor_config.enable_late_chunking = False  # Preserve table structure
    wrapper.processor_config.processing_profile = ProcessingProfile.GENERAL
    
    # Reinitialize processor with new config
    wrapper.processor = EnhancedDocumentProcessor(wrapper.processor_config)
    
    print("✅ Processor configured for Excel files")
    print(f"   - Quality validation: DISABLED")
    print(f"   - Min chunk size: {wrapper.processor_config.min_chunk_size}")
    print(f"   - Quality threshold: {wrapper.processor_config.quality_threshold}")
    print()
    
    # Process files
    total_chunks = 0
    successful = 0
    failed = 0
    skipped = 0
    
    for i, file_path in enumerate(files, 1):
        print(f"[{i}/{len(files)}] {file_path.name}")
        print("-" * 70)
        
        try:
            # Process and upload
            result = wrapper.process_document(str(file_path), processing_profile="general")
            
            if result.status == "success" and result.chunks_created > 0:
                successful += 1
                total_chunks += result.chunks_created
                print(f"   ✅ SUCCESS: {result.chunks_created} chunks created")
                print(f"   📊 Quality: {result.quality_score:.2f}")
                print(f"   ⏱️  Time: {result.processing_time_ms/1000:.1f}s")
            elif result.status == "success" and result.chunks_created == 0:
                skipped += 1
                print(f"   ⚠️  SKIPPED: No chunks created (file too small or low quality)")
            else:
                failed += 1
                print(f"   ❌ FAILED: {result.error}")
                
        except Exception as e:
            failed += 1
            print(f"   ❌ EXCEPTION: {e}")
        
        print()
    
    # Summary
    print("=" * 80)
    print("📊 UPLOAD SUMMARY:")
    print(f"   Total Files: {len(files)}")
    print(f"   ✅ Successful: {successful}")
    print(f"   ⚠️  Skipped: {skipped}")
    print(f"   ❌ Failed: {failed}")
    print(f"   📝 Total Chunks in Qdrant: {total_chunks}")
    print("=" * 80)
    
    if successful > 0:
        print(f"\n✅ Successfully uploaded {successful} Excel files with {total_chunks} chunks!")
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    exit(main())
