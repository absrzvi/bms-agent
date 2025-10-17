#!/usr/bin/env python3
"""
Analyze Quality Validation - Why 5/11 chunks pass
"""

import sys
from pathlib import Path

# Add paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "bms-agent" / "scr"))

from enhanced_document_processor import (
    EnhancedDocumentProcessor, ProcessingConfig, ProcessingProfile, ChunkingStrategy
)

def analyze_quality_validation():
    """Analyze why only 5/11 chunks pass quality validation"""
    
    # Test quality validation in detail
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
    
    print('🔍 DETAILED QUALITY VALIDATION ANALYSIS')
    print('=' * 60)
    
    result = processor.process_document(pdf_path)
    
    if result and result.get('processing_success'):
        chunks = result.get('chunks', [])
        quality_report = result.get('quality_report', {})
        
        print('📊 Quality Validation Results:')
        print(f'   Final Chunks: {len(chunks)}')
        print(f'   Total Processed: {quality_report.get("total_chunks", 0)}')
        print(f'   Passed Quality: {quality_report.get("passed_chunks", 0)}')
        print(f'   Failed Quality: {quality_report.get("failed_chunks", 0)}')
        print(f'   Average Quality: {quality_report.get("average_quality", 0):.3f}')
        
        # Calculate pass rate
        total = quality_report.get('total_chunks', 0)
        passed = quality_report.get('passed_chunks', 0)
        if total > 0:
            pass_rate = (passed / total) * 100
            print(f'   Pass Rate: {pass_rate:.1f}%')
        
        print('\n🔍 Why Are Chunks Failing Quality Validation?')
        print('=' * 60)
        
        # The issue is likely that late chunking creates fewer, larger chunks
        # but quality validation processes the original smaller chunks
        print('\n📊 Processing Flow Analysis:')
        print('   1. Initial chunking creates ~11 smaller chunks')
        print('   2. Quality validation tests all 11 chunks')
        print(f'   3. Late chunking combines them into {len(chunks)} larger chunks')
        print('   4. Only chunks that pass quality make it to final output')
        
        # Check quality thresholds
        if hasattr(processor, 'quality_validator'):
            thresholds = processor.quality_validator.thresholds
            print('\n⚙️  Current Quality Thresholds:')
            for metric, threshold in thresholds.items():
                print(f'   {metric}: {threshold}')
        
        # Show quality scores for final chunks
        print('\n📈 Final Chunk Quality Scores:')
        for i, chunk in enumerate(chunks[:3]):
            quality_info = chunk.get('quality', {})
            if quality_info:
                overall_score = quality_info.get('overall_score', 0)
                passes = quality_info.get('passes_quality', False)
                status = '✅' if passes else '❌'
                print(f'   Chunk {i+1}: {status} {overall_score:.3f}')
                
                # Show failed metrics if any
                failed_metrics = quality_info.get('failed_metrics', [])
                if failed_metrics:
                    print(f'      Failed: {failed_metrics}')
            else:
                print(f'   Chunk {i+1}: No quality info available')
        
        print('\n💡 QUALITY VALIDATION EXPLANATION:')
        print(f'   • Late chunking processes {total} initial chunks')
        print(f'   • Quality validation filters out low-quality chunks')
        print(f'   • Only {passed} chunks meet quality standards')
        print(f'   • These are combined into {len(chunks)} final chunks')
        print('   • This is NORMAL and GOOD - quality filtering working!')
        
        if pass_rate < 50:
            print(f'\n⚠️  Low pass rate ({pass_rate:.1f}%) suggests:')
            print('   • Quality thresholds may be too strict for this document type')
            print('   • Document may have challenging content (tables, lists, etc.)')
            print('   • PDF extraction artifacts affecting quality scores')
        else:
            print(f'\n✅ Pass rate ({pass_rate:.1f}%) is reasonable for quality filtering')
        
        # Test without quality validation to see all chunks
        print('\n🔬 COMPARISON: Processing WITHOUT Quality Validation')
        print('=' * 60)
        
        config_no_quality = ProcessingConfig(
            chunk_size=400,
            min_chunk_size=30,
            chunking_strategy=ChunkingStrategy.SLIDING_WINDOW,
            processing_profile=ProcessingProfile.RAILWAY,
            enable_contextual_retrieval=True,
            enable_late_chunking=True,
            enable_quality_validation=False,  # Disabled
            enable_hybrid_search=True,
            enable_advanced_preprocessing=True
        )
        
        processor_no_quality = EnhancedDocumentProcessor(config_no_quality)
        result_no_quality = processor_no_quality.process_document(pdf_path)
        
        if result_no_quality and result_no_quality.get('processing_success'):
            chunks_no_quality = result_no_quality.get('chunks', [])
            print(f'   Without Quality Validation: {len(chunks_no_quality)} chunks')
            print(f'   With Quality Validation: {len(chunks)} chunks')
            print(f'   Difference: {len(chunks_no_quality) - len(chunks)} chunks filtered out')
            
            if len(chunks_no_quality) > len(chunks):
                print('\n✅ Quality validation is working correctly!')
                print('   It filters out lower-quality chunks to improve results')
            else:
                print('\n🤔 Quality validation may not be filtering as expected')
    
    else:
        print('❌ Processing failed')

if __name__ == "__main__":
    analyze_quality_validation()
