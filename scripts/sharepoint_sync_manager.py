#!/usr/bin/env python3
"""
SharePoint Sync Manager - Automated Daily Document Synchronization

This script manages the complete workflow:
1. Downloads new/updated documents from SharePoint
2. Organizes files by type into proper directory structure
3. Processes documents with Enhanced Document Processor v4.0
4. Ingests to Qdrant database
5. Moves processed files to archive
6. Handles errors and failed documents

Directory Structure:
/workspace/bms_data/
├── incoming/           # Downloaded files sorted by type
│   ├── pdf/
│   ├── docx/
│   ├── xlsx/
│   ├── pptx/
│   ├── csv/
│   └── txt/
├── processing/         # Currently being processed
├── processed/          # Successfully processed (archive)
│   ├── pdf/
│   ├── docx/
│   └── ...
├── failed/             # Failed to process (with error logs)
│   ├── pdf/
│   ├── docx/
│   └── ...
└── uploads/            # API upload directory (existing)

Can be run:
- Manually: python sharepoint_sync_manager.py
- Daily cron: 0 2 * * * /path/to/sharepoint_sync_manager.py
- Systemd timer: See sharepoint-sync.timer
"""

import json
import shutil
import logging
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.download_sharepoint_server import SharePointDownloader, load_documents_from_csv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/workspace/logs/sharepoint_sync.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DirectoryManager:
    """Manages the directory structure for document processing"""
    
    def __init__(self, base_dir='/workspace/bms_data'):
        self.base_dir = Path(base_dir)
        self.dirs = {
            'incoming': self.base_dir / 'incoming',
            'processing': self.base_dir / 'processing',
            'processed': self.base_dir / 'processed',
            'failed': self.base_dir / 'failed',
            'uploads': self.base_dir / 'uploads'  # API upload dir
        }
        
        # File type subdirectories
        self.file_types = ['pdf', 'docx', 'xlsx', 'pptx', 'csv', 'txt', 'doc', 'xls']
        
        self.setup_directories()
    
    def setup_directories(self):
        """Create all required directories"""
        logger.info("Setting up directory structure...")
        
        # Create main directories
        for name, path in self.dirs.items():
            path.mkdir(parents=True, exist_ok=True)
            logger.info(f"  ✅ {name}: {path}")
        
        # Create file type subdirectories
        for dir_name in ['incoming', 'processed', 'failed']:
            for file_type in self.file_types:
                subdir = self.dirs[dir_name] / file_type
                subdir.mkdir(exist_ok=True)
        
        logger.info("✅ Directory structure ready")
    
    def get_file_type(self, filename: str) -> str:
        """Get file type from filename"""
        ext = Path(filename).suffix.lower().lstrip('.')
        
        # Normalize extensions
        if ext in ['doc', 'docx']:
            return 'docx'
        elif ext in ['xls', 'xlsx']:
            return 'xlsx'
        elif ext in ['ppt', 'pptx']:
            return 'pptx'
        elif ext in self.file_types:
            return ext
        else:
            return 'other'
    
    def organize_file(self, source_path: Path, destination: str = 'incoming') -> Path:
        """Move file to appropriate directory based on type"""
        file_type = self.get_file_type(source_path.name)
        dest_dir = self.dirs[destination] / file_type
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        dest_path = dest_dir / source_path.name
        
        # Handle duplicates
        if dest_path.exists():
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            stem = dest_path.stem
            suffix = dest_path.suffix
            dest_path = dest_dir / f"{stem}_{timestamp}{suffix}"
        
        shutil.move(str(source_path), str(dest_path))
        return dest_path
    
    def move_to_processing(self, file_path: Path) -> Path:
        """Move file to processing directory"""
        dest_path = self.dirs['processing'] / file_path.name
        shutil.move(str(file_path), str(dest_path))
        return dest_path
    
    def move_to_processed(self, file_path: Path) -> Path:
        """Move successfully processed file to archive"""
        file_type = self.get_file_type(file_path.name)
        dest_dir = self.dirs['processed'] / file_type
        dest_path = dest_dir / file_path.name
        
        if dest_path.exists():
            dest_path.unlink()  # Replace existing
        
        shutil.move(str(file_path), str(dest_path))
        return dest_path
    
    def move_to_failed(self, file_path: Path, error_msg: str) -> Path:
        """Move failed file with error log"""
        file_type = self.get_file_type(file_path.name)
        dest_dir = self.dirs['failed'] / file_type
        dest_path = dest_dir / file_path.name
        
        # Save error log
        error_log_path = dest_path.with_suffix(dest_path.suffix + '.error.txt')
        error_log_path.write_text(f"Error: {error_msg}\nTimestamp: {datetime.now().isoformat()}\n")
        
        if dest_path.exists():
            dest_path.unlink()
        
        shutil.move(str(file_path), str(dest_path))
        logger.warning(f"Moved to failed: {dest_path}")
        logger.warning(f"Error log: {error_log_path}")
        
        return dest_path


class SharePointSyncManager:
    """Manages the complete SharePoint sync workflow"""
    
    def __init__(self, 
                 cookies_file='/workspace/001-bms-agent/sharepoint_cookies.txt',
                 csv_file='/workspace/001-bms-agent/docs/bms-docs-urls.md',
                 base_dir='/workspace/bms_data',
                 lookback_days=1):
        
        self.cookies_file = Path(cookies_file)
        self.csv_file = Path(csv_file)
        self.lookback_days = lookback_days
        
        # Calculate cutoff date (yesterday or custom)
        self.cutoff_date = (datetime.now() - timedelta(days=lookback_days)).strftime('%Y-%m-%d')
        
        # Initialize managers
        self.dir_manager = DirectoryManager(base_dir)
        self.downloader = None
        
        # Stats
        self.stats = {
            'downloaded': 0,
            'organized': 0,
            'processed': 0,
            'failed': 0,
            'skipped': 0
        }
    
    def initialize_downloader(self):
        """Initialize SharePoint downloader"""
        logger.info("Initializing SharePoint downloader...")
        
        # Use incoming directory as temporary download location
        temp_download_dir = self.dir_manager.base_dir / 'temp_downloads'
        temp_download_dir.mkdir(exist_ok=True)
        
        self.downloader = SharePointDownloader(
            cookies_file=self.cookies_file,
            cutoff_date=self.cutoff_date,
            output_dir=temp_download_dir
        )
        
        logger.info(f"✅ Downloader ready (cutoff: {self.cutoff_date})")
    
    def download_documents(self) -> List[Dict]:
        """Download new/updated documents from SharePoint"""
        logger.info("=" * 70)
        logger.info("STEP 1: DOWNLOADING FROM SHAREPOINT")
        logger.info("=" * 70)
        
        # Load document list
        documents = load_documents_from_csv(self.csv_file)
        logger.info(f"📋 Found {len(documents)} documents in catalog")
        
        # Download
        self.downloader.process_documents(documents, delay=2, max_retries=2)
        
        self.stats['downloaded'] = self.downloader.stats['downloaded']
        self.stats['skipped'] = self.downloader.stats['skipped']
        
        logger.info(f"✅ Downloaded: {self.stats['downloaded']}")
        logger.info(f"⏭️  Skipped: {self.stats['skipped']}")
        
        return documents
    
    def organize_downloads(self):
        """Organize downloaded files by type"""
        logger.info("\n" + "=" * 70)
        logger.info("STEP 2: ORGANIZING FILES BY TYPE")
        logger.info("=" * 70)
        
        temp_dir = self.dir_manager.base_dir / 'temp_downloads'
        downloaded_files = list(temp_dir.glob('*'))
        
        logger.info(f"📁 Found {len(downloaded_files)} files to organize")
        
        for file_path in downloaded_files:
            if file_path.is_file():
                try:
                    dest_path = self.dir_manager.organize_file(file_path, 'incoming')
                    logger.info(f"  ✅ {file_path.name} → {dest_path.parent.name}/")
                    self.stats['organized'] += 1
                except Exception as e:
                    logger.error(f"  ❌ Error organizing {file_path.name}: {e}")
        
        # Clean up temp directory
        if temp_dir.exists() and not list(temp_dir.iterdir()):
            temp_dir.rmdir()
        
        logger.info(f"✅ Organized: {self.stats['organized']} files")
    
    def process_documents(self):
        """Process documents with Enhanced Document Processor v4.0"""
        logger.info("\n" + "=" * 70)
        logger.info("STEP 3: PROCESSING DOCUMENTS")
        logger.info("=" * 70)
        
        # Get all files from incoming directory
        incoming_files = []
        for file_type in self.dir_manager.file_types:
            type_dir = self.dir_manager.dirs['incoming'] / file_type
            if type_dir.exists():
                incoming_files.extend(list(type_dir.glob('*')))
        
        logger.info(f"📄 Found {len(incoming_files)} files to process")
        
        if not incoming_files:
            logger.info("No files to process")
            return
        
        # Import processor
        try:
            from bms_agent.scr.enhanced_document_processor import EnhancedDocumentProcessor
            processor = EnhancedDocumentProcessor()
            logger.info("✅ Enhanced Document Processor v4.0 loaded")
        except Exception as e:
            logger.error(f"❌ Failed to load processor: {e}")
            return
        
        # Process each file
        for file_path in incoming_files:
            try:
                logger.info(f"\n📄 Processing: {file_path.name}")
                
                # Move to processing directory
                processing_path = self.dir_manager.move_to_processing(file_path)
                
                # Process document
                result = processor.process_document(str(processing_path))
                
                if result and result.get('status') == 'success':
                    # Move to processed
                    self.dir_manager.move_to_processed(processing_path)
                    self.stats['processed'] += 1
                    logger.info(f"  ✅ Processed successfully")
                else:
                    # Move to failed
                    error_msg = result.get('error', 'Unknown error') if result else 'Processing failed'
                    self.dir_manager.move_to_failed(processing_path, error_msg)
                    self.stats['failed'] += 1
                    logger.error(f"  ❌ Processing failed: {error_msg}")
                
            except Exception as e:
                logger.error(f"  ❌ Error processing {file_path.name}: {e}")
                # Move to failed if still in processing
                if processing_path.exists():
                    self.dir_manager.move_to_failed(processing_path, str(e))
                self.stats['failed'] += 1
        
        logger.info(f"\n✅ Processed: {self.stats['processed']}")
        logger.info(f"❌ Failed: {self.stats['failed']}")
    
    def generate_report(self) -> Dict:
        """Generate sync report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'cutoff_date': self.cutoff_date,
            'lookback_days': self.lookback_days,
            'stats': self.stats,
            'directories': {
                'incoming': len(list(self.dir_manager.dirs['incoming'].rglob('*.*'))),
                'processing': len(list(self.dir_manager.dirs['processing'].glob('*.*'))),
                'processed': len(list(self.dir_manager.dirs['processed'].rglob('*.*'))),
                'failed': len(list(self.dir_manager.dirs['failed'].rglob('*.*')))
            }
        }
        
        # Save report
        report_file = self.dir_manager.base_dir / f"sync_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"\n💾 Report saved: {report_file}")
        
        return report
    
    def print_summary(self):
        """Print final summary"""
        logger.info("\n" + "=" * 70)
        logger.info("🎉 SYNC COMPLETE")
        logger.info("=" * 70)
        logger.info(f"📅 Cutoff Date: {self.cutoff_date}")
        logger.info(f"⬇️  Downloaded: {self.stats['downloaded']}")
        logger.info(f"📁 Organized: {self.stats['organized']}")
        logger.info(f"✅ Processed: {self.stats['processed']}")
        logger.info(f"❌ Failed: {self.stats['failed']}")
        logger.info(f"⏭️  Skipped: {self.stats['skipped']}")
        logger.info("=" * 70)
        
        # Directory status
        logger.info("\n📊 Directory Status:")
        for name, path in self.dir_manager.dirs.items():
            if name in ['incoming', 'processed', 'failed']:
                count = len(list(path.rglob('*.*')))
                logger.info(f"  {name:12s}: {count:4d} files")
    
    def run(self):
        """Run the complete sync workflow"""
        try:
            logger.info("\n" + "=" * 70)
            logger.info("🚀 SHAREPOINT SYNC MANAGER STARTED")
            logger.info("=" * 70)
            logger.info(f"Timestamp: {datetime.now().isoformat()}")
            logger.info(f"Lookback: {self.lookback_days} days")
            logger.info(f"Cutoff Date: {self.cutoff_date}")
            
            # Step 1: Download
            self.initialize_downloader()
            self.download_documents()
            
            # Step 2: Organize
            self.organize_downloads()
            
            # Step 3: Process
            self.process_documents()
            
            # Generate report
            self.generate_report()
            
            # Print summary
            self.print_summary()
            
            return 0
            
        except KeyboardInterrupt:
            logger.warning("\n⚠️  Sync interrupted by user")
            return 1
        except Exception as e:
            logger.error(f"\n❌ Sync failed: {e}", exc_info=True)
            return 1


def main():
    parser = argparse.ArgumentParser(
        description='SharePoint Sync Manager - Automated document synchronization',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Daily sync (last 24 hours)
  python sharepoint_sync_manager.py
  
  # Sync last 7 days
  python sharepoint_sync_manager.py --lookback-days 7
  
  # Custom cutoff date
  python sharepoint_sync_manager.py --cutoff-date 2024-01-01
  
  # Dry run (download only, no processing)
  python sharepoint_sync_manager.py --download-only
        """
    )
    
    parser.add_argument(
        '--cookies',
        default='/workspace/001-bms-agent/sharepoint_cookies.txt',
        help='Path to cookies file'
    )
    parser.add_argument(
        '--csv',
        default='/workspace/001-bms-agent/docs/bms-docs-urls.md',
        help='Path to CSV file with URLs'
    )
    parser.add_argument(
        '--base-dir',
        default='/workspace/bms_data',
        help='Base directory for document management'
    )
    parser.add_argument(
        '--lookback-days',
        type=int,
        default=1,
        help='Number of days to look back for updates (default: 1)'
    )
    parser.add_argument(
        '--cutoff-date',
        help='Custom cutoff date (YYYY-MM-DD), overrides lookback-days'
    )
    parser.add_argument(
        '--download-only',
        action='store_true',
        help='Only download and organize, skip processing'
    )
    
    args = parser.parse_args()
    
    # Create sync manager
    manager = SharePointSyncManager(
        cookies_file=args.cookies,
        csv_file=args.csv,
        base_dir=args.base_dir,
        lookback_days=args.lookback_days
    )
    
    # Override cutoff date if specified
    if args.cutoff_date:
        manager.cutoff_date = args.cutoff_date
    
    # Run sync
    if args.download_only:
        manager.initialize_downloader()
        manager.download_documents()
        manager.organize_downloads()
        manager.print_summary()
        return 0
    else:
        return manager.run()


if __name__ == '__main__':
    exit(main())
