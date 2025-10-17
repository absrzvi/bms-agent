#!/usr/bin/env python3
"""Process the two new uploaded documents with enhanced processor"""

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
    # Initialize processor
    print("🚀 Initializing Enhanced Document Processor v4.0...")
    processor = BMSDocumentProcessor(
        qdrant_host='localhost',
        qdrant_port=6333,
        collection_name='nomad_bms_documents'
    )

    # Documents to process
    docs_dir = Path('/workspace/bms_data/new_docs')
    documents = list(docs_dir.glob('*'))

    print(f"\n📚 Found {len(documents)} documents to process\n")

    results = []
    for doc_path in documents:
        print(f"{'='*70}")
        print(f"📄 Processing: {doc_path.name}")
        print(f"📦 Size: {doc_path.stat().st_size / (1024*1024):.2f} MB")
        print(f"{'='*70}\n")

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

            results.append({
                'filename': doc_path.name,
                'status': 'success',
                'chunks': result.chunks_created,
                'doc_id': result.document_id
            })

        except Exception as e:
            print(f"\n❌ FAILED: {doc_path.name}")
            print(f"   Error: {str(e)}")
            results.append({
                'filename': doc_path.name,
                'status': 'failed',
                'error': str(e)
            })

        print(f"\n")

    # Summary
    print(f"{'='*70}")
    print(f"📊 PROCESSING SUMMARY")
    print(f"{'='*70}")

    successful = [r for r in results if r['status'] == 'success']
    failed = [r for r in results if r['status'] == 'failed']

    print(f"✅ Successful: {len(successful)}")
    print(f"❌ Failed: {len(failed)}")
    print(f"📊 Total chunks created: {sum(r.get('chunks', 0) for r in successful)}")

    if successful:
        print(f"\n✅ Successfully processed:")
        for r in successful:
            print(f"   - {r['filename']}: {r['chunks']} chunks")

    if failed:
        print(f"\n❌ Failed to process:")
        for r in failed:
            print(f"   - {r['filename']}: {r.get('error', 'Unknown error')}")

if __name__ == '__main__':
    main()
