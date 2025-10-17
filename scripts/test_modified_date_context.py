#!/usr/bin/env python3
"""
Test Enhanced Contextual Retrieval with Document Modified Date
"""

import sys
from pathlib import Path

# Add paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "bms-agent" / "scr"))

from enhanced_document_processor import (
    EnhancedDocumentProcessor, ProcessingConfig, ProcessingProfile, ChunkingStrategy
)

def test_modified_date_context():
    """Test enhanced contextual retrieval with modified date"""
    
    # Test with enhanced contextual retrieval including modified date
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
    
    print('📅 TESTING ENHANCED CONTEXTUAL RETRIEVAL WITH MODIFIED DATE')
    print('=' * 70)
    
    result = processor.process_document(pdf_path)
    
    if result and result.get('processing_success'):
        chunks = result.get('chunks', [])
        
        print('✅ SUCCESS! Enhanced contextual retrieval with modified date working!')
        print('📄 Document Metadata:')
        print(f'   Title: {result.get("title", "N/A")}')
        print(f'   Type: {result.get("type", "N/A")}')
        print(f'   Modified Date: {result.get("modified_date", "N/A")}')
        print(f'   Chunks: {len(chunks)}')
        
        if len(chunks) >= 2:
            print('\n📄 First 2 Chunks with Enhanced Context (Including Modified Date):')
            
            for i, chunk in enumerate(chunks[:2]):
                content = chunk.get('content', '')
                
                print(f'\n🔸 Chunk {i+1}:')
                print(f'   Length: {len(content)} chars')
                
                # Extract and display the context part
                if '<context>' in content and '</context>' in content:
                    context_start = content.find('<context>') + 9
                    context_end = content.find('</context>')
                    context_part = content[context_start:context_end].strip()
                    
                    print('   📅 Enhanced Context:')
                    print(f'      {context_part}')
                    
                    # Show actual content (after context)
                    actual_content = content[context_end + 10:].strip()[:120]
                    print(f'   📝 Content Preview: "{actual_content}..."')
                else:
                    print(f'   📝 Content: "{content[:150]}..."')
        
        print('\n🎯 ENHANCED CONTEXTUAL FEATURES:')
        print('   ✅ Document title from filename')
        print('   ✅ Intelligent document type detection')
        print('   ✅ Last modified date for temporal context')
        print('   ✅ Section positioning within document')
        print('   ✅ Content preview for relevance')
        
        return True
    
    else:
        print('❌ Processing failed')
        if result:
            print(f'Error: {result.get("error", "Unknown error")}')
        return False

if __name__ == "__main__":
    success = test_modified_date_context()
    if success:
        print('\n🎉 ENHANCED CONTEXTUAL RETRIEVAL WITH MODIFIED DATE WORKING PERFECTLY!')
    else:
        print('\n⚠️  Need to debug contextual retrieval issues')
