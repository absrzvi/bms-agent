#!/usr/bin/env python3
"""Process single document - no late chunking or contextual retrieval"""

import sys
import os
from pathlib import Path

# Set NLTK data path
os.environ['NLTK_DATA'] = '/workspace/nltk_data'

# Add paths
sys.path.insert(0, '/workspace/001-bms-agent')
sys.path.insert(0, '/workspace/001-bms-agent/bms-agent/scr')

from api.processor_wrapper import BMSDocumentProcessor

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('file_path', help='Path to document')
    args = parser.parse_args()

    # Initialize processor
    print("🚀 Initializing Document Processor (simplified)...")
    processor = BMSDocumentProcessor(
        qdrant_host='localhost',
        qdrant_port=6333,
        collection_name='nomad_bms_documents'
    )

    doc_path = Path(args.file_path)

    print(f"\n📄 Processing: {doc_path.name}")
    print(f"📦 Size: {doc_path.stat().st_size / (1024*1024):.2f} MB\n")

    try:
        result = processor.process_document(
            file_path=str(doc_path),
            processing_profile='railway',
            replace_existing=True
        )

        print(f"\n✅ SUCCESS: {doc_path.name}")
        print(f"   📊 Chunks created: {result.chunks_created}")
        print(f"   ⏱️  Processing time: {result.processing_time_ms / 1000:.2f}s")
        print(f"   🆔 Document ID: {result.document_id}")

    except Exception as e:
        print(f"\n❌ FAILED: {doc_path.name}")
        print(f"   Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
