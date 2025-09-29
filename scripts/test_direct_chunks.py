#!/usr/bin/env python3
"""
Direct test of Enhanced Document Processor to see actual chunks
"""

import sys
from pathlib import Path

# Add paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "bms-agent" / "scr"))

from enhanced_document_processor import (
    EnhancedDocumentProcessor, ProcessingConfig, ProcessingProfile, ChunkingStrategy
)

def test_direct_processing():
    """Test the processor directly to see chunks"""
    
    # Configuration that we know works
    config = ProcessingConfig(
        chunk_size=400,
        min_chunk_size=30,
        quality_threshold=30.0,
        chunking_strategy=ChunkingStrategy.SLIDING_WINDOW,
        processing_profile=ProcessingProfile.TECHNICAL,
        
        # Disable complex features
        enable_contextual_retrieval=False,
        enable_late_chunking=False,
        enable_quality_validation=False,
        enable_hybrid_search=False,
        enable_advanced_preprocessing=True
    )
    
    processor = EnhancedDocumentProcessor(config)
    pdf_path = '/workspace/windsurf-project/bms-doc-upload/pdf/BMS-QHSE-PRO-001 Risk Management.pdf'
    
    print('🔍 Testing direct processor call...')
    result = processor.process_document(pdf_path)
    
    print(f'Result type: {type(result)}')
    print(f'Result keys: {list(result.keys()) if isinstance(result, dict) else "Not a dict"}')
    
    if result and isinstance(result, dict):
        print(f'Status: {result.get("status")}')
        chunks = result.get('chunks', [])
        print(f'Chunks found: {len(chunks)}')
        
        if chunks:
            print(f'\n📄 First 5 chunks:')
            for i, chunk in enumerate(chunks[:5]):
                print(f'\n🔸 Chunk {i+1}:')
                print(f'   Type: {type(chunk)}')
                
                if isinstance(chunk, dict):
                    print(f'   Keys: {list(chunk.keys())}')
                    content = chunk.get('content', '')
                    print(f'   Content length: {len(content)} characters')
                    
                    # Clean up the content preview
                    preview = content.strip()[:200]
                    if len(content) > 200:
                        preview += "..."
                    print(f'   Content preview: {repr(preview)}')
                    
                    # Show other metadata
                    for key, value in chunk.items():
                        if key != 'content':
                            print(f'   {key}: {value}')
                else:
                    print(f'   Content: {repr(str(chunk)[:100])}')
        else:
            print('❌ No chunks in result')
            
        # Show other result metadata
        print(f'\n📊 Result metadata:')
        for key, value in result.items():
            if key != 'chunks':
                print(f'   {key}: {value}')
                
    else:
        print('❌ No result or invalid result format')
        print(f'Raw result: {result}')

if __name__ == "__main__":
    test_direct_processing()
