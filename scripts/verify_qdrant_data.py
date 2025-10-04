#!/usr/bin/env python3
"""
Qdrant Database Verification Script
Comprehensive validation of collection schema, metadata, indexes, and data quality
"""

import json
import sys
from typing import Dict, List, Any
from collections import Counter
import requests

QDRANT_URL = "http://localhost:6333"
COLLECTION_NAME = "nomad_bms_documents"

def get_collection_info() -> Dict[str, Any]:
    """Get collection configuration and statistics"""
    response = requests.get(f"{QDRANT_URL}/collections/{COLLECTION_NAME}")
    response.raise_for_status()
    return response.json()["result"]

def scroll_points(limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    """Scroll through collection points"""
    payload = {
        "limit": limit,
        "with_payload": True,
        "with_vector": False,
        "offset": offset
    }
    response = requests.post(
        f"{QDRANT_URL}/collections/{COLLECTION_NAME}/points/scroll",
        json=payload
    )
    response.raise_for_status()
    return response.json()["result"]["points"]

def verify_schema(info: Dict[str, Any]) -> Dict[str, Any]:
    """Verify collection schema configuration"""
    print("\n" + "="*80)
    print("SCHEMA VERIFICATION")
    print("="*80)
    
    results = {
        "status": "PASS",
        "issues": [],
        "warnings": []
    }
    
    # Check vector configuration
    vectors = info["config"]["params"]["vectors"]
    expected_vectors = ["chunk_embedding", "parent_embedding", "child_embedding", "full_doc_embedding"]
    
    print(f"\n✓ Vector Configuration:")
    for vec_name in expected_vectors:
        if vec_name in vectors:
            vec_config = vectors[vec_name]
            size = vec_config["size"]
            distance = vec_config["distance"]
            on_disk = vec_config.get("on_disk", False)
            
            if size != 768:
                results["issues"].append(f"{vec_name}: Wrong dimension {size}, expected 768")
                results["status"] = "FAIL"
            if distance != "Cosine":
                results["warnings"].append(f"{vec_name}: Distance metric is {distance}, expected Cosine")
            
            print(f"  - {vec_name}: {size}d, {distance}, on_disk={on_disk}")
        else:
            results["issues"].append(f"Missing vector: {vec_name}")
            results["status"] = "FAIL"
    
    # Check sparse vectors
    sparse_vectors = info["config"]["params"].get("sparse_vectors", {})
    if "keyword_sparse" in sparse_vectors:
        print(f"\n✓ Sparse Vectors: keyword_sparse configured")
    else:
        results["warnings"].append("Missing sparse vector: keyword_sparse")
    
    # Check HNSW configuration
    hnsw = info["config"]["hnsw_config"]
    print(f"\n✓ HNSW Configuration:")
    print(f"  - m: {hnsw['m']}")
    print(f"  - ef_construct: {hnsw['ef_construct']}")
    print(f"  - full_scan_threshold: {hnsw['full_scan_threshold']}")
    
    # Check on-disk payload
    on_disk_payload = info["config"]["params"]["on_disk_payload"]
    print(f"\n✓ Storage: on_disk_payload={on_disk_payload}")
    
    return results

def verify_indexes(info: Dict[str, Any]) -> Dict[str, Any]:
    """Verify payload indexes"""
    print("\n" + "="*80)
    print("INDEX VERIFICATION")
    print("="*80)
    
    results = {
        "status": "PASS",
        "issues": [],
        "warnings": []
    }
    
    payload_schema = info.get("payload_schema", {})
    
    # Expected indexed fields
    expected_keyword_indexes = [
        "document_id", "document_name", "document_type", "chunk_id",
        "chunk_type", "hierarchy_level", "processing_version",
        "network_component", "department", "configuration_type",
        "standard_compliance", "train_id", "fleet_type", "search_type",
        "context_type", "processing_profile"
    ]
    
    expected_text_indexes = [
        "content", "keywords", "technical_terms", "entities",
        "surrounding_context", "contextual_description"
    ]
    
    expected_numeric_indexes = [
        "quality_score", "document_version", "chunk_index", "chunk_size"
    ]
    
    expected_bool_indexes = [
        "is_parent", "is_child", "has_context", "late_chunking_applied"
    ]
    
    print(f"\n✓ Keyword Indexes ({len(expected_keyword_indexes)} expected):")
    for field in expected_keyword_indexes:
        if field in payload_schema:
            data_type = payload_schema[field]["data_type"]
            points = payload_schema[field]["points"]
            if data_type == "keyword":
                print(f"  ✓ {field}: {points} points")
            else:
                results["issues"].append(f"{field}: Wrong type {data_type}, expected keyword")
                results["status"] = "FAIL"
        else:
            results["warnings"].append(f"Missing keyword index: {field}")
    
    print(f"\n✓ Text Indexes ({len(expected_text_indexes)} expected):")
    for field in expected_text_indexes:
        if field in payload_schema:
            data_type = payload_schema[field]["data_type"]
            points = payload_schema[field]["points"]
            if data_type == "text":
                print(f"  ✓ {field}: {points} points")
            else:
                results["issues"].append(f"{field}: Wrong type {data_type}, expected text")
                results["status"] = "FAIL"
        else:
            results["warnings"].append(f"Missing text index: {field}")
    
    print(f"\n✓ Numeric Indexes ({len(expected_numeric_indexes)} expected):")
    for field in expected_numeric_indexes:
        if field in payload_schema:
            data_type = payload_schema[field]["data_type"]
            points = payload_schema[field]["points"]
            expected_type = "float" if field in ["quality_score", "document_version"] else "integer"
            if data_type == expected_type:
                print(f"  ✓ {field}: {points} points ({data_type})")
            else:
                results["issues"].append(f"{field}: Wrong type {data_type}, expected {expected_type}")
                results["status"] = "FAIL"
        else:
            results["warnings"].append(f"Missing numeric index: {field}")
    
    print(f"\n✓ Boolean Indexes ({len(expected_bool_indexes)} expected):")
    for field in expected_bool_indexes:
        if field in payload_schema:
            data_type = payload_schema[field]["data_type"]
            points = payload_schema[field]["points"]
            if data_type == "bool":
                print(f"  ✓ {field}: {points} points")
            else:
                results["issues"].append(f"{field}: Wrong type {data_type}, expected bool")
                results["status"] = "FAIL"
        else:
            results["warnings"].append(f"Missing boolean index: {field}")
    
    return results

def verify_data_quality(sample_size: int = 500) -> Dict[str, Any]:
    """Verify data quality and completeness"""
    print("\n" + "="*80)
    print("DATA QUALITY VERIFICATION")
    print("="*80)
    
    results = {
        "status": "PASS",
        "issues": [],
        "warnings": [],
        "stats": {}
    }
    
    # Sample points
    points = scroll_points(limit=sample_size)
    
    # Statistics
    doc_types = Counter()
    quality_scores = []
    missing_fields = Counter()
    chunk_types = Counter()
    processing_versions = Counter()
    
    required_fields = [
        "document_id", "document_name", "document_type", "content",
        "chunk_id", "chunk_index", "quality_score", "processing_version"
    ]
    
    for point in points:
        payload = point["payload"]
        
        # Check required fields
        for field in required_fields:
            if field not in payload or payload[field] is None:
                missing_fields[field] += 1
        
        # Collect statistics
        if payload.get("document_type"):
            doc_types[payload["document_type"]] += 1
        
        if payload.get("quality_score") is not None:
            quality_scores.append(payload["quality_score"])
        
        if payload.get("chunk_type"):
            chunk_types[payload["chunk_type"]] += 1
        
        if payload.get("processing_version"):
            processing_versions[payload["processing_version"]] += 1
    
    # Report statistics
    print(f"\n✓ Sample Size: {len(points)} points")
    
    print(f"\n✓ Document Types:")
    for doc_type, count in doc_types.most_common():
        print(f"  - {doc_type}: {count} chunks ({count/len(points)*100:.1f}%)")
    
    if quality_scores:
        avg_quality = sum(quality_scores) / len(quality_scores)
        min_quality = min(quality_scores)
        max_quality = max(quality_scores)
        print(f"\n✓ Quality Scores:")
        print(f"  - Average: {avg_quality:.3f}")
        print(f"  - Range: {min_quality:.3f} - {max_quality:.3f}")
        print(f"  - Points with scores: {len(quality_scores)}/{len(points)} ({len(quality_scores)/len(points)*100:.1f}%)")
        
        if min_quality < 0.70:
            results["warnings"].append(f"Some chunks below quality threshold (min: {min_quality:.3f})")
    
    print(f"\n✓ Chunk Types:")
    for chunk_type, count in chunk_types.most_common():
        print(f"  - {chunk_type}: {count} chunks ({count/len(points)*100:.1f}%)")
    
    print(f"\n✓ Processing Versions:")
    for version, count in processing_versions.most_common():
        print(f"  - {version}: {count} chunks ({count/len(points)*100:.1f}%)")
    
    # Check for missing fields
    if missing_fields:
        print(f"\n⚠ Missing Required Fields:")
        for field, count in missing_fields.most_common():
            pct = count / len(points) * 100
            print(f"  - {field}: {count}/{len(points)} points ({pct:.1f}%)")
            if pct > 10:
                results["issues"].append(f"{field} missing in {pct:.1f}% of points")
                results["status"] = "FAIL"
            else:
                results["warnings"].append(f"{field} missing in {pct:.1f}% of points")
    
    results["stats"] = {
        "sample_size": len(points),
        "document_types": dict(doc_types),
        "avg_quality": sum(quality_scores) / len(quality_scores) if quality_scores else 0,
        "chunk_types": dict(chunk_types),
        "processing_versions": dict(processing_versions)
    }
    
    return results

def verify_vectors(sample_size: int = 10) -> Dict[str, Any]:
    """Verify vector embeddings"""
    print("\n" + "="*80)
    print("VECTOR VERIFICATION")
    print("="*80)
    
    results = {
        "status": "PASS",
        "issues": [],
        "warnings": []
    }
    
    # Get points with vectors
    payload = {
        "limit": sample_size,
        "with_payload": False,
        "with_vector": True
    }
    response = requests.post(
        f"{QDRANT_URL}/collections/{COLLECTION_NAME}/points/scroll",
        json=payload
    )
    response.raise_for_status()
    points = response.json()["result"]["points"]
    
    vector_names = ["chunk_embedding", "parent_embedding", "child_embedding", "full_doc_embedding"]
    
    for vec_name in vector_names:
        vectors_found = 0
        for point in points:
            if vec_name in point.get("vector", {}):
                vectors_found += 1
                vec = point["vector"][vec_name]
                if len(vec) != 768:
                    results["issues"].append(f"{vec_name}: Wrong dimension {len(vec)}, expected 768")
                    results["status"] = "FAIL"
        
        print(f"  ✓ {vec_name}: {vectors_found}/{len(points)} points have vectors")
        
        if vectors_found == 0:
            results["warnings"].append(f"No {vec_name} vectors found in sample")
    
    return results

def main():
    """Main verification workflow"""
    print("\n" + "="*80)
    print("QDRANT DATABASE VERIFICATION")
    print(f"Collection: {COLLECTION_NAME}")
    print("="*80)
    
    try:
        # Get collection info
        info = get_collection_info()
        
        print(f"\n✓ Collection Status: {info['status']}")
        print(f"✓ Points: {info['points_count']:,}")
        print(f"✓ Vectors: {info['vectors_count']:,}")
        print(f"✓ Segments: {info['segments_count']}")
        print(f"✓ Optimizer: {info['optimizer_status']}")
        
        # Run verifications
        schema_results = verify_schema(info)
        index_results = verify_indexes(info)
        data_results = verify_data_quality(sample_size=500)
        vector_results = verify_vectors(sample_size=10)
        
        # Summary
        print("\n" + "="*80)
        print("VERIFICATION SUMMARY")
        print("="*80)
        
        all_results = [schema_results, index_results, data_results, vector_results]
        
        total_issues = sum(len(r["issues"]) for r in all_results)
        total_warnings = sum(len(r["warnings"]) for r in all_results)
        
        overall_status = "PASS" if all(r["status"] == "PASS" for r in all_results) else "FAIL"
        
        print(f"\n{'✓' if overall_status == 'PASS' else '✗'} Overall Status: {overall_status}")
        print(f"  - Critical Issues: {total_issues}")
        print(f"  - Warnings: {total_warnings}")
        
        if total_issues > 0:
            print(f"\n✗ Critical Issues:")
            for r in all_results:
                for issue in r["issues"]:
                    print(f"  - {issue}")
        
        if total_warnings > 0:
            print(f"\n⚠ Warnings:")
            for r in all_results:
                for warning in r["warnings"]:
                    print(f"  - {warning}")
        
        # Data statistics
        if "stats" in data_results:
            stats = data_results["stats"]
            print(f"\n✓ Data Statistics:")
            print(f"  - Sample Size: {stats['sample_size']} points")
            print(f"  - Document Types: {len(stats['document_types'])}")
            print(f"  - Average Quality: {stats['avg_quality']:.3f}")
            print(f"  - Processing Versions: {list(stats['processing_versions'].keys())}")
        
        print("\n" + "="*80)
        
        # Exit code
        sys.exit(0 if overall_status == "PASS" else 1)
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
