#!/usr/bin/env python3
"""
Comprehensive Test of ALL Enhanced Document Processor v4.0 Features
Tests every feature on one PDF document with detailed output
"""

import sys
import json
import time
from pathlib import Path
from typing import Dict, Any, List

# Add paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "bms-agent" / "scr"))
sys.path.insert(0, str(project_root / "api"))

try:
    from enhanced_document_processor import (
        EnhancedDocumentProcessor, ProcessingConfig, ProcessingProfile,
        ChunkingStrategy
    )
    from processor_wrapper import BMSDocumentProcessor
    PROCESSOR_AVAILABLE = True
except ImportError as e:
    print(f"❌ Error importing: {e}")
    PROCESSOR_AVAILABLE = False

def test_feature_configuration(feature_name: str, config: ProcessingConfig, pdf_path: str):
    """Test a specific feature configuration"""
    print(f"\n🧪 Testing: {feature_name}")
    print("-" * 50)
    
    try:
        start_time = time.time()
        processor = EnhancedDocumentProcessor(config)
        result = processor.process_document(pdf_path)
        processing_time = time.time() - start_time
        
        if result and result.get("processing_success", False):
            chunks = result.get("chunks", [])
            statistics = result.get("statistics", {})
            quality_report = result.get("quality_report", {})
            entities = result.get("entities", {})
            
            print(f"✅ SUCCESS: {len(chunks)} chunks created")
            print(f"   Processing Time: {processing_time:.2f}s")
            print(f"   Avg Chunk Size: {statistics.get('avg_chunk_size', 0):.1f} chars")
            print(f"   Document Length: {statistics.get('document_length', 0)} chars")
            
            # Show feature-specific results
            if entities:
                topics = entities.get('topics', [])[:5]
                key_phrases = entities.get('key_phrases', [])[:3]
                if topics:
                    print(f"   🏷️  Topics: {', '.join(topics)}")
                if key_phrases:
                    print(f"   🔑 Key Phrases: {', '.join(key_phrases)}")
            
            # Show first 2 chunks with metadata
            print(f"   📄 Sample Chunks:")
            for i, chunk in enumerate(chunks[:2]):
                content = chunk.get('content', '')[:100].replace('\n', ' ')
                print(f"      Chunk {i+1}: {len(chunk.get('content', ''))} chars - \"{content}...\"")
                
                # Show chunk metadata
                metadata_items = []
                for key, value in chunk.items():
                    if key not in ['content'] and value:
                        if isinstance(value, str) and len(value) > 30:
                            value = value[:30] + "..."
                        metadata_items.append(f"{key}={value}")
                
                if metadata_items:
                    print(f"         Metadata: {', '.join(metadata_items[:3])}")
            
            return result
            
        else:
            error = result.get("error", "Unknown error") if result else "No result"
            print(f"❌ FAILED: {error}")
            return None
            
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
        return None

def test_all_enhanced_features():
    """Test all Enhanced Document Processor v4.0 features"""
    
    pdf_path = "/workspace/windsurf-project/bms-doc-upload/pdf/BMS-QHSE-PRO-001 Risk Management.pdf"
    
    if not Path(pdf_path).exists():
        print(f"❌ PDF not found: {pdf_path}")
        return
    
    print("🚀 COMPREHENSIVE ENHANCED DOCUMENT PROCESSOR v4.0 FEATURE TEST")
    print("=" * 80)
    print(f"📄 Test Document: {Path(pdf_path).name}")
    print(f"📁 Document Path: {pdf_path}")
    
    # Base configuration for all tests
    base_config = {
        "chunk_size": 400,
        "min_chunk_size": 30,
        "quality_threshold": 30.0,
        "processing_profile": ProcessingProfile.RAILWAY,
        "enable_advanced_preprocessing": True,
        "enable_ocr": True,
        "extract_tables": True,
        "extract_images": True,
        "enable_versioning": True
    }
    
    # Test configurations for different features
    feature_tests = [
        {
            "name": "1. Basic Sliding Window Chunking",
            "config": ProcessingConfig(
                **base_config,
                chunking_strategy=ChunkingStrategy.SLIDING_WINDOW,
                enable_contextual_retrieval=False,
                enable_late_chunking=False,
                enable_quality_validation=False,
                enable_hybrid_search=False
            )
        },
        {
            "name": "2. Hierarchical Chunking Engine",
            "config": ProcessingConfig(
                **base_config,
                chunking_strategy=ChunkingStrategy.HIERARCHICAL,
                parent_chunk_size=1000,
                child_chunk_size=300,
                enable_contextual_retrieval=False,
                enable_late_chunking=False,
                enable_quality_validation=False,
                enable_hybrid_search=False
            )
        },
        {
            "name": "3. Contextual Retrieval Engine",
            "config": ProcessingConfig(
                **base_config,
                chunking_strategy=ChunkingStrategy.SLIDING_WINDOW,
                enable_contextual_retrieval=True,
                enable_late_chunking=False,
                enable_quality_validation=False,
                enable_hybrid_search=False
            )
        },
        {
            "name": "4. Late Chunking Engine",
            "config": ProcessingConfig(
                **base_config,
                chunking_strategy=ChunkingStrategy.LATE_CHUNKING,
                enable_contextual_retrieval=False,
                enable_late_chunking=True,
                enable_quality_validation=False,
                enable_hybrid_search=False
            )
        },
        {
            "name": "5. Quality Validation Engine",
            "config": ProcessingConfig(
                **base_config,
                chunking_strategy=ChunkingStrategy.SLIDING_WINDOW,
                enable_contextual_retrieval=False,
                enable_late_chunking=False,
                enable_quality_validation=True,
                enable_hybrid_search=False
            )
        },
        {
            "name": "6. Hybrid Search Preparation",
            "config": ProcessingConfig(
                **base_config,
                chunking_strategy=ChunkingStrategy.SLIDING_WINDOW,
                enable_contextual_retrieval=False,
                enable_late_chunking=False,
                enable_quality_validation=False,
                enable_hybrid_search=True
            )
        },
        {
            "name": "7. Semantic Chunking Strategy",
            "config": ProcessingConfig(
                **base_config,
                chunking_strategy=ChunkingStrategy.SEMANTIC,
                enable_contextual_retrieval=False,
                enable_late_chunking=False,
                enable_quality_validation=False,
                enable_hybrid_search=False
            )
        },
        {
            "name": "8. Sentence Window Strategy",
            "config": ProcessingConfig(
                **base_config,
                chunking_strategy=ChunkingStrategy.SENTENCE_WINDOW,
                enable_contextual_retrieval=False,
                enable_late_chunking=False,
                enable_quality_validation=False,
                enable_hybrid_search=False
            )
        },
        {
            "name": "9. Structural Chunking Strategy",
            "config": ProcessingConfig(
                **base_config,
                chunking_strategy=ChunkingStrategy.STRUCTURAL,
                enable_contextual_retrieval=False,
                enable_late_chunking=False,
                enable_quality_validation=False,
                enable_hybrid_search=False
            )
        },
        {
            "name": "10. ALL FEATURES COMBINED (v4.0 Full Power)",
            "config": ProcessingConfig(
                **base_config,
                chunking_strategy=ChunkingStrategy.HIERARCHICAL,
                parent_chunk_size=1000,
                child_chunk_size=300,
                enable_contextual_retrieval=True,
                enable_late_chunking=True,
                enable_quality_validation=True,
                enable_hybrid_search=True
            )
        }
    ]
    
    # Run all feature tests
    results = {}
    successful_tests = 0
    
    for test_config in feature_tests:
        result = test_feature_configuration(
            test_config["name"], 
            test_config["config"], 
            pdf_path
        )
        
        results[test_config["name"]] = result
        if result:
            successful_tests += 1
    
    # Generate comprehensive report
    print("\n" + "=" * 80)
    print("📊 ENHANCED DOCUMENT PROCESSOR v4.0 COMPREHENSIVE TEST REPORT")
    print("=" * 80)
    
    print(f"\n📈 Overall Results:")
    print(f"   Total Tests: {len(feature_tests)}")
    print(f"   Successful: {successful_tests}")
    print(f"   Success Rate: {(successful_tests/len(feature_tests)*100):.1f}%")
    
    # Feature-by-feature analysis
    print(f"\n🔍 Feature Analysis:")
    
    for test_name, result in results.items():
        if result:
            chunks = result.get("chunks", [])
            statistics = result.get("statistics", {})
            
            print(f"\n✅ {test_name}")
            print(f"   Chunks: {len(chunks)}")
            print(f"   Avg Size: {statistics.get('avg_chunk_size', 0):.1f} chars")
            print(f"   Total Length: {statistics.get('document_length', 0)} chars")
            
            # Show unique features of this test
            if "Hierarchical" in test_name and chunks:
                hierarchy_levels = set(chunk.get('hierarchy_level', 'unknown') for chunk in chunks)
                print(f"   Hierarchy Levels: {', '.join(hierarchy_levels)}")
            
            if "Contextual" in test_name and chunks:
                contextual_chunks = sum(1 for chunk in chunks if chunk.get('contextual_description'))
                print(f"   Contextual Chunks: {contextual_chunks}/{len(chunks)}")
            
            if "Quality" in test_name and chunks:
                quality_scores = [chunk.get('quality_score', 0) for chunk in chunks if chunk.get('quality_score')]
                if quality_scores:
                    avg_quality = sum(quality_scores) / len(quality_scores)
                    print(f"   Avg Quality Score: {avg_quality:.2f}")
            
            if "Hybrid" in test_name and chunks:
                hybrid_chunks = sum(1 for chunk in chunks if chunk.get('keywords') or chunk.get('technical_terms'))
                print(f"   Hybrid-Ready Chunks: {hybrid_chunks}/{len(chunks)}")
                
        else:
            print(f"\n❌ {test_name}")
            print(f"   Status: Failed")
    
    # Best performing configuration
    chunk_counts = {name: len(result.get("chunks", [])) for name, result in results.items() if result}
    if chunk_counts:
        best_config = max(chunk_counts.items(), key=lambda x: x[1])
        print(f"\n🏆 Best Performing Configuration:")
        print(f"   {best_config[0]}: {best_config[1]} chunks")
    
    # Save detailed results
    try:
        report_data = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "test_document": pdf_path,
            "total_tests": len(feature_tests),
            "successful_tests": successful_tests,
            "success_rate": (successful_tests/len(feature_tests)*100),
            "results": {}
        }
        
        for test_name, result in results.items():
            if result:
                chunks = result.get("chunks", [])
                statistics = result.get("statistics", {})
                report_data["results"][test_name] = {
                    "success": True,
                    "chunks_created": len(chunks),
                    "avg_chunk_size": statistics.get("avg_chunk_size", 0),
                    "document_length": statistics.get("document_length", 0),
                    "processing_success": result.get("processing_success", False)
                }
            else:
                report_data["results"][test_name] = {
                    "success": False,
                    "chunks_created": 0,
                    "error": "Processing failed"
                }
        
        report_path = project_root / "enhanced_processor_feature_test_report.json"
        with open(report_path, 'w') as f:
            json.dump(report_data, f, indent=2)
        print(f"\n💾 Detailed report saved to: {report_path}")
        
    except Exception as e:
        print(f"\n⚠️  Could not save report: {e}")
    
    print("\n" + "=" * 80)
    print("🎯 ENHANCED DOCUMENT PROCESSOR v4.0 FEATURE TEST COMPLETE")
    print("=" * 80)
    
    return results

def test_hybrid_search_integration():
    """Test hybrid search integration with actual search queries"""
    print("\n🔍 TESTING HYBRID SEARCH INTEGRATION")
    print("=" * 60)
    
    try:
        # Use the BMS processor wrapper for full integration
        processor = BMSDocumentProcessor()
        
        # Override config for hybrid search testing
        from enhanced_document_processor import ProcessingConfig, ProcessingProfile, ChunkingStrategy
        
        hybrid_config = ProcessingConfig(
            chunk_size=400,
            min_chunk_size=30,
            quality_threshold=30.0,
            chunking_strategy=ChunkingStrategy.SLIDING_WINDOW,
            processing_profile=ProcessingProfile.RAILWAY,
            enable_contextual_retrieval=False,
            enable_late_chunking=False,
            enable_quality_validation=False,
            enable_hybrid_search=True,
            enable_advanced_preprocessing=True
        )
        
        processor.enhanced_processor.config = hybrid_config
        
        pdf_path = "/workspace/windsurf-project/bms-doc-upload/pdf/BMS-QHSE-PRO-001 Risk Management.pdf"
        
        print(f"📄 Processing document for hybrid search...")
        result = processor.process_document(pdf_path, 'railway')
        
        if result.status == "success" and result.chunks_created > 0:
            print(f"✅ Document processed: {result.chunks_created} chunks created")
            
            # Test search queries
            test_queries = [
                "risk management process",
                "executive risk register", 
                "InfoSec incident response",
                "departmental risk assessment",
                "QHSE compliance procedures"
            ]
            
            print(f"\n🔍 Testing search queries:")
            
            for query in test_queries:
                print(f"\n📝 Query: '{query}'")
                
                # Test semantic search
                try:
                    if processor.qdrant_client:
                        # Generate query embedding
                        query_embedding = processor._generate_embeddings(query)
                        
                        if query_embedding:
                            # Perform search
                            search_results = processor.qdrant_client.search(
                                collection_name=processor.collection_name,
                                query_vector=("chunk_embedding", query_embedding),
                                limit=3,
                                with_payload=True
                            )
                            
                            print(f"   🎯 Found {len(search_results)} results")
                            
                            for i, hit in enumerate(search_results):
                                score = hit.score
                                content = hit.payload.get("content", "")[:100]
                                print(f"      {i+1}. Score: {score:.3f} - \"{content}...\"")
                        else:
                            print(f"   ❌ Failed to generate query embedding")
                    else:
                        print(f"   ⚠️  Qdrant not available for search testing")
                        
                except Exception as e:
                    print(f"   ❌ Search failed: {e}")
        else:
            print(f"❌ Document processing failed: {result.error if hasattr(result, 'error') else 'Unknown error'}")
            
    except Exception as e:
        print(f"❌ Hybrid search test failed: {e}")

def main():
    """Main test execution"""
    if not PROCESSOR_AVAILABLE:
        print("❌ Enhanced Document Processor not available")
        return 1
    
    # Test all features
    feature_results = test_all_enhanced_features()
    
    # Test hybrid search integration
    test_hybrid_search_integration()
    
    # Final summary
    successful_features = sum(1 for result in feature_results.values() if result)
    total_features = len(feature_results)
    
    print(f"\n🎯 FINAL SUMMARY:")
    print(f"   Enhanced Document Processor v4.0 Features Tested: {total_features}")
    print(f"   Successfully Working Features: {successful_features}")
    print(f"   Overall Feature Coverage: {(successful_features/total_features*100):.1f}%")
    
    if successful_features >= 7:  # Most features working
        print(f"   🎉 EXCELLENT: Enhanced Document Processor v4.0 is highly functional!")
        return 0
    elif successful_features >= 4:  # Some features working
        print(f"   ✅ GOOD: Core functionality working, some advanced features need attention")
        return 0
    else:
        print(f"   ⚠️  NEEDS WORK: Multiple features require debugging")
        return 1

if __name__ == "__main__":
    exit(main())
