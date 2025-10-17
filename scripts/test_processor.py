#!/usr/bin/env python3
"""
Test script for Enhanced Document Processor v4.0 integration
Validates all engines work and verifies complete feature coverage in Qdrant collection
"""

import sys
import json
import tempfile
from pathlib import Path
from typing import Dict, Any

# Add API to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "api"))

try:
    from processor_wrapper import BMSDocumentProcessor
    PROCESSOR_AVAILABLE = True
except ImportError as e:
    print(f"❌ Error importing processor wrapper: {e}")
    PROCESSOR_AVAILABLE = False

def create_test_documents() -> Dict[str, Path]:
    """Create test documents for validation"""
    docs = {}
    
    # Railway technical document with all features to test
    railway_content = """
    Railway Network Configuration Manual - R4600-2Ax CCU
    
    Section 1: VLAN Configuration
    The R4600-2Ax Central Control Unit (CCU) supports VLAN 101 with 1Gbps Ethernet throughput.
    Configure the network settings according to EN50155 railway standards.
    
    Key Components:
    - CCU Model: R4600-2Ax
    - Network Interface: Dual Gigabit Ethernet
    - VLAN Support: 802.1Q tagging
    - Compliance: EN50155, EN50121, TSI specifications
    
    Section 2: Network Topology
    The railway network consists of:
    1. Primary VLAN 101: Passenger information systems
    2. Secondary VLAN 102: Maintenance and diagnostics
    3. Management VLAN 103: Administrative access
    
    Configuration Steps:
    1. Connect to CCU management interface at 192.168.1.100
    2. Navigate to Network Configuration menu
    3. Set VLAN ID to 101 for passenger services
    4. Configure IP range: 192.168.101.0/24
    5. Enable QoS with priority 6 for real-time data
    6. Test connectivity using ping and iperf tools
    
    Section 3: Technical Specifications
    - Operating Voltage: 12V DC (±20%)
    - Power Consumption: Maximum 2.5A
    - Operating Temperature: -40°C to +70°C
    - Storage Temperature: -50°C to +85°C
    - Humidity: 5% to 95% non-condensing
    - IP Rating: IP65 for outdoor installations
    - Vibration: IEC 61373 Category 1
    - EMC: EN50121-3-2 Class A
    
    Section 4: Maintenance Procedures
    Regular maintenance includes:
    - Monthly visual inspection of connections
    - Quarterly performance testing
    - Annual firmware updates
    - Log file analysis for error patterns
    
    Troubleshooting Common Issues:
    1. Network connectivity problems
       - Check cable connections
       - Verify VLAN configuration
       - Test with known good equipment
    
    2. Performance degradation
       - Monitor bandwidth utilization
       - Check for interference sources
       - Validate QoS settings
    
    Section 5: Standards Compliance
    This system complies with:
    - EN50155: Railway applications - Electronic equipment
    - EN50121: Railway applications - Electromagnetic compatibility  
    - TSI specifications for interoperability
    - IEC 61375: Train communication network
    - IEEE 802.1Q: Virtual LAN standard
    
    For technical support, contact ÖBB Technical Services.
    Document Version: 2.1
    Last Updated: 2024-09-29
    """
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(railway_content)
        docs['railway_manual'] = Path(f.name)
    
    # CSV data document for testing structured data processing
    csv_content = """component,model,specification,compliance,train_fleet
CCU,R4600-2Ax,1Gbps Ethernet,EN50155,CityJet
Router,RT-5000,Dual-band WiFi,EN50121,Railjet
Switch,SW-24P,24-port managed,TSI,S-Bahn
Gateway,GW-100,Multi-protocol,EN50155,Nightjet
Antenna,ANT-5G,5GHz directional,EN50121,CityJet"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(csv_content)
        docs['equipment_specs'] = Path(f.name)
    
    return docs

def test_processor_initialization():
    """Test processor initialization and configuration"""
    print("🔧 Testing processor initialization...")
    
    try:
        processor = BMSDocumentProcessor()
        status = processor.get_processing_status()
        
        print(f"✅ Processor initialized successfully")
        print(f"   Enhanced Processor Available: {status['enhanced_processor_available']}")
        print(f"   Qdrant Available: {status['qdrant_available']}")
        print(f"   Ollama Available: {status['ollama_available']}")
        print(f"   Collection Name: {status['collection_name']}")
        
        enabled_features = status.get('enabled_features', [])
        print(f"   Enabled Features ({len(enabled_features)}): {', '.join(enabled_features)}")
        
        # Validate all expected v4.0 features are enabled
        expected_features = [
            'contextual_retrieval',
            'hierarchical_chunking', 
            'late_chunking',
            'quality_validation',
            'hybrid_search_prep',
            'entity_extraction',
            'advanced_preprocessing',
            'railway_processing',
            'version_tracking'
        ]
        
        missing_features = [f for f in expected_features if f not in enabled_features]
        if missing_features:
            print(f"⚠️  Missing expected features: {', '.join(missing_features)}")
        else:
            print(f"✅ All expected v4.0 features are enabled")
        
        return processor, True
        
    except Exception as e:
        print(f"❌ Processor initialization failed: {e}")
        return None, False

def test_document_processing(processor: BMSDocumentProcessor, test_docs: Dict[str, Path]):
    """Test document processing with all engines"""
    print("\n📄 Testing document processing...")
    
    results = {}
    
    for doc_name, doc_path in test_docs.items():
        print(f"\n🔍 Processing {doc_name}...")
        
        try:
            # Determine processing profile
            profile = "railway" if "railway" in doc_name else "general"
            
            # Process document
            result = processor.process_document(str(doc_path), profile)
            results[doc_name] = result
            
            if result.status == "success":
                print(f"✅ {doc_name} processed successfully")
                print(f"   Document ID: {result.document_id}")
                print(f"   Chunks Created: {result.chunks_created}")
                print(f"   Quality Score: {result.quality_score:.1f}")
                print(f"   Processing Time: {result.processing_time_ms}ms")
                print(f"   Features Used: {', '.join(result.features_extracted)}")
                
                # Validate expected features were used
                expected_features = ['contextual_retrieval', 'hierarchical_chunking', 'quality_validation']
                used_features = result.features_extracted
                
                for feature in expected_features:
                    if feature in used_features:
                        print(f"   ✅ {feature}: Active")
                    else:
                        print(f"   ⚠️  {feature}: Not detected")
                
            else:
                print(f"❌ {doc_name} processing failed: {result.error}")
                
        except Exception as e:
            print(f"❌ Error processing {doc_name}: {e}")
            results[doc_name] = None
    
    return results

def test_qdrant_storage(processor: BMSDocumentProcessor):
    """Test Qdrant storage and retrieval"""
    print("\n💾 Testing Qdrant storage...")
    
    if not processor.qdrant_client:
        print("❌ Qdrant client not available - skipping storage tests")
        return False
    
    try:
        # Get collection info
        collection_info = processor.qdrant_client.get_collection(processor.collection_name)
        
        print(f"✅ Collection '{processor.collection_name}' accessible")
        print(f"   Status: {collection_info.status}")
        print(f"   Points Count: {collection_info.points_count}")
        print(f"   Vectors Count: {collection_info.vectors_count}")
        
        # Check vector configurations
        vectors_config = collection_info.config.params.vectors
        expected_vectors = ["chunk_embedding", "parent_embedding", "child_embedding", "full_doc_embedding"]
        
        print(f"   Vector Types:")
        for vector_name in expected_vectors:
            if vector_name in vectors_config:
                size = vectors_config[vector_name].size
                print(f"     ✅ {vector_name}: {size}D")
            else:
                print(f"     ❌ {vector_name}: Missing")
        
        # Check sparse vectors
        sparse_config = getattr(collection_info.config.params, 'sparse_vectors', None)
        if sparse_config and "keyword_sparse" in sparse_config:
            print(f"     ✅ keyword_sparse: Configured")
        else:
            print(f"     ⚠️  keyword_sparse: Not configured")
        
        return True
        
    except Exception as e:
        print(f"❌ Qdrant storage test failed: {e}")
        return False

def test_search_functionality(processor: BMSDocumentProcessor):
    """Test search functionality (basic validation)"""
    print("\n🔍 Testing search functionality...")
    
    if not processor.qdrant_client:
        print("❌ Qdrant client not available - skipping search tests")
        return False
    
    try:
        # Test basic search query (this would be expanded in actual search endpoints)
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        
        # Search for documents with railway profile
        search_filter = Filter(
            must=[
                FieldCondition(
                    key="processing_profile",
                    match=MatchValue(value="railway")
                )
            ]
        )
        
        # Get some points to verify storage
        points = processor.qdrant_client.scroll(
            collection_name=processor.collection_name,
            scroll_filter=search_filter,
            limit=5
        )
        
        if points[0]:  # points is a tuple (points, next_page_offset)
            print(f"✅ Found {len(points[0])} railway documents in collection")
            
            # Check first point structure
            first_point = points[0][0]
            payload = first_point.payload
            
            print(f"   Sample point structure:")
            print(f"     Document ID: {payload.get('document_id', 'N/A')}")
            print(f"     Chunk Type: {payload.get('chunk_type', 'N/A')}")
            print(f"     Quality Score: {payload.get('quality_score', 'N/A')}")
            print(f"     Has Context: {payload.get('has_context', 'N/A')}")
            print(f"     Processing Version: {payload.get('processing_version', 'N/A')}")
            
            return True
        else:
            print("⚠️  No points found in collection")
            return False
            
    except Exception as e:
        print(f"❌ Search functionality test failed: {e}")
        return False

def generate_test_report(processor_status: bool, 
                        processing_results: Dict[str, Any],
                        storage_status: bool,
                        search_status: bool):
    """Generate comprehensive test report"""
    print("\n" + "="*60)
    print("ENHANCED DOCUMENT PROCESSOR v4.0 TEST REPORT")
    print("="*60)
    
    # Overall status
    all_tests_passed = processor_status and storage_status and search_status
    overall_status = "✅ PASS" if all_tests_passed else "❌ FAIL"
    print(f"Overall Status: {overall_status}")
    print()
    
    # Component status
    print("Component Status:")
    print(f"  Processor Initialization: {'✅ PASS' if processor_status else '❌ FAIL'}")
    print(f"  Qdrant Storage: {'✅ PASS' if storage_status else '❌ FAIL'}")
    print(f"  Search Functionality: {'✅ PASS' if search_status else '❌ FAIL'}")
    print()
    
    # Document processing results
    print("Document Processing Results:")
    for doc_name, result in processing_results.items():
        if result and result.status == "success":
            print(f"  {doc_name}: ✅ PASS ({result.chunks_created} chunks, {result.quality_score:.1f} quality)")
        else:
            error = result.error if result else "Unknown error"
            print(f"  {doc_name}: ❌ FAIL ({error})")
    print()
    
    # Feature coverage validation
    if processing_results:
        sample_result = next((r for r in processing_results.values() if r and r.status == "success"), None)
        if sample_result:
            features_used = sample_result.features_extracted
            expected_features = [
                'contextual_retrieval', 'hierarchical_chunking', 'late_chunking',
                'quality_validation', 'hybrid_search_prep', 'entity_extraction',
                'advanced_preprocessing', 'railway_processing', 'version_tracking'
            ]
            
            print("Enhanced Document Processor v4.0 Feature Coverage:")
            for feature in expected_features:
                status = "✅ ACTIVE" if feature in features_used else "❌ MISSING"
                print(f"  {feature}: {status}")
    
    print("\n" + "="*60)
    
    # Save report to file
    report_data = {
        "timestamp": str(Path(__file__).stat().st_mtime),
        "overall_status": "PASS" if all_tests_passed else "FAIL",
        "component_status": {
            "processor_initialization": processor_status,
            "qdrant_storage": storage_status,
            "search_functionality": search_status
        },
        "processing_results": {
            name: {
                "status": result.status if result else "error",
                "chunks_created": result.chunks_created if result else 0,
                "quality_score": result.quality_score if result else 0.0,
                "features_extracted": result.features_extracted if result else []
            } for name, result in processing_results.items()
        }
    }
    
    try:
        report_path = project_root / "processor_test_report.json"
        with open(report_path, 'w') as f:
            json.dump(report_data, f, indent=2)
        print(f"📄 Detailed report saved to: {report_path}")
    except Exception as e:
        print(f"⚠️  Could not save report: {e}")

def main():
    """Main test execution"""
    print("🚀 Enhanced Document Processor v4.0 Integration Test")
    print("="*60)
    
    if not PROCESSOR_AVAILABLE:
        print("❌ Processor wrapper not available - cannot run tests")
        return 1
    
    # Create test documents
    print("📝 Creating test documents...")
    test_docs = create_test_documents()
    print(f"✅ Created {len(test_docs)} test documents")
    
    try:
        # Test 1: Processor initialization
        processor, processor_status = test_processor_initialization()
        
        # Test 2: Document processing
        processing_results = {}
        if processor:
            processing_results = test_document_processing(processor, test_docs)
        
        # Test 3: Qdrant storage
        storage_status = False
        if processor:
            storage_status = test_qdrant_storage(processor)
        
        # Test 4: Search functionality
        search_status = False
        if processor:
            search_status = test_search_functionality(processor)
        
        # Generate report
        generate_test_report(processor_status, processing_results, storage_status, search_status)
        
        # Cleanup
        print("\n🧹 Cleaning up test documents...")
        for doc_path in test_docs.values():
            if doc_path.exists():
                doc_path.unlink()
        
        # Return appropriate exit code
        all_passed = processor_status and storage_status and search_status
        return 0 if all_passed else 1
        
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
