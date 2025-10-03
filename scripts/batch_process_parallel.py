#!/usr/bin/env python3
"""
Parallel Batch Processing for T034
Process documents with multiple workers and real-time progress display
"""

import sys
import time
import argparse
from pathlib import Path
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import Manager, cpu_count
import logging

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "bms-agent" / "scr"))

from enhanced_document_processor import EnhancedDocumentProcessor, ProcessingConfig, ProcessingProfile

# Configure logging
logging.basicConfig(
    level=logging.WARNING,  # Reduce noise in parallel mode
    format='%(asctime)s - %(processName)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/workspace/logs/batch_processing_parallel.log'),
    ]
)
logger = logging.getLogger(__name__)


def process_single_document(args):
    """Process a single document - runs in worker process"""
    file_path_str, incoming_dir, processed_dir, failed_dir = args
    
    try:
        file_path = Path(file_path_str)
        
        # Initialize processor in worker
        config = ProcessingConfig(
            chunk_size=2000,
            chunk_overlap=400,
            quality_threshold=0.70,
            enable_quality_validation=True,
            enable_contextual_retrieval=True,
            enable_late_chunking=True,
            processing_profile=ProcessingProfile.RAILWAY
        )
        processor = EnhancedDocumentProcessor(config)
        
        # Process document
        result = processor.process_document(str(file_path))
        
        # Determine success
        success = result.get('processing_success', False)
        chunks = result.get('chunks', [])
        quality_report = result.get('quality_report', {})
        avg_quality = quality_report.get('average_quality', 0.0)
        
        # Move file
        file_type = file_path.suffix.lower().lstrip('.')
        if file_type not in ['pdf', 'docx', 'xlsx', 'pptx', 'csv', 'txt', 'doc', 'xls']:
            file_type = 'other'
        
        target_dir = Path(processed_dir) if success else Path(failed_dir)
        target_path = target_dir / file_type / file_path.name
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Handle duplicates
        if target_path.exists():
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            target_path = target_dir / file_type / f"{file_path.stem}_{timestamp}{file_path.suffix}"
        
        file_path.rename(target_path)
        
        return {
            'success': success,
            'filename': file_path.name,
            'chunks': len(chunks),
            'quality': avg_quality,
            'errors': result.get('errors', []) if not success else []
        }
        
    except Exception as e:
        logger.error(f"Error processing {file_path_str}: {e}", exc_info=True)
        return {
            'success': False,
            'filename': Path(file_path_str).name,
            'chunks': 0,
            'quality': 0.0,
            'errors': [str(e)]
        }


def main():
    parser = argparse.ArgumentParser(description='Parallel Batch Processing for BMS Agent')
    parser.add_argument('-w', '--workers', type=int, default=4, help='Number of parallel workers (default: 4)')
    parser.add_argument('--max-workers', type=int, default=None, help='Maximum workers (default: CPU count)')
    args = parser.parse_args()
    
    # Directories
    incoming_dir = Path('/workspace/bms_data/incoming')
    processed_dir = Path('/workspace/bms_data/processed')
    failed_dir = Path('/workspace/bms_data/failed')
    
    # Create output directories
    for dir_path in [processed_dir, failed_dir]:
        dir_path.mkdir(parents=True, exist_ok=True)
        for subdir in ['pdf', 'docx', 'xlsx', 'pptx', 'csv', 'txt', 'doc', 'xls', 'other']:
            (dir_path / subdir).mkdir(exist_ok=True)
    
    # Get all files
    all_files = []
    patterns = ['*.pdf', '*.docx', '*.xlsx', '*.pptx', '*.csv', '*.txt', '*.doc', '*.xls']
    for pattern in patterns:
        all_files.extend(list(incoming_dir.rglob(pattern)))
    
    all_files = sorted(all_files)
    total_files = len(all_files)
    
    if total_files == 0:
        print("❌ No files found in incoming directory!")
        return 1
    
    # Determine worker count
    max_workers = args.max_workers or cpu_count()
    num_workers = min(args.workers, max_workers, total_files)
    
    print("="*80)
    print("🚀 BMS Agent - Parallel Batch Processing (T034)")
    print("="*80)
    print(f"📁 Input Directory: {incoming_dir}")
    print(f"📁 Processed Directory: {processed_dir}")
    print(f"📁 Failed Directory: {failed_dir}")
    print(f"📋 Total Files: {total_files}")
    print(f"⚡ Workers: {num_workers} (max available: {max_workers})")
    print("="*80)
    print()
    
    # Statistics
    stats = {
        'processed': 0,
        'failed': 0,
        'total_chunks': 0,
        'quality_scores': [],
        'start_time': time.time()
    }
    
    # Prepare arguments for workers
    file_args = [(str(f), str(incoming_dir), str(processed_dir), str(failed_dir)) for f in all_files]
    
    # Process with progress display
    print("🔄 Processing documents...")
    print()
    
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        # Submit all tasks
        future_to_file = {executor.submit(process_single_document, arg): arg[0] for arg in file_args}
        
        # Process completed tasks with progress
        for i, future in enumerate(as_completed(future_to_file), 1):
            try:
                result = future.result()
                
                if result['success']:
                    stats['processed'] += 1
                    stats['total_chunks'] += result['chunks']
                    if result['quality'] > 0:
                        stats['quality_scores'].append(result['quality'])
                    status = f"✅ {result['chunks']} chunks, quality: {result['quality']:.3f}"
                else:
                    stats['failed'] += 1
                    error_msg = result['errors'][0] if result['errors'] else 'Unknown error'
                    status = f"❌ {error_msg[:50]}"
                
                # Progress display
                elapsed = time.time() - stats['start_time']
                rate = i / elapsed if elapsed > 0 else 0
                eta = (total_files - i) / rate if rate > 0 else 0
                
                print(f"[{i}/{total_files}] {result['filename'][:50]:50s} {status}")
                print(f"  Progress: {i/total_files*100:.1f}% | Rate: {rate:.1f} docs/sec | ETA: {eta/60:.1f} min")
                print()
                
            except Exception as e:
                stats['failed'] += 1
                print(f"[{i}/{total_files}] ❌ Error: {e}")
                print()
    
    # Final summary
    elapsed = time.time() - stats['start_time']
    avg_quality = sum(stats['quality_scores']) / len(stats['quality_scores']) if stats['quality_scores'] else 0
    success_rate = (stats['processed'] / total_files * 100) if total_files > 0 else 0
    
    print("="*80)
    print("📊 Processing Summary:")
    print(f"   Total Files: {total_files}")
    print(f"   ✅ Processed: {stats['processed']}")
    print(f"   ❌ Failed: {stats['failed']}")
    print(f"   📝 Total Chunks: {stats['total_chunks']}")
    print(f"   🎯 Average Quality: {avg_quality:.3f}")
    print(f"   ⏱️  Time Elapsed: {elapsed/60:.1f} minutes")
    print(f"   ⚡ Speed: {total_files/elapsed:.2f} docs/sec")
    print("="*80)
    print()
    print("✅ Acceptance Criteria Check:")
    print(f"   Success Rate: {success_rate:.1f}% (target: ≥95%): {'✅ PASS' if success_rate >= 95 else '❌ FAIL'}")
    print(f"   Avg Quality: {avg_quality:.3f} (target: ≥0.70): {'✅ PASS' if avg_quality >= 0.70 else '❌ FAIL'}")
    print(f"   Total Chunks: {stats['total_chunks']}")
    print()
    
    if success_rate >= 95 and avg_quality >= 0.70:
        print("🎉 T034 - COMPLETED SUCCESSFULLY!")
        return 0
    else:
        print("⚠️  T034 - Completed with issues (review failed documents)")
        return 1


if __name__ == '__main__':
    exit(main())
