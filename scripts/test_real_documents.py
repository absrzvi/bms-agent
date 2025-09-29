#!/usr/bin/env python3
"""
Test Enhanced Document Processor v4.0 with Real BMS Documents
Tests processing of actual business documents from different formats
"""

import sys
import json
import time
from pathlib import Path
from typing import Dict, Any, List

# Add API to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "api"))

try:
    from processor_wrapper import BMSDocumentProcessor
    PROCESSOR_AVAILABLE = True
except ImportError as e:
    print(f"❌ Error importing processor wrapper: {e}")
    PROCESSOR_AVAILABLE = False

# Document paths
BMS_DOC_ROOT = Path("/workspace/windsurf-project/bms-doc-upload")

def get_test_documents() -> Dict[str, List[Path]]:
    """Get sample documents from each format folder"""
    test_docs = {
        "pdf": [],
        "docx": [],
        "xlsx": [],
        "pptx": []
    }
    
    # PDF documents
    pdf_dir = BMS_DOC_ROOT / "pdf"
    if pdf_dir.exists():
        pdf_files = [
            "BMS-QHSE-PRO-001 Risk Management.pdf",
            "BMS-BDEV-PRO-001 Bid Development.pdf", 
            "BMS-ISEC-POL-001 Information Security Policy Statement.pdf",
            "Asset Registration Process.pdf",
            "Employee Expenses Process.pdf"
        ]
        for filename in pdf_files:
            file_path = pdf_dir / filename
            if file_path.exists():
                test_docs["pdf"].append(file_path)
    
    # DOCX documents
    doc_dir = BMS_DOC_ROOT / "doc"
    if doc_dir.exists():
        docx_files = [
            "BMS-BCON-FOR-001-Business Continuity Response Template.docx",
            "BMS-BCON-FOR-002 QHSE - Fatality or serious incident response.docx",
            "BMS-BCON-FOR-003-Business Continuity Response Template - CyberIncidents.docx"
        ]
        for filename in docx_files:
            file_path = doc_dir / filename
            if file_path.exists():
                test_docs["docx"].append(file_path)
    
    # XLSX documents
    xls_dir = BMS_DOC_ROOT / "xls"
    if xls_dir.exists():
        xlsx_files = [
            "BMS-BDEV-FOR-005 Bid Action Log Check List.xlsx",
            "BMS-BDEV-FOR-019 System MTBF Calculation.xlsx",
            "BMS-BDEV-FOR-020 Maintenance Plan.xlsx"
        ]
        for filename in xlsx_files:
            file_path = xls_dir / filename
            if file_path.exists():
                test_docs["xlsx"].append(file_path)
    
    # PPTX documents
    ppt_dir = BMS_DOC_ROOT / "ppt"
    if ppt_dir.exists():
        pptx_files = [
            "BMS-BDEV-FOR-008 Bid Kick Off Template.pptx",
            "BMS-BDEV-FOR-014 Win-Loss Analysis Template.pptx",
            "BMS-PROJ-FOR-031 Financial Project Review Template.pptx"
        ]
        for filename in pptx_files:
            file_path = ppt_dir / filename
            if file_path.exists():
                test_docs["pptx"].append(file_path)
    
    return test_docs

def test_document_processing(processor: BMSDocumentProcessor, test_docs: Dict[str, List[Path]]):
    """Test processing of real BMS documents"""
    print("📄 Testing Enhanced Document Processor v4.0 with Real BMS Documents")
    print("=" * 70)
    
    results = {}
    total_processed = 0
    total_successful = 0
    total_chunks = 0
    
    # Profile mapping for different document types
    profile_mapping = {
        "QHSE": "technical",
        "BDEV": "general", 
        "ISEC": "technical",
        "BCON": "general",
        "PROJ": "financial",
        "ENGI": "technical",
        "HUMR": "legal",
        "Asset": "technical",
        "Employee": "general"
    }
    
    for format_type, documents in test_docs.items():
        if not documents:
            print(f"\n⚠️  No {format_type.upper()} documents found")
            continue
            
        print(f"\n🔍 Testing {format_type.upper()} Documents ({len(documents)} files)")
        print("-" * 50)
        
        format_results = []
        
        for doc_path in documents:
            print(f"\n📄 Processing: {doc_path.name}")
            
            # Determine processing profile based on document code
            profile = "general"  # default
            for code, prof in profile_mapping.items():
                if code in doc_path.name:
                    profile = prof
                    break
            
            print(f"   Profile: {profile}")
            
            try:
                start_time = time.time()
                result = processor.process_document(str(doc_path), profile)
                processing_time = time.time() - start_time
                
                total_processed += 1
                
                if result.status == "success":
                    total_successful += 1
                    total_chunks += result.chunks_created
                    
                    print(f"   ✅ Success: {result.chunks_created} chunks, {result.quality_score:.1f} quality")
                    print(f"   ⏱️  Time: {processing_time:.2f}s")
                    print(f"   🚀 Features: {len(result.features_extracted)} active")
                    
                    # Show some features
                    key_features = [f for f in result.features_extracted if f in [
                        'hierarchical_chunking', 'contextual_retrieval', 'quality_validation', 
                        'railway_processing', 'advanced_preprocessing'
                    ]]
                    if key_features:
                        print(f"   🔧 Key Features: {', '.join(key_features)}")
                    
                else:
                    print(f"   ❌ Failed: {result.error}")
                
                format_results.append({
                    "file": doc_path.name,
                    "status": result.status,
                    "chunks": result.chunks_created,
                    "quality": result.quality_score,
                    "time": processing_time,
                    "features": result.features_extracted,
                    "error": result.error
                })
                
            except Exception as e:
                print(f"   ❌ Exception: {e}")
                format_results.append({
                    "file": doc_path.name,
                    "status": "error",
                    "chunks": 0,
                    "quality": 0.0,
                    "time": 0.0,
                    "features": [],
                    "error": str(e)
                })
        
        results[format_type] = format_results
    
    # Generate comprehensive report
    print("\n" + "=" * 70)
    print("📊 ENHANCED DOCUMENT PROCESSOR v4.0 - REAL DOCUMENT TEST REPORT")
    print("=" * 70)
    
    print(f"\n📈 Overall Statistics:")
    print(f"   Total Documents Processed: {total_processed}")
    print(f"   Successful Processes: {total_successful}")
    print(f"   Success Rate: {(total_successful/total_processed*100):.1f}%" if total_processed > 0 else "   Success Rate: 0%")
    print(f"   Total Chunks Generated: {total_chunks}")
    print(f"   Average Chunks per Document: {(total_chunks/total_successful):.1f}" if total_successful > 0 else "   Average Chunks per Document: 0")
    
    # Format-specific statistics
    print(f"\n📋 Format-Specific Results:")
    for format_type, format_results in results.items():
        if not format_results:
            continue
            
        successful = [r for r in format_results if r["status"] == "success"]
        total_format = len(format_results)
        success_rate = len(successful) / total_format * 100 if total_format > 0 else 0
        
        print(f"\n   {format_type.upper()} Documents:")
        print(f"     Processed: {total_format}")
        print(f"     Successful: {len(successful)}")
        print(f"     Success Rate: {success_rate:.1f}%")
        
        if successful:
            avg_chunks = sum(r["chunks"] for r in successful) / len(successful)
            avg_quality = sum(r["quality"] for r in successful) / len(successful)
            avg_time = sum(r["time"] for r in successful) / len(successful)
            
            print(f"     Avg Chunks: {avg_chunks:.1f}")
            print(f"     Avg Quality: {avg_quality:.1f}")
            print(f"     Avg Time: {avg_time:.2f}s")
    
    # Feature usage analysis
    print(f"\n🔧 Enhanced Features Usage Analysis:")
    all_features = {}
    for format_results in results.values():
        for result in format_results:
            if result["status"] == "success":
                for feature in result["features"]:
                    all_features[feature] = all_features.get(feature, 0) + 1
    
    if all_features:
        print("   Feature Usage Count:")
        for feature, count in sorted(all_features.items(), key=lambda x: x[1], reverse=True):
            print(f"     {feature}: {count} documents")
    
    # Document type analysis
    print(f"\n📑 Document Type Analysis:")
    doc_types = {}
    for format_results in results.values():
        for result in format_results:
            # Extract document type from filename
            filename = result["file"]
            if "BMS-" in filename:
                doc_type = filename.split("-")[1] if len(filename.split("-")) > 1 else "UNKNOWN"
                doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
    
    if doc_types:
        print("   BMS Document Types Processed:")
        for doc_type, count in sorted(doc_types.items(), key=lambda x: x[1], reverse=True):
            print(f"     {doc_type}: {count} documents")
    
    # Save detailed report
    try:
        report_data = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "summary": {
                "total_processed": total_processed,
                "total_successful": total_successful,
                "success_rate": (total_successful/total_processed*100) if total_processed > 0 else 0,
                "total_chunks": total_chunks
            },
            "format_results": results,
            "feature_usage": all_features,
            "document_types": doc_types
        }
        
        report_path = project_root / "real_documents_test_report.json"
        with open(report_path, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        print(f"\n💾 Detailed report saved to: {report_path}")
        
    except Exception as e:
        print(f"\n⚠️  Could not save detailed report: {e}")
    
    print("\n" + "=" * 70)
    
    return results

def test_api_integration(test_docs: Dict[str, List[Path]]):
    """Test API integration with real documents"""
    print("\n🌐 Testing API Integration with Real Documents")
    print("-" * 50)
    
    import requests
    
    api_url = "http://localhost:8000"
    
    # Test health check
    try:
        response = requests.get(f"{api_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ API Health Check: Passed")
        else:
            print(f"❌ API Health Check: Failed ({response.status_code})")
            return
    except Exception as e:
        print(f"❌ API Health Check: Failed - {e}")
        return
    
    # Test document upload with one file from each format
    upload_results = []
    
    for format_type, documents in test_docs.items():
        if not documents:
            continue
            
        # Test with first document of each type
        test_doc = documents[0]
        print(f"\n📤 Testing upload: {test_doc.name}")
        
        try:
            with open(test_doc, 'rb') as f:
                files = {'file': (test_doc.name, f, f'application/{format_type}')}
                data = {'profile': 'technical'}
                
                response = requests.post(f"{api_url}/api/v1/documents/upload", files=files, data=data, timeout=60)
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"   ✅ Upload Success: {result['processing_result']['chunks_created']} chunks")
                    upload_results.append({
                        "file": test_doc.name,
                        "status": "success",
                        "chunks": result['processing_result']['chunks_created']
                    })
                else:
                    print(f"   ❌ Upload Failed: {response.status_code}")
                    upload_results.append({
                        "file": test_doc.name,
                        "status": "failed",
                        "error": response.text
                    })
                    
        except Exception as e:
            print(f"   ❌ Upload Exception: {e}")
            upload_results.append({
                "file": test_doc.name,
                "status": "error",
                "error": str(e)
            })
    
    # Test search functionality
    if any(r["status"] == "success" for r in upload_results):
        print(f"\n🔍 Testing Search Functionality")
        
        test_queries = [
            "risk management process",
            "bid development procedure", 
            "business continuity response",
            "information security policy"
        ]
        
        for query in test_queries:
            try:
                search_data = {"query": query, "limit": 5}
                response = requests.post(f"{api_url}/api/v1/search/semantic", json=search_data, timeout=30)
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"   ✅ Search '{query}': {len(result['results'])} results")
                else:
                    print(f"   ❌ Search '{query}': Failed ({response.status_code})")
                    
            except Exception as e:
                print(f"   ❌ Search '{query}': Exception - {e}")
    
    print(f"\n📊 API Integration Summary:")
    successful_uploads = [r for r in upload_results if r["status"] == "success"]
    print(f"   Successful Uploads: {len(successful_uploads)}/{len(upload_results)}")
    
    return upload_results

def main():
    """Main test execution"""
    print("🚀 Enhanced Document Processor v4.0 - Real BMS Document Test")
    print("=" * 70)
    
    if not PROCESSOR_AVAILABLE:
        print("❌ Processor wrapper not available - cannot run tests")
        return 1
    
    # Get test documents
    print("📁 Scanning for BMS documents...")
    test_docs = get_test_documents()
    
    total_docs = sum(len(docs) for docs in test_docs.values())
    if total_docs == 0:
        print("❌ No BMS documents found in expected directories")
        return 1
    
    print(f"✅ Found {total_docs} BMS documents across {len([k for k, v in test_docs.items() if v])} formats")
    
    for format_type, docs in test_docs.items():
        if docs:
            print(f"   {format_type.upper()}: {len(docs)} files")
    
    try:
        # Initialize processor
        print(f"\n🔧 Initializing Enhanced Document Processor v4.0...")
        processor = BMSDocumentProcessor()
        
        # Test document processing
        processing_results = test_document_processing(processor, test_docs)
        
        # Test API integration
        api_results = test_api_integration(test_docs)
        
        # Final assessment
        total_successful = sum(
            len([r for r in format_results if r["status"] == "success"])
            for format_results in processing_results.values()
        )
        
        overall_success = total_successful > 0
        
        print(f"\n🎯 Final Assessment:")
        print(f"   Enhanced Document Processor v4.0: {'✅ OPERATIONAL' if overall_success else '❌ ISSUES'}")
        print(f"   Real Document Processing: {'✅ WORKING' if total_successful > 0 else '❌ FAILED'}")
        print(f"   API Integration: {'✅ WORKING' if any(r['status'] == 'success' for r in api_results) else '❌ FAILED'}")
        
        return 0 if overall_success else 1
        
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
