#!/usr/bin/env python3
"""
Batch Process Incoming Documents - T034 Implementation
Process all downloaded SharePoint documents from /workspace/bms_data/incoming/
and ingest them into Qdrant with 768-dim embeddings.
Supports parallel processing with multiple workers.
"""

import sys
import json
import shutil
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import Manager
import logging

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "bms-agent" / "scr"))

from enhanced_document_processor import EnhancedDocumentProcessor, ProcessingConfig, ProcessingProfile
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/workspace/logs/batch_processing.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class BatchProcessor:
    """Batch processor for incoming SharePoint documents"""
    
    def __init__(self, use_gpu: bool = True, shard_index: int | None = None, shard_count: int | None = None):
        self.base_dir = Path('/workspace/bms_data')
        self.incoming_dir = self.base_dir / 'incoming'
        self.processed_dir = self.base_dir / 'processed'
        self.failed_dir = self.base_dir / 'failed'

        if shard_count is not None and shard_count <= 0:
            raise ValueError("shard_count must be positive")
        if shard_index is not None and shard_count is None:
            raise ValueError("shard_count must be provided when shard_index is set")
        if shard_index is not None and not (0 <= shard_index < shard_count):
            raise ValueError("shard_index must be in range [0, shard_count)")

        self.shard_index = shard_index
        self.shard_count = shard_count
        
        # Create output directories
        for dir_path in [self.processed_dir, self.failed_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
            for subdir in ['pdf', 'docx', 'xlsx', 'pptx', 'csv', 'txt', 'doc', 'xls', 'other']:
                (dir_path / subdir).mkdir(exist_ok=True)
        
        # Initialize processor with 768-dim embeddings
        config = ProcessingConfig(
            chunk_size=2000,
            chunk_overlap=400,
            quality_threshold=0.70,
            enable_quality_validation=True,
            enable_contextual_retrieval=True,
            enable_late_chunking=True,
            processing_profile=ProcessingProfile.RAILWAY,
            use_gpu=use_gpu  # Allow CPU/GPU selection
        )
        self.processor = EnhancedDocumentProcessor(config)
        
        # Initialize Qdrant client
        self.qdrant_client = QdrantClient(host="localhost", port=6333)
        self.collection_name = "nomad_bms_documents"
        
        # Statistics
        self.stats = {
            'total_files': 0,
            'processed': 0,
            'failed': 0,
            'total_chunks': 0,
            'quality_scores': [],
            'start_time': datetime.now()
        }
    
    def get_all_files(self) -> List[Path]:
        """Get all files from incoming directory"""
        all_files = []
        patterns = ['*.pdf', '*.docx', '*.xlsx', '*.pptx', '*.csv', '*.txt', '*.doc', '*.xls']
        
        for pattern in patterns:
            files = list(self.incoming_dir.rglob(pattern))
            all_files.extend(files)
        
        return sorted(all_files)
    
    def get_file_type(self, file_path: Path) -> str:
        """Get file type subdirectory name"""
        ext = file_path.suffix.lower().lstrip('.')
        if ext in ['pdf', 'docx', 'xlsx', 'pptx', 'csv', 'txt', 'doc', 'xls']:
            return ext
        return 'other'
    
    def process_file(self, file_path: Path) -> Tuple[bool, Dict]:
        """Process a single file - Enhanced Document Processor handles Qdrant ingestion"""
        try:
            logger.info(f"Processing: {file_path.name}")
            
            # Process document (processor handles Qdrant storage automatically)
            result = self.processor.process_document(str(file_path))
            
            if not result.get('processing_success', False):
                logger.error(f"❌ Processing failed: {file_path.name}")
                return False, result
            
            # Get chunks and quality
            chunks = result.get('chunks', [])
            quality_report = result.get('quality_report', {})
            avg_quality = quality_report.get('average_quality', 0.0)
            num_chunks = len(chunks)
            
            if num_chunks == 0:
                logger.warning(f"⚠️  No chunks generated: {file_path.name}")
                return False, result
            
            # Enhanced Document Processor v4.0 already stored chunks in Qdrant
            # Just track statistics here
            logger.info(f"✅ Processed {num_chunks} chunks (quality: {avg_quality:.3f})")
            
            self.stats['quality_scores'].append(avg_quality)
            self.stats['total_chunks'] += num_chunks
            
            return True, result
            
        except Exception as e:
            logger.error(f"❌ Error processing {file_path.name}: {e}", exc_info=True)
            return False, {'errors': [str(e)]}
    
    def move_file(self, file_path: Path, success: bool):
        """Move file to processed or failed directory"""
        try:
            file_type = self.get_file_type(file_path)
            target_dir = self.processed_dir if success else self.failed_dir
            target_path = target_dir / file_type / file_path.name
            
            # Handle duplicate names
            if target_path.exists():
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                target_path = target_dir / file_type / f"{file_path.stem}_{timestamp}{file_path.suffix}"
            
            shutil.move(str(file_path), str(target_path))
            logger.debug(f"Moved to: {target_path}")
            
        except Exception as e:
            logger.error(f"Failed to move {file_path.name}: {e}")
    
    def run(self):
        """Run batch processing"""
        logger.info("="*80)
        logger.info("🚀 BMS Agent - Batch Processing Incoming Documents (T034)")
        logger.info("="*80)
        logger.info(f"📁 Input Directory: {self.incoming_dir}")
        logger.info(f"📁 Processed Directory: {self.processed_dir}")
        logger.info(f"🗄️  Qdrant Collection: {self.collection_name}")
        logger.info("")
        
        # Get all files
        all_files = self.get_all_files()

        if self.shard_count and self.shard_count > 1:
            filtered_files = [
                file_path
                for idx, file_path in enumerate(all_files)
                if idx % self.shard_count == self.shard_index
            ]
        else:
            filtered_files = all_files

        self.stats['total_files'] = len(filtered_files)

        if not filtered_files:
            logger.error("❌ No files found in incoming directory!")
            return 1
        
        logger.info(f"📋 Found {len(all_files)} documents to process")
        if self.shard_count and self.shard_count > 1:
            logger.info(f"🔀 Shard {self.shard_index + 1}/{self.shard_count}: processing {len(filtered_files)} documents")
        logger.info("")
        
        # Process each file
        for i, file_path in enumerate(filtered_files, 1):
            logger.info(f"[{i}/{len(filtered_files)}] {file_path.name}")
            success, result = self.process_file(file_path)
            
            if success:
                self.stats['processed'] += 1
                self.move_file(file_path, success=True)
            else:
                self.stats['failed'] += 1
                self.move_file(file_path, success=False)
                # Log error details
                errors = result.get('errors', ['Unknown error'])
                file_type = self.get_file_type(file_path)
                error_log_path = self.failed_dir / file_type / f"{file_path.stem}_error.log"
                with open(error_log_path, 'w') as f:
                    f.write(f"File: {file_path.name}\n")
                    f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                    f.write(f"Errors:\n")
                    for error in errors:
                        f.write(f"  - {error}\n")
            
            logger.info("")
        
        # Print summary
        self.print_summary()
        
        # Check acceptance criteria
        success_rate = (self.stats['processed'] / self.stats['total_files'] * 100) if self.stats['total_files'] > 0 else 0
        avg_quality = sum(self.stats['quality_scores']) / len(self.stats['quality_scores']) if self.stats['quality_scores'] else 0
        
        logger.info("")
        logger.info("✅ Acceptance Criteria Check:")
        logger.info(f"   Success Rate: {success_rate:.1f}% (target: ≥95%): {'✅ PASS' if success_rate >= 95 else '❌ FAIL'}")
        logger.info(f"   Avg Quality: {avg_quality:.3f} (target: ≥0.70): {'✅ PASS' if avg_quality >= 0.70 else '❌ FAIL'}")
        logger.info(f"   Total Chunks: {self.stats['total_chunks']}")
        logger.info("")
        
        if success_rate >= 95 and avg_quality >= 0.70:
            logger.info("🎉 T034 - COMPLETED SUCCESSFULLY!")
            return 0
        else:
            logger.warning("⚠️  T034 - Completed with issues (review failed documents)")
            return 1
    
    def print_summary(self):
        """Print processing summary"""
        elapsed = (datetime.now() - self.stats['start_time']).total_seconds()
        
        logger.info("="*80)
        logger.info("📊 Processing Summary:")
        logger.info(f"   Total Files: {self.stats['total_files']}")
        logger.info(f"   ✅ Processed: {self.stats['processed']}")
        logger.info(f"   ❌ Failed: {self.stats['failed']}")
        logger.info(f"   📝 Total Chunks: {self.stats['total_chunks']}")
        
        if self.stats['quality_scores']:
            avg_quality = sum(self.stats['quality_scores']) / len(self.stats['quality_scores'])
            logger.info(f"   🎯 Average Quality: {avg_quality:.3f}")
        
        logger.info(f"   ⏱️  Time Elapsed: {elapsed:.1f} seconds")
        
        if self.stats['total_files'] > 0:
            docs_per_sec = self.stats['total_files'] / elapsed if elapsed > 0 else 0
            logger.info(f"   ⚡ Speed: {docs_per_sec:.2f} docs/sec")
        
        logger.info("="*80)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Batch Process Incoming Documents')
    parser.add_argument('--cpu', action='store_true', help='Force CPU mode (avoid GPU OOM in parallel processing)')
    parser.add_argument('--shard-index', type=int, help='Zero-based shard index for splitting work across workers')
    parser.add_argument('--shard-count', type=int, help='Total number of shards/workers when splitting work')
    args = parser.parse_args()
    
    processor = BatchProcessor(
        use_gpu=not args.cpu,
        shard_index=args.shard_index,
        shard_count=args.shard_count
    )
    return processor.run()


if __name__ == '__main__':
    exit(main())
