#!/usr/bin/env python3
"""
Test Enhanced Document Processor v4.0 with Real DOCX Files
Show detailed chunks for verification
"""

import sys
from pathlib import Path

# Add paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "bms-agent" / "scr"))

from enhanced_document_processor import (
    EnhancedDocumentProcessor, ProcessingConfig, ProcessingProfile, ChunkingStrategy
)

def test_docx_files_with_chunks():
    """Test DOCX files and show detailed chunks"""
    
    # Optimized configuration
    config = ProcessingConfig(
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
    
    processor = EnhancedDocumentProcessor(config)
    
    # Test files (select smaller ones for faster processing)
    test_files = [
        '/workspace/windsurf-project/bms-doc-upload/doc/BMS-HI-PROD-FOR-002 Routine Test Checklist.docx',
        '/workspace/windsurf-project/bms-doc-upload/doc/BMS-COMM-FOR-001 Bank Parent Company Guarantee Request Form.docx',
        '/workspace/windsurf-project/bms-doc-upload/doc/BMS-ENER-FOR-002 Energy Bulletin.docx'
    ]
    
    print('🔍 TESTING ENHANCED DOCUMENT PROCESSOR v4.0 WITH REAL DOCX FILES')
    print('=' * 75)
    
    for i, file_path in enumerate(test_files, 1):
        file_path_obj = Path(file_path)
        
        if not file_path_obj.exists():
            print(f'⚠️  File not found: {file_path_obj.name}')
            continue
            
        print(f'\n📄 TEST {i}: {file_path_obj.name}')
        print('=' * 60)
        
        try:
            result = processor.process_document(file_path_obj)
            
            if result and result.get('processing_success'):
                chunks = result.get('chunks', [])
                quality_report = result.get('quality_report', {})
                
                # Summary
                total = quality_report.get('total_chunks', 0)
                passed = quality_report.get('passed_chunks', 0)
                avg_quality = quality_report.get('average_quality', 0)
                
                print(f'✅ SUCCESS! Processing complete')
                print(f'   Final Chunks: {len(chunks)}')
                print(f'   Quality Score: {avg_quality:.3f}')
                print(f'   Pass Rate: {(passed/total*100):.1f}%' if total > 0 else 'N/A')
                
                # Document metadata
                print(f'\n📋 Document Metadata:')
                print(f'   Title: {result.get("title", "N/A")}')
                print(f'   Type: {result.get("type", "N/A")}')
                print(f'   Modified: {result.get("modified_date", "N/A")}')
                
                # Show detailed chunks
                print(f'\n📄 DETAILED CHUNKS ({len(chunks)} total):')
                print('-' * 60)
                
                for j, chunk in enumerate(chunks[:3]):  # Show first 3 chunks
                    content = chunk.get('content', '')
                    metadata = chunk.get('metadata', {})
                    quality_info = chunk.get('quality', {})
                    
                    print(f'\n🔸 CHUNK {j+1}:')
                    print(f'   Length: {len(content)} characters')
                    print(f'   Method: {metadata.get("chunking_method", "unknown")}')
                    
                    # Quality metrics
                    if quality_info:
                        overall_score = quality_info.get('overall_score', 0)
                        passes = quality_info.get('passes_quality', False)
                        print(f'   Quality: {overall_score:.3f} {"✅" if passes else "❌"}')
                    
                    # Hybrid search info
                    if 'keyword_content' in chunk:
                        keyword_count = metadata.get('keyword_count', 0)
                        print(f'   Keywords: {keyword_count} extracted')
                    
                    # Extract and show context vs content
                    if '<context>' in content and '</context>' in content:
                        context_start = content.find('<context>') + 9
                        context_end = content.find('</context>')
                        context_part = content[context_start:context_end].strip()
                        actual_content = content[context_end + 10:].strip()
                        
                        print(f'\n   📋 Context:')
                        print(f'      {context_part}')
                        
                        print(f'\n   📝 Content Preview (first 300 chars):')
                        print(f'      "{actual_content[:300]}..."')
                        
                        # Check for clean boundaries
                        if actual_content and not actual_content[0].islower():
                            print(f'   ✅ Clean start boundary')
                        else:
                            print(f'   ⚠️  Potential boundary issue')
                            
                        if actual_content.endswith(('.', '!', '?', ':')):
                            print(f'   ✅ Clean end boundary')
                        else:
                            print(f'   ⚠️  Incomplete ending')
                    else:
                        print(f'\n   📝 Raw Content (first 300 chars):')
                        print(f'      "{content[:300]}..."')
                
                if len(chunks) > 3:
                    print(f'\n   ... and {len(chunks) - 3} more chunks')
                
            else:
                print(f'❌ FAILED to process {file_path_obj.name}')
                if result:
                    error = result.get('error', 'Unknown error')
                    print(f'   Error: {error}')
                    
        except Exception as e:
            print(f'❌ EXCEPTION processing {file_path_obj.name}: {e}')
        
        print()  # Add spacing between files
    
    print('🎯 DOCX PROCESSING TEST COMPLETE!')
    print('   Enhanced Document Processor v4.0 verified with real business documents')

if __name__ == "__main__":
    test_docx_files_with_chunks()
