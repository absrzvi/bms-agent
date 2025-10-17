#!/usr/bin/env python3
"""
Detailed Quality Diagnostic - Analyze ALL quality issues in chunks
"""

import sys
from pathlib import Path

# Add paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "bms-agent" / "scr"))

from enhanced_document_processor import (
    EnhancedDocumentProcessor, ProcessingConfig, ProcessingProfile, ChunkingStrategy
)

def detailed_quality_diagnostic():
    """Analyze all chunks to identify specific quality issues"""
    
    # Test with quality validation to get detailed metrics
    config = ProcessingConfig(
        chunk_size=400,
        min_chunk_size=30,
        quality_threshold=60.0,
        min_quality_score=50.0,
        chunking_strategy=ChunkingStrategy.SLIDING_WINDOW,
        processing_profile=ProcessingProfile.RAILWAY,
        enable_contextual_retrieval=False,  # Disable to see raw chunks
        enable_late_chunking=False,  # Disable to see individual chunks
        enable_quality_validation=True,
        enable_hybrid_search=False,
        enable_advanced_preprocessing=True
    )
    
    processor = EnhancedDocumentProcessor(config)
    pdf_path = '/workspace/windsurf-project/bms-doc-upload/pdf/BMS-QHSE-PRO-001 Risk Management.pdf'
    
    print('🔍 DETAILED QUALITY DIAGNOSTIC - ALL CHUNKS')
    print('=' * 70)
    
    result = processor.process_document(pdf_path)
    
    if result and result.get('processing_success'):
        chunks = result.get('chunks', [])
        quality_report = result.get('quality_report', {})
        
        print(f'📊 Processing Results:')
        print(f'   Total Chunks: {len(chunks)}')
        print(f'   Average Quality: {quality_report.get("average_quality", 0):.3f}')
        
        # Get quality validator to analyze each chunk
        quality_validator = processor.quality_validator
        
        # Read original document for comparison
        original_text = processor._read_document(Path(pdf_path))
        
        print(f'\n🔍 INDIVIDUAL CHUNK ANALYSIS:')
        print('=' * 70)
        
        all_issues = []
        
        for i, chunk in enumerate(chunks):
            content = chunk.get('content', '')
            
            print(f'\n🔸 CHUNK {i+1} DETAILED ANALYSIS:')
            print('-' * 50)
            print(f'📝 Content ({len(content)} chars):')
            print(f'   "{content[:200]}..."')
            
            # Get detailed quality metrics
            quality_result = quality_validator.validate_chunk_quality(
                chunk, original_text, context=None
            )
            
            metrics = quality_result['metrics']
            overall_score = quality_result['overall_score']
            passes = quality_result['passes_quality']
            failed_metrics = quality_result['failed_metrics']
            
            print(f'\n📊 Quality Metrics:')
            print(f'   Overall Score: {overall_score:.3f} {"✅" if passes else "❌"}')
            
            # Analyze each metric in detail
            print(f'\n📈 Detailed Metric Analysis:')
            
            for metric, score in metrics.items():
                threshold = quality_validator.thresholds.get(metric, 0.5)
                status = "✅" if score >= threshold else "❌"
                print(f'   {status} {metric}: {score:.3f} (threshold: {threshold})')
                
                # Identify specific issues
                if score < threshold:
                    issue = _diagnose_metric_issue(metric, score, content, original_text)
                    print(f'      🔍 Issue: {issue}')
                    all_issues.append((f'Chunk {i+1}', metric, score, issue))
            
            if failed_metrics:
                print(f'\n❌ Failed Metrics: {failed_metrics}')
            
            # Content-specific analysis
            print(f'\n🔍 Content Analysis:')
            content_issues = _analyze_content_issues(content)
            for issue in content_issues:
                print(f'   ⚠️  {issue}')
                all_issues.append((f'Chunk {i+1}', 'content', 0, issue))
        
        # Summary of all issues
        print(f'\n' + '=' * 70)
        print(f'📋 COMPREHENSIVE ISSUE SUMMARY:')
        print('=' * 70)
        
        # Group issues by type
        issue_types = {}
        for chunk, metric, score, issue in all_issues:
            if metric not in issue_types:
                issue_types[metric] = []
            issue_types[metric].append((chunk, score, issue))
        
        for metric, issues in issue_types.items():
            print(f'\n🔸 {metric.upper()} ISSUES ({len(issues)} occurrences):')
            for chunk, score, issue in issues[:3]:  # Show first 3
                if score > 0:
                    print(f'   • {chunk}: {score:.3f} - {issue}')
                else:
                    print(f'   • {chunk}: {issue}')
        
        # Recommendations
        print(f'\n' + '=' * 70)
        print(f'💡 RECOMMENDATIONS TO IMPROVE QUALITY:')
        print('=' * 70)
        
        # Analyze most common issues
        metric_counts = {}
        for chunk, metric, score, issue in all_issues:
            metric_counts[metric] = metric_counts.get(metric, 0) + 1
        
        sorted_issues = sorted(metric_counts.items(), key=lambda x: x[1], reverse=True)
        
        for metric, count in sorted_issues[:5]:  # Top 5 issues
            print(f'\n🔧 {metric.upper()} (affects {count} chunks):')
            recommendations = _get_recommendations(metric)
            for rec in recommendations:
                print(f'   • {rec}')
    
    else:
        print('❌ Processing failed')

def _diagnose_metric_issue(metric: str, score: float, content: str, original: str) -> str:
    """Diagnose specific issues with quality metrics"""
    
    if metric == 'faithfulness':
        if score < 0.7:
            return "Content significantly differs from original document"
        elif score < 0.85:
            return "Some content may be paraphrased or modified"
        else:
            return "Minor faithfulness issues"
    
    elif metric == 'context_recall':
        if score < 0.1:
            return "Chunk captures very little of the original context"
        elif score < 0.3:
            return "Limited context coverage - chunk may be too focused"
        else:
            return "Moderate context coverage issues"
    
    elif metric == 'semantic_similarity':
        if score < 0.1:
            return "Very low vocabulary overlap with original"
        elif score < 0.3:
            return "Limited shared vocabulary - may be too specialized"
        else:
            return "Moderate vocabulary differences"
    
    elif metric == 'context_precision':
        if score < 0.5:
            return "High noise-to-signal ratio in content"
        elif score < 0.7:
            return "Some irrelevant or low-value content included"
        else:
            return "Minor precision issues with content focus"
    
    elif metric == 'answer_relevancy':
        if score < 0.6:
            return "Content not well-aligned with expected relevance"
        elif score < 0.8:
            return "Moderate relevance issues"
        else:
            return "Minor relevance alignment issues"
    
    elif metric == 'information_density':
        if score < 0.3:
            return "Very low information density - too much filler"
        elif score < 0.5:
            return "Low information density - repetitive content"
        else:
            return "Moderate information density issues"
    
    elif metric == 'readability_score':
        if score < 0.4:
            return "Poor readability - fragmented or unclear text"
        elif score < 0.6:
            return "Moderate readability issues"
        else:
            return "Minor readability concerns"
    
    return "Unknown quality issue"

def _analyze_content_issues(content: str) -> list:
    """Analyze content for specific issues"""
    issues = []
    
    # Check for fragmentation
    sentences = content.split('.')
    if len(sentences) > 10 and any(len(s.strip()) < 10 for s in sentences):
        issues.append("Contains fragmented sentences")
    
    # Check for repetition
    words = content.lower().split()
    if len(set(words)) / len(words) < 0.6:
        issues.append("High word repetition (low vocabulary diversity)")
    
    # Check for technical artifacts
    if '##' in content or '@@' in content:
        issues.append("Contains processing artifacts or markers")
    
    # Check for incomplete sentences
    if not content.strip().endswith(('.', '!', '?', ':')):
        issues.append("Ends with incomplete sentence")
    
    # Check for excessive whitespace or formatting issues
    if '  ' in content or '\n\n' in content:
        issues.append("Contains formatting artifacts (excessive whitespace)")
    
    # Check for very short or very long sentences
    sentences = [s.strip() for s in content.split('.') if s.strip()]
    if sentences:
        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences)
        if avg_sentence_length < 5:
            issues.append("Very short sentences (may be fragmented)")
        elif avg_sentence_length > 30:
            issues.append("Very long sentences (may be run-on)")
    
    return issues

def _get_recommendations(metric: str) -> list:
    """Get recommendations for improving specific metrics"""
    
    recommendations = {
        'faithfulness': [
            "Improve chunk boundary detection to preserve complete thoughts",
            "Reduce text preprocessing that might alter meaning",
            "Ensure chunks maintain original document structure"
        ],
        'context_recall': [
            "Increase chunk size to capture more context",
            "Improve sentence boundary detection",
            "Use overlapping chunks to preserve context"
        ],
        'semantic_similarity': [
            "Preserve more original vocabulary during preprocessing",
            "Reduce aggressive text normalization",
            "Maintain technical terms and domain-specific language"
        ],
        'context_precision': [
            "Improve filtering of non-content elements",
            "Better detection of headers, footers, and artifacts",
            "Enhance content relevance scoring"
        ],
        'answer_relevancy': [
            "Improve document type detection",
            "Better alignment with expected content types",
            "Enhance contextual understanding"
        ],
        'information_density': [
            "Remove more repetitive content",
            "Improve deduplication algorithms",
            "Better filtering of low-information content"
        ],
        'readability_score': [
            "Improve sentence reconstruction after PDF extraction",
            "Better handling of formatting artifacts",
            "Enhance text flow and coherence"
        ]
    }
    
    return recommendations.get(metric, ["No specific recommendations available"])

if __name__ == "__main__":
    detailed_quality_diagnostic()
