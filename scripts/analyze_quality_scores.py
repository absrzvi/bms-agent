#!/usr/bin/env python3
"""
Analyze quality scores in detail to understand why they're low
"""

import sys
from pathlib import Path

# Add paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "bms-agent" / "scr"))

from enhanced_document_processor import (
    EnhancedDocumentProcessor, ProcessingConfig, ProcessingProfile, ChunkingStrategy
)

def analyze_quality_in_detail():
    """Analyze quality scores in detail"""
    
    config = ProcessingConfig(
        chunk_size=400,
        min_chunk_size=30,
        quality_threshold=30.0,
        min_quality_score=0.5,
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
    
    print('🔍 DETAILED QUALITY SCORE ANALYSIS')
    print('=' * 70)
    
    # Get the original document text for comparison
    original_text = processor._read_document(Path(pdf_path))
    print(f'📄 Original document: {len(original_text)} characters')
    
    # Process with quality validation disabled first to get raw chunks
    config_no_quality = ProcessingConfig(
        chunk_size=400,
        min_chunk_size=30,
        quality_threshold=30.0,
        min_quality_score=0.5,
        chunking_strategy=ChunkingStrategy.SLIDING_WINDOW,
        processing_profile=ProcessingProfile.RAILWAY,
        enable_contextual_retrieval=False,  # Disable to get clean chunks
        enable_late_chunking=False,
        enable_quality_validation=False,
        enable_hybrid_search=False,
        enable_advanced_preprocessing=True
    )
    
    processor_no_quality = EnhancedDocumentProcessor(config_no_quality)
    result_raw = processor_no_quality.process_document(pdf_path)
    
    if result_raw and result_raw.get('processing_success'):
        raw_chunks = result_raw.get('chunks', [])
        print(f'📊 Raw chunks (no quality validation): {len(raw_chunks)}')
        
        # Analyze first 3 chunks in detail
        quality_validator = processor.quality_validator
        
        for i, chunk in enumerate(raw_chunks[:3]):
            print(f'\\n🔸 CHUNK {i+1} QUALITY ANALYSIS:')
            print('-' * 50)
            
            content = chunk.get('content', '')
            print(f'📝 Content ({len(content)} chars):')
            print(f'   \"{content[:150]}...\"')
            
            # Get detailed quality metrics
            quality_result = quality_validator.validate_chunk_quality(
                chunk, original_text, context=None
            )
            
            metrics = quality_result['metrics']
            overall_score = quality_result['overall_score']
            passes = quality_result['passes_quality']
            failed_metrics = quality_result['failed_metrics']
            
            print(f'\\n📊 Quality Metrics:')
            print(f'   Overall Score: {overall_score:.3f}')
            status_icon = "✅" if passes else "❌"
            print(f'   Passes Quality: {status_icon}')
            
            print(f'\\n📈 Individual Metrics:')
            for metric, score in metrics.items():
                threshold = quality_validator.thresholds.get(metric, 0.5)
                status_icon = "✅" if score >= threshold else "❌"
                print(f'   {status_icon} {metric}: {score:.3f} (threshold: {threshold})')
            
            if failed_metrics:
                print(f'\\n❌ Failed Metrics: {failed_metrics}')
            
            # Explain why scores might be low
            print(f'\\n🔍 Analysis:')
            
            if metrics['faithfulness'] < 0.7:
                score = metrics['faithfulness']
                print(f'   • Low Faithfulness ({score:.3f}): Chunk content may not match original well')
            
            if metrics['context_recall'] < 0.5:
                score = metrics['context_recall']
                print(f'   • Low Recall ({score:.3f}): Chunk may not capture enough key information')
            
            if metrics['semantic_similarity'] < 0.3:
                score = metrics['semantic_similarity']
                print(f'   • Low Semantic Similarity ({score:.3f}): Limited word overlap with original')
            
            if metrics['information_density'] < 0.6:
                score = metrics['information_density']
                print(f'   • Low Information Density ({score:.3f}): Too many repeated words or low content')
            
            if metrics['readability_score'] < 0.6:
                score = metrics['readability_score']
                print(f'   • Low Readability ({score:.3f}): Text may be hard to read or fragmented')
        
        # Calculate what would improve scores
        print(f'\\n' + '=' * 70)
        print(f'💡 RECOMMENDATIONS TO IMPROVE QUALITY SCORES:')
        print('=' * 70)
        
        avg_scores = {}
        for metric in ['faithfulness', 'answer_relevancy', 'context_precision', 'context_recall', 
                      'semantic_similarity', 'information_density', 'readability_score']:
            scores = [quality_validator.validate_chunk_quality(chunk, original_text)['metrics'][metric] 
                     for chunk in raw_chunks[:5]]
            avg_scores[metric] = sum(scores) / len(scores)
        
        print(f'\\n📊 Average Scores Across First 5 Chunks:')
        for metric, avg_score in avg_scores.items():
            threshold = quality_validator.thresholds.get(metric, 0.5)
            status_icon = "✅" if avg_score >= threshold else "❌"
            print(f'   {status_icon} {metric}: {avg_score:.3f}')
        
        # Identify the main issues
        low_scores = [(metric, score) for metric, score in avg_scores.items() if score < 0.6]
        
        if low_scores:
            print(f'\\n🔧 Main Issues (scores < 0.6):')
            for metric, score in sorted(low_scores, key=lambda x: x[1]):
                print(f'   • {metric}: {score:.3f}')
                
                if metric == 'context_recall':
                    print(f'     → Chunks may be too small or missing key sentences')
                elif metric == 'semantic_similarity':
                    print(f'     → Limited vocabulary overlap (common with technical docs)')
                elif metric == 'information_density':
                    print(f'     → Too many repeated words or filler content')
                elif metric == 'readability_score':
                    print(f'     → Text fragmentation from PDF extraction artifacts')
                elif metric == 'faithfulness':
                    print(f'     → Chunks may not accurately represent original content')
        
        # Suggest threshold adjustments
        print(f'\\n⚙️  SUGGESTED THRESHOLD ADJUSTMENTS:')
        for metric, avg_score in avg_scores.items():
            current_threshold = quality_validator.thresholds.get(metric, 0.5)
            if avg_score < current_threshold:
                suggested = max(avg_score - 0.1, 0.1)  # 10% below average, minimum 0.1
                print(f'   {metric}: {current_threshold:.2f} → {suggested:.2f}')

if __name__ == "__main__":
    analyze_quality_in_detail()
