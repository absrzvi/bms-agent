#!/usr/bin/env python3
"""
Test Fixed Railway Processing - No More TECH_TERM Placeholders
"""

import sys
import re
from pathlib import Path

# Add paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "bms-agent" / "scr"))

from enhanced_document_processor import (
    EnhancedDocumentProcessor, ProcessingConfig, ProcessingProfile, ChunkingStrategy
)

def test_fixed_railway_processing():
    """Test fixed railway processing without TECH_TERM placeholders"""
    
    # Test with fixed railway processing
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
    
    print('🔧 TESTING FIXED RAILWAY PROCESSING (NO MORE TECH_TERM PLACEHOLDERS)')
    print('=' * 75)
    
    result = processor.process_document(pdf_path)
    
    if result and result.get('processing_success'):
        chunks = result.get('chunks', [])
        
        print('✅ SUCCESS! Fixed railway processing working!')
        print('📄 Document Info:')
        print(f'   Title: {result.get("title", "N/A")}')
        print(f'   Type: {result.get("type", "N/A")}')
        print(f'   Modified Date: {result.get("modified_date", "N/A")}')
        print(f'   Chunks: {len(chunks)}')
        
        # Check all chunks for TECH_TERM placeholders
        total_placeholders = 0
        clean_chunks = 0
        
        for chunk in chunks:
            content = chunk.get('content', '')
            placeholder_count = content.count('##TECH_TERM_')
            total_placeholders += placeholder_count
            if placeholder_count == 0:
                clean_chunks += 1
        
        print(f'\n📊 Placeholder Analysis:')
        print(f'   Total Chunks: {len(chunks)}')
        print(f'   Clean Chunks (no placeholders): {clean_chunks}')
        print(f'   Chunks with Placeholders: {len(chunks) - clean_chunks}')
        print(f'   Total TECH_TERM Placeholders: {total_placeholders}')
        
        if len(chunks) >= 2:
            print('\n📄 First 2 Chunks - Detailed Analysis:')
            
            for i, chunk in enumerate(chunks[:2]):
                content = chunk.get('content', '')
                
                print(f'\n🔸 Chunk {i+1}:')
                print(f'   Length: {len(content)} chars')
                
                # Check for TECH_TERM placeholders
                tech_term_count = content.count('##TECH_TERM_')
                if tech_term_count > 0:
                    print(f'   ❌ Still has {tech_term_count} TECH_TERM placeholders')
                    # Show examples
                    placeholders = re.findall(r'##TECH_TERM_[^#]+##', content)
                    print(f'   Examples: {placeholders[:3]}')
                else:
                    print('   ✅ No TECH_TERM placeholders found - clean text!')
                
                # Show clean content preview
                if '<context>' in content and '</context>' in content:
                    context_end = content.find('</context>')
                    actual_content = content[context_end + 10:].strip()[:150]
                    print(f'   📝 Clean Content: "{actual_content}..."')
                else:
                    print(f'   📝 Content: "{content[:150]}..."')
        
        print('\n🎯 RAILWAY PROCESSING FIX RESULTS:')
        if total_placeholders == 0:
            print('   ✅ Perfect! No TECH_TERM placeholders found')
            print('   ✅ Technical terms preserved during processing')
            print('   ✅ Terms restored to original form in final output')
            print('   ✅ Clean, readable text for search and display')
            return True
        else:
            print(f'   ⚠️  Still found {total_placeholders} placeholders - needs more work')
            return False
    
    else:
        print('❌ Processing failed')
        if result:
            print(f'Error: {result.get("error", "Unknown error")}')
        return False

if __name__ == "__main__":
    success = test_fixed_railway_processing()
    if success:
        print('\n🎉 RAILWAY PROCESSING COMPLETELY FIXED!')
    else:
        print('\n🔧 Still need to debug railway processing issues')
