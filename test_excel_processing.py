#!/usr/bin/env python3
"""Test Excel file processing with Enhanced Document Processor v4.0"""

import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path.cwd() / 'bms-agent' / 'scr'))

from enhanced_document_processor import (
    EnhancedDocumentProcessor, ProcessingConfig, ProcessingProfile, ChunkingStrategy
)

# XLSX-optimized configuration
config = ProcessingConfig(
    chunk_size=1000,
    min_chunk_size=150,
    chunk_overlap=200,
    quality_threshold=45.0,
    min_quality_score=35.0,
    chunking_strategy=ChunkingStrategy.SLIDING_WINDOW,
    processing_profile=ProcessingProfile.GENERAL,
    enable_contextual_retrieval=True,
    enable_late_chunking=False,
    enable_quality_validation=False,
    enable_hybrid_search=True,
    enable_advanced_preprocessing=True
)

processor = EnhancedDocumentProcessor(config)

# Test files
test_files = [
    '/workspace/bms_data/uploads/xls/BMS-PROJ-FOR-023 Control Plan.xlsx',
    '/workspace/bms_data/uploads/xls/BMS-PROJ-FOR-016 Commissioning Test Report.xlsx',
]

print('📊 TESTING EXCEL FILE PROCESSING')
print('=' * 70)

for test_file_path in test_files:
    test_file = Path(test_file_path)
    
    if not test_file.exists():
        print(f'⚠️  File not found: {test_file.name}')
        continue
    
    print(f'\n\n📄 FILE: {test_file.name}')
    print('=' * 70)
    
    # Step 1: Raw extraction
    print('\n🔍 STEP 1: Raw Content Extraction')
    print('-' * 50)
    raw_content = processor._read_document(test_file)
    print(f'✅ Extracted {len(raw_content)} characters')
    print(f'\n📊 First 800 characters of raw content:')
    print(raw_content[:800])
    print('\n...')
    
    # Step 2: Full processing
    print('\n\n🔍 STEP 2: Full Document Processing with Chunking')
    print('-' * 50)
    result = processor.process_document(test_file)
    
    if result and result.get('processing_success'):
        chunks = result.get('chunks', [])
        print(f'✅ Processing successful!')
        print(f'   Total chunks created: {len(chunks)}')
        
        # Show first 2 chunks in detail
        for i, chunk in enumerate(chunks[:2]):
            print(f'\n\n📦 CHUNK {i+1} DETAILS:')
            print('=' * 60)
            content = chunk.get('content', '')
            metadata = chunk.get('metadata', {})
            
            print(f'Content Length: {len(content)} chars')
            print(f'Chunk Type: {metadata.get("chunk_type", "N/A")}')
            print(f'Quality Score: {metadata.get("quality_score", "N/A")}')
            print(f'Has Context: {metadata.get("has_context", False)}')
            print(f'Hierarchy Level: {metadata.get("hierarchy_level", "N/A")}')
            print()
            print('📝 Content Preview (first 600 chars):')
            print(content[:600])
            print('\n...')
            print()
            print('🏷️  Metadata Keys:', list(metadata.keys()))
            if 'keywords' in metadata:
                keywords = metadata.get('keywords', [])
                print(f'🔑 Keywords ({len(keywords)}): {keywords[:15]}')
            if 'entities' in metadata:
                entities = metadata.get('entities', [])
                print(f'🎯 Entities ({len(entities)}): {entities[:15]}')
            if 'technical_terms' in metadata:
                terms = metadata.get('technical_terms', [])
                print(f'⚙️  Technical Terms ({len(terms)}): {terms[:15]}')
        
        if len(chunks) > 2:
            print(f'\n... and {len(chunks) - 2} more chunks')
            
    else:
        print('❌ Processing failed')
        if result:
            print(f'Error: {result.get("error", "Unknown")}')

print('\n\n✅ TEST COMPLETE!')
