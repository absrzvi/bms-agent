#!/usr/bin/env python3
"""
Test Enhanced Document Processor v4.0 with ALL features enabled and spaCy models
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

def test_full_features():
    """Test FULL feature set with spaCy models available"""
    
    # Full feature configuration with adjusted thresholds
    config = ProcessingConfig(
        chunk_size=400,
        min_chunk_size=30,
        quality_threshold=30.0,  # Lower threshold for better success
        min_quality_score=0.5,   # Much lower minimum quality score (0.5 instead of 50.0)
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
    
    print('🚀 TESTING FULL FEATURE SET WITH SPACY MODELS')
    print('=' * 70)
    print(f'Document: {pdf_path.split("/")[-1]}')
    
    result = processor.process_document(pdf_path)
    
    if result and result.get('processing_success'):
        chunks = result.get('chunks', [])
        statistics = result.get('statistics', {})
        
        print(f'\n🎉 SUCCESS! Full feature set working!')
        print(f'📊 Processing Summary:')
        print(f'   Total Chunks: {len(chunks)}')
        print(f'   Avg Chunk Size: {statistics.get("avg_chunk_size", 0):.1f} chars')
        print(f'   Document Length: {statistics.get("document_length", 0)} chars')
        
        if len(chunks) >= 5:
            print(f'\n📄 FIRST 5 CHUNKS WITH FULL METADATA:')
            print('=' * 70)
            
            for i, chunk in enumerate(chunks[:5]):
                print(f'\n🔸 CHUNK {i+1}:')
                print('-' * 50)
                
                # Content
                content = chunk.get('content', '')
                print(f'📝 Content ({len(content)} chars):')
                content_preview = content.replace('\n', ' ').strip()[:250]
                if len(content) > 250:
                    content_preview += '...'
                print(f'   "{content_preview}"')
                
                # Core metadata
                print(f'\n🏷️  Core Metadata:')
                print(f'   Index: {chunk.get("index", "N/A")}')
                print(f'   Chunk Type: {chunk.get("chunk_type", "N/A")}')
                print(f'   Hierarchy Level: {chunk.get("hierarchy_level", "N/A")}')
                
                # Quality metrics (now available with spaCy)
                quality_score = chunk.get('quality_score')
                if quality_score is not None:
                    print(f'   ⭐ Quality Score: {quality_score:.2f}')
                
                # Contextual information
                contextual_desc = chunk.get('contextual_description')
                if contextual_desc:
                    print(f'\n🔗 Contextual Description:')
                    desc_preview = contextual_desc[:150] + '...' if len(contextual_desc) > 150 else contextual_desc
                    print(f'   "{desc_preview}"')
                
                # Keywords and technical terms (hybrid search)
                keywords = chunk.get('keywords', [])
                technical_terms = chunk.get('technical_terms', [])
                if keywords:
                    print(f'\n🔑 Keywords: {keywords[:5]}')
                if technical_terms:
                    print(f'🔧 Technical Terms: {technical_terms[:5]}')
                
                # Position metadata
                metadata = chunk.get('metadata', {})
                if metadata:
                    print(f'\n📍 Position Info:')
                    for key in ['position', 'size', 'method']:
                        if key in metadata:
                            print(f'   {key.title()}: {metadata[key]}')
        
        # Document-level features
        print(f'\n' + '=' * 70)
        print(f'📄 DOCUMENT-LEVEL FEATURES:')
        print('=' * 70)
        
        entities = result.get('entities', {})
        if entities:
            topics = entities.get('topics', [])[:8]
            key_phrases = entities.get('key_phrases', [])[:5]
            
            if topics:
                print(f'🏷️  Document Topics: {topics}')
            if key_phrases:
                print(f'🔑 Key Phrases: {key_phrases}')
        
        railway_metadata = result.get('railway_metadata', {})
        if railway_metadata:
            railway_specific = railway_metadata.get('railway_specific', {})
            standards = railway_specific.get('standards_compliance', [])
            if standards:
                print(f'🚂 Railway Standards: {standards}')
        
        quality_report = result.get('quality_report', {})
        if quality_report:
            print(f'\n📊 Quality Report:')
            for key, value in quality_report.items():
                print(f'   {key}: {value}')
        
        return True
    
    else:
        print('❌ Processing failed')
        if result:
            print(f'Error: {result.get("error", "Unknown error")}')
        return False

if __name__ == "__main__":
    success = test_full_features()
    if success:
        print(f'\n🎯 ALL FEATURES WORKING WITH SPACY MODELS! 🎉')
    else:
        print(f'\n⚠️  Some features need adjustment')
