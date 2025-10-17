#!/usr/bin/env python3
"""
Debug Enhanced Document Processor Chunking
Focus on one PDF file to understand and fix chunking issues
"""

import sys
import json
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

def debug_step_by_step(pdf_path: str):
    """Debug the processing step by step"""
    print("🔍 DEBUGGING ENHANCED DOCUMENT PROCESSOR CHUNKING")
    print("=" * 60)
    print(f"📄 Target PDF: {pdf_path}")
    
    if not Path(pdf_path).exists():
        print(f"❌ File not found: {pdf_path}")
        return
    
    # Step 1: Test basic PDF reading
    print("\n📖 Step 1: Testing PDF Text Extraction")
    print("-" * 40)
    
    try:
        # Test with pdfplumber
        import pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            for page_num, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
                print(f"   Page {page_num + 1}: {len(page_text) if page_text else 0} characters")
        
        print(f"✅ Total extracted text: {len(text)} characters")
        print(f"📝 First 300 characters:")
        print(f"   {repr(text[:300])}")
        
        if len(text.strip()) < 50:
            print("⚠️  WARNING: Very little text extracted - this might cause chunking issues")
            
    except Exception as e:
        print(f"❌ PDF extraction failed: {e}")
        return
    
    # Step 2: Test different chunking configurations
    print(f"\n🔧 Step 2: Testing Chunking Configurations")
    print("-" * 40)
    
    configs_to_test = [
        {
            "name": "Very Permissive Hierarchical",
            "chunk_size": 300,
            "min_chunk_size": 20,
            "quality_threshold": 20.0,
            "chunking_strategy": ChunkingStrategy.HIERARCHICAL
        },
        {
            "name": "Sentence Window",
            "chunk_size": 500,
            "min_chunk_size": 50,
            "quality_threshold": 25.0,
            "chunking_strategy": ChunkingStrategy.SENTENCE_WINDOW
        },
        {
            "name": "Sliding Window",
            "chunk_size": 400,
            "min_chunk_size": 30,
            "quality_threshold": 30.0,
            "chunking_strategy": ChunkingStrategy.SLIDING_WINDOW
        },
        {
            "name": "Semantic",
            "chunk_size": 600,
            "min_chunk_size": 40,
            "quality_threshold": 35.0,
            "chunking_strategy": ChunkingStrategy.SEMANTIC
        }
    ]
    
    successful_config = None
    
    for config_info in configs_to_test:
        print(f"\n🧪 Testing: {config_info['name']}")
        
        try:
            config = ProcessingConfig(
                chunk_size=config_info["chunk_size"],
                min_chunk_size=config_info["min_chunk_size"],
                quality_threshold=config_info["quality_threshold"],
                chunking_strategy=config_info["chunking_strategy"],
                processing_profile=ProcessingProfile.TECHNICAL,
                
                # Disable complex features for debugging
                enable_contextual_retrieval=False,
                enable_late_chunking=False,
                enable_quality_validation=False,
                enable_hybrid_search=False,
                
                # Keep basic features
                enable_advanced_preprocessing=True,
                enable_ocr=True,
                extract_tables=True,
                extract_images=True,
                enable_versioning=False
            )
            
            processor = EnhancedDocumentProcessor(config)
            result = processor.process_document(pdf_path)
            
            if result and result.get("status") == "success":
                chunks = result.get("chunks", [])
                print(f"   ✅ SUCCESS: {len(chunks)} chunks created")
                print(f"   📊 Quality: {result.get('quality_metrics', {}).get('overall_score', 'N/A')}")
                
                if chunks:
                    successful_config = (config_info, result)
                    break
            else:
                error = result.get("error", "Unknown error") if result else "No result"
                print(f"   ❌ FAILED: {error}")
                
        except Exception as e:
            print(f"   ❌ EXCEPTION: {e}")
    
    # Step 3: Show successful chunking details
    if successful_config:
        config_info, result = successful_config
        chunks = result.get("chunks", [])
        
        print(f"\n🎉 SUCCESS WITH: {config_info['name']}")
        print("=" * 60)
        print(f"📊 Results Summary:")
        print(f"   Total Chunks: {len(chunks)}")
        print(f"   Config Used: {config_info}")
        
        print(f"\n📄 First 5 Chunks:")
        print("-" * 40)
        
        for i, chunk in enumerate(chunks[:5]):
            print(f"\n🔸 Chunk {i + 1}:")
            print(f"   ID: {chunk.get('chunk_id', 'N/A')}")
            print(f"   Type: {chunk.get('chunk_type', 'N/A')}")
            print(f"   Size: {len(chunk.get('content', ''))} characters")
            print(f"   Quality: {chunk.get('quality_score', 'N/A')}")
            print(f"   Hierarchy: {chunk.get('hierarchy_level', 'N/A')}")
            
            content = chunk.get('content', '')
            if content:
                # Show first 200 characters of content
                preview = content.strip()[:200]
                if len(content) > 200:
                    preview += "..."
                print(f"   Content Preview: {repr(preview)}")
            
            # Show metadata
            metadata = {k: v for k, v in chunk.items() if k not in ['content']}
            print(f"   Metadata: {json.dumps(metadata, indent=6, default=str)}")
        
        return result
    else:
        print(f"\n❌ ALL CHUNKING ATTEMPTS FAILED")
        print("🔧 Debugging suggestions:")
        print("   1. Check if PDF text extraction is working properly")
        print("   2. Try even lower chunk size and quality thresholds")
        print("   3. Check for encoding issues in the text")
        print("   4. Verify sentence tokenization is working")
        
        return None

def test_with_simple_text():
    """Test chunking with simple text to isolate the issue"""
    print(f"\n🧪 TESTING WITH SIMPLE TEXT")
    print("=" * 60)
    
    simple_text = """
    BMS Risk Management Process Documentation
    
    This document outlines the comprehensive risk management process for BMS operations.
    
    Section 1: Risk Identification
    Risk identification is the first critical step in our risk management framework.
    We systematically identify potential risks that could impact our operations.
    This includes operational risks, technical risks, and compliance risks.
    
    Section 2: Risk Assessment
    Once risks are identified, we conduct thorough risk assessments.
    We evaluate the probability and potential impact of each risk.
    This helps us prioritize our risk mitigation efforts effectively.
    
    Section 3: Risk Mitigation
    For each identified risk, we develop appropriate mitigation strategies.
    These strategies are designed to reduce both the likelihood and impact of risks.
    We implement preventive measures and contingency plans as needed.
    
    Section 4: Risk Monitoring
    Continuous monitoring is essential for effective risk management.
    We regularly review and update our risk assessments.
    This ensures our risk management approach remains current and effective.
    """
    
    # Create temporary file
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(simple_text)
        temp_file = f.name
    
    try:
        config = ProcessingConfig(
            chunk_size=200,
            min_chunk_size=20,
            quality_threshold=20.0,
            chunking_strategy=ChunkingStrategy.SENTENCE_WINDOW,
            processing_profile=ProcessingProfile.TECHNICAL,
            
            # Minimal features for testing
            enable_contextual_retrieval=False,
            enable_late_chunking=False,
            enable_quality_validation=False,
            enable_hybrid_search=False,
            enable_advanced_preprocessing=True
        )
        
        processor = EnhancedDocumentProcessor(config)
        result = processor.process_document(temp_file)
        
        if result and result.get("status") == "success":
            chunks = result.get("chunks", [])
            print(f"✅ Simple text chunking SUCCESS: {len(chunks)} chunks")
            
            for i, chunk in enumerate(chunks[:3]):
                print(f"\n📄 Chunk {i + 1}: {len(chunk.get('content', ''))} chars")
                print(f"   Content: {repr(chunk.get('content', '')[:100])}")
        else:
            error = result.get("error", "Unknown") if result else "No result"
            print(f"❌ Simple text chunking FAILED: {error}")
            
    except Exception as e:
        print(f"❌ Simple text test EXCEPTION: {e}")
    finally:
        Path(temp_file).unlink()

def main():
    """Main debugging function"""
    if not PROCESSOR_AVAILABLE:
        print("❌ Enhanced Document Processor not available")
        return
    
    # Test with the BMS Risk Management PDF
    pdf_path = "/workspace/windsurf-project/bms-doc-upload/pdf/BMS-QHSE-PRO-001 Risk Management.pdf"
    
    if not Path(pdf_path).exists():
        print(f"❌ PDF not found: {pdf_path}")
        print("📁 Available PDFs:")
        pdf_dir = Path("/workspace/windsurf-project/bms-doc-upload/pdf")
        if pdf_dir.exists():
            for pdf_file in list(pdf_dir.glob("*.pdf"))[:5]:
                print(f"   {pdf_file}")
        return
    
    # First test with simple text
    test_with_simple_text()
    
    # Then test with the actual PDF
    result = debug_step_by_step(pdf_path)
    
    if result:
        print(f"\n🎯 CHUNKING DEBUG COMPLETE - SUCCESS!")
        print(f"   Use the successful configuration for your API")
    else:
        print(f"\n🔧 CHUNKING DEBUG COMPLETE - NEEDS MORE WORK")
        print(f"   Check the debugging suggestions above")

if __name__ == "__main__":
    main()
