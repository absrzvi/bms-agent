#!/usr/bin/env python3
"""
Show All Metadata for Enhanced Document Processor v4.0 Chunks
"""

import sys
import json
from pathlib import Path

# Add paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "bms-agent" / "scr"))

from enhanced_document_processor import (
    EnhancedDocumentProcessor, ProcessingConfig, ProcessingProfile, ChunkingStrategy
)

def show_all_metadata():
    """Show comprehensive metadata for all chunks"""
    
    # Full feature configuration
    config = ProcessingConfig(
        chunk_size=400,
        min_chunk_size=30,
        quality_threshold=60.0,
        min_quality_score=50.0,
        chunking_strategy=ChunkingStrategy.SLIDING_WINDOW,
        processing_profile=ProcessingProfile.RAILWAY,
        enable_contextual_retrieval=True,
        enable_late_chunking=True,
        enable_quality_validation=True,
        enable_hybrid_search=True,
        enable_advanced_preprocessing=True
    )
    
    processor = EnhancedDocumentProcessor(config)
    pdf_path = '/workspace/windsurf-project/bms-doc-upload/pdf/BMS-QHSE-PRO-001 Risk Management.pdf'
    
    print('📊 COMPREHENSIVE METADATA ANALYSIS - ENHANCED DOCUMENT PROCESSOR v4.0')
    print('=' * 80)
    
    result = processor.process_document(pdf_path)
    
    if result and result.get('processing_success'):
        chunks = result.get('chunks', [])
        
        print('🎉 SUCCESS! Full metadata extraction working!')
        
        # Document-level metadata
        print('\n📄 DOCUMENT-LEVEL METADATA:')
        print('=' * 50)
        
        doc_metadata = {
            'document_id': result.get('document_id'),
            'title': result.get('title'),
            'type': result.get('type'),
            'file_name': result.get('file_name'),
            'file_path': result.get('file_path'),
            'modified_date': result.get('modified_date'),
            'processing_timestamp': result.get('processing_timestamp'),
            'total_chunks': len(chunks)
        }
        
        for key, value in doc_metadata.items():
            print(f'   {key}: {value}')
        
        # Processing configuration
        config_info = result.get('config', {})
        if config_info:
            print('\n⚙️  PROCESSING CONFIGURATION:')
            print('=' * 50)
            for key, value in config_info.items():
                print(f'   {key}: {value}')
        
        # Quality report
        quality_report = result.get('quality_report', {})
        if quality_report:
            print('\n📈 QUALITY VALIDATION REPORT:')
            print('=' * 50)
            for key, value in quality_report.items():
                print(f'   {key}: {value}')
        
        # Document statistics
        statistics = result.get('statistics', {})
        if statistics:
            print('\n📊 DOCUMENT STATISTICS:')
            print('=' * 50)
            for key, value in statistics.items():
                print(f'   {key}: {value}')
        
        # Entity extraction
        entities = result.get('entities', {})
        if entities:
            print('\n🏷️  ENTITY EXTRACTION:')
            print('=' * 50)
            for key, value in entities.items():
                if isinstance(value, list):
                    print(f'   {key}: {value[:10]}')  # Show first 10 items
                else:
                    print(f'   {key}: {value}')
        
        # Railway-specific metadata
        railway_metadata = result.get('railway_metadata', {})
        if railway_metadata:
            print('\n🚂 RAILWAY-SPECIFIC METADATA:')
            print('=' * 50)
            for key, value in railway_metadata.items():
                if isinstance(value, dict):
                    print(f'   {key}:')
                    for subkey, subvalue in value.items():
                        if isinstance(subvalue, list):
                            print(f'      {subkey}: {subvalue[:5]}')  # Show first 5
                        else:
                            print(f'      {subkey}: {subvalue}')
                else:
                    print(f'   {key}: {value}')
        
        # Show first 3 chunks with complete metadata
        print(f'\n📄 FIRST 3 CHUNKS - COMPLETE METADATA:')
        print('=' * 80)
        
        for i, chunk in enumerate(chunks[:3]):
            print(f'\n🔸 CHUNK {i+1} METADATA:')
            print('-' * 60)
            
            # Basic chunk info
            content = chunk.get('content', '')
            print(f'📝 Content Length: {len(content)} characters')
            
            # Extract context and actual content
            if '<context>' in content and '</context>' in content:
                context_start = content.find('<context>') + 9
                context_end = content.find('</context>')
                context_part = content[context_start:context_end].strip()
                actual_content = content[context_end + 10:].strip()
                
                print(f'🔗 Context: {context_part}')
                print(f'📄 Actual Content Preview: "{actual_content[:200]}..."')
            else:
                print(f'📄 Content Preview: "{content[:200]}..."')
            
            # All chunk metadata
            print(f'\n📋 Complete Chunk Metadata:')
            chunk_metadata = {}
            for key, value in chunk.items():
                if key != 'content':  # Don't repeat the content
                    chunk_metadata[key] = value
            
            # Pretty print metadata
            if chunk_metadata:
                for key, value in chunk_metadata.items():
                    if isinstance(value, dict):
                        print(f'   {key}:')
                        for subkey, subvalue in value.items():
                            print(f'      {subkey}: {subvalue}')
                    elif isinstance(value, list):
                        if len(value) <= 5:
                            print(f'   {key}: {value}')
                        else:
                            print(f'   {key}: {value[:5]}... ({len(value)} total)')
                    else:
                        print(f'   {key}: {value}')
            else:
                print('   No additional metadata')
        
        # Version info
        version_info = result.get('version_info', {})
        if version_info:
            print(f'\n📋 VERSION TRACKING:')
            print('=' * 50)
            for key, value in version_info.items():
                if key == 'content':
                    print(f'   {key}: {len(str(value))} characters')
                elif isinstance(value, list):
                    print(f'   {key}: {len(value)} items')
                else:
                    print(f'   {key}: {value}')
        
        # Processing errors (if any)
        errors = result.get('errors', [])
        if errors:
            print(f'\n⚠️  PROCESSING ERRORS:')
            print('=' * 50)
            for error in errors:
                print(f'   {error}')
        else:
            print(f'\n✅ NO PROCESSING ERRORS')
        
        return True
    
    else:
        print('❌ Processing failed')
        if result:
            print(f'Error: {result.get("error", "Unknown error")}')
        return False

if __name__ == "__main__":
    success = show_all_metadata()
    if success:
        print('\n🎯 COMPREHENSIVE METADATA EXTRACTION COMPLETE!')
        print('   All Enhanced Document Processor v4.0 features working with full metadata')
    else:
        print('\n⚠️  Metadata extraction issues detected')
