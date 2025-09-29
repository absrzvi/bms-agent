#!/usr/bin/env python3
"""
Test Enhanced Document Processor v4.0 with Settings for More Chunks
Compare quality-optimized vs quantity-optimized settings
"""

import sys
from pathlib import Path

# Add paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "bms-agent" / "scr"))

from enhanced_document_processor import (
    EnhancedDocumentProcessor, ProcessingConfig, ProcessingProfile, ChunkingStrategy
)

def test_more_chunks_settings():
    """Test with settings optimized for more chunks"""
    
    # Configuration for MORE CHUNKS (quantity over quality)
    config_more_chunks = ProcessingConfig(
        chunk_size=800,         # Smaller chunks
        min_chunk_size=100,     # Lower minimum
        chunk_overlap=100,      # Less overlap
        quality_threshold=40.0, # Lower quality threshold
        min_quality_score=30.0, # Lower minimum quality
        chunking_strategy=ChunkingStrategy.SLIDING_WINDOW,
        processing_profile=ProcessingProfile.GENERAL,
        enable_contextual_retrieval=True,
        enable_late_chunking=False,  # Disable for more chunks
        enable_quality_validation=False,  # Disable filtering
        enable_hybrid_search=True,
        enable_advanced_preprocessing=True
    )
    
    # Configuration for QUALITY (current optimized)
    config_quality = ProcessingConfig(
        chunk_size=2000,
        min_chunk_size=300,
        chunk_overlap=400,
        quality_threshold=60.0,
        min_quality_score=50.0,
        chunking_strategy=ChunkingStrategy.SLIDING_WINDOW,
        processing_profile=ProcessingProfile.GENERAL,
        enable_contextual_retrieval=True,
        enable_late_chunking=True,
        enable_quality_validation=True,
        enable_hybrid_search=True,
        enable_advanced_preprocessing=True
    )
    
    # Test file
    test_file = '/workspace/windsurf-project/bms-doc-upload/doc/BMS-COMM-FOR-001 Bank Parent Company Guarantee Request Form.docx'
    
    print('🔍 COMPARING CHUNK GENERATION STRATEGIES')
    print('=' * 70)
    print(f'📄 Test File: {Path(test_file).name}')
    print()
    
    # Test 1: More Chunks Configuration
    print('📊 TEST 1: MORE CHUNKS CONFIGURATION')
    print('=' * 50)
    
    processor_more = EnhancedDocumentProcessor(config_more_chunks)
    result_more = processor_more.process_document(test_file)
    
    if result_more and result_more.get('processing_success'):
        chunks_more = result_more.get('chunks', [])
        quality_report_more = result_more.get('quality_report', {})
        
        print(f'✅ SUCCESS! More chunks configuration')
        print(f'   Final Chunks: {len(chunks_more)}')
        print(f'   Average Chunk Size: {sum(len(c.get("content", "")) for c in chunks_more) / len(chunks_more):.0f} chars' if chunks_more else 'N/A')
        
        # Show first few chunks
        print(f'\n📄 CHUNK SAMPLES (first 3):')
        for i, chunk in enumerate(chunks_more[:3]):
            content = chunk.get('content', '')
            print(f'\n🔸 Chunk {i+1}:')
            print(f'   Length: {len(content)} chars')
            
            # Show content preview
            if '<context>' in content and '</context>' in content:
                context_end = content.find('</context>')
                actual_content = content[context_end + 10:].strip()[:200]
                print(f'   Content: "{actual_content}..."')
            else:
                print(f'   Content: "{content[:200]}..."')
    
    print('\n' + '=' * 70)
    
    # Test 2: Quality Configuration
    print('📊 TEST 2: QUALITY CONFIGURATION (CURRENT)')
    print('=' * 50)
    
    processor_quality = EnhancedDocumentProcessor(config_quality)
    result_quality = processor_quality.process_document(test_file)
    
    if result_quality and result_quality.get('processing_success'):
        chunks_quality = result_quality.get('chunks', [])
        quality_report_quality = result_quality.get('quality_report', {})
        
        avg_quality = quality_report_quality.get('average_quality', 0)
        
        print(f'✅ SUCCESS! Quality configuration')
        print(f'   Final Chunks: {len(chunks_quality)}')
        print(f'   Average Quality: {avg_quality:.3f}')
        print(f'   Average Chunk Size: {sum(len(c.get("content", "")) for c in chunks_quality) / len(chunks_quality):.0f} chars' if chunks_quality else 'N/A')
        
        # Show chunks
        print(f'\n📄 CHUNK SAMPLES (first 3):')
        for i, chunk in enumerate(chunks_quality[:3]):
            content = chunk.get('content', '')
            quality_info = chunk.get('quality', {})
            
            print(f'\n🔸 Chunk {i+1}:')
            print(f'   Length: {len(content)} chars')
            if quality_info:
                print(f'   Quality: {quality_info.get("overall_score", 0):.3f}')
            
            # Show content preview
            if '<context>' in content and '</context>' in content:
                context_end = content.find('</context>')
                actual_content = content[context_end + 10:].strip()[:200]
                print(f'   Content: "{actual_content}..."')
            else:
                print(f'   Content: "{content[:200]}..."')
    
    # Comparison
    print('\n' + '=' * 70)
    print('🎯 COMPARISON SUMMARY')
    print('=' * 70)
    
    if result_more and result_quality:
        chunks_more_count = len(result_more.get('chunks', []))
        chunks_quality_count = len(result_quality.get('chunks', []))
        quality_score = result_quality.get('quality_report', {}).get('average_quality', 0)
        
        print(f'📊 CHUNK COUNT:')
        print(f'   More Chunks Config: {chunks_more_count} chunks')
        print(f'   Quality Config: {chunks_quality_count} chunks')
        print(f'   Difference: {chunks_more_count - chunks_quality_count:+d} chunks')
        
        print(f'\n📈 TRADE-OFFS:')
        print(f'   More Chunks → Better granularity, more detailed analysis')
        print(f'   Quality Config → Better context, higher quality ({quality_score:.3f})')
        
        print(f'\n💡 RECOMMENDATIONS:')
        print(f'   • Use MORE CHUNKS for: Detailed analysis, search indexing, fine-grained processing')
        print(f'   • Use QUALITY CONFIG for: Context preservation, high-quality output, enterprise use')
        print(f'   • Adjust chunk_size (400-2000) based on your specific needs')

if __name__ == "__main__":
    test_more_chunks_settings()
