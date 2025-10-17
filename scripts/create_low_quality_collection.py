#!/usr/bin/env python3
"""
T037: Create Low-Quality Collection

Creates the nomad_bms_documents_low_quality collection with the same schema
as the primary collection for storing chunks with quality score <0.70.
"""

import requests
import json
import sys

QDRANT_URL = "http://localhost:6333"
COLLECTION_NAME = "nomad_bms_documents_low_quality"


def create_low_quality_collection():
    """Create low-quality collection with v4.0 schema"""
    
    # Collection configuration matching primary collection
    config = {
        "vectors": {
            "chunk_embedding": {
                "size": 768,
                "distance": "Cosine"
            },
            "parent_embedding": {
                "size": 768,
                "distance": "Cosine",
                "on_disk": False
            },
            "child_embedding": {
                "size": 768,
                "distance": "Cosine"
            },
            "full_doc_embedding": {
                "size": 768,
                "distance": "Cosine",
                "on_disk": True
            }
        },
        "sparse_vectors": {
            "keyword_sparse": {}
        },
        "shard_number": 1,
        "replication_factor": 1,
        "on_disk_payload": True
    }
    
    print(f"🔧 Creating collection: {COLLECTION_NAME}")
    print(f"📊 Configuration: v4.0 schema (768-dim multi-vector + sparse)")
    
    try:
        response = requests.put(
            f"{QDRANT_URL}/collections/{COLLECTION_NAME}",
            json=config,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code in [200, 201]:
            print(f"✅ Collection created successfully")
            
            # Verify creation
            verify_response = requests.get(f"{QDRANT_URL}/collections/{COLLECTION_NAME}")
            if verify_response.status_code == 200:
                data = verify_response.json()
                point_count = data.get("result", {}).get("points_count", 0)
                print(f"✅ Verification: Collection exists with {point_count} points")
                print(f"📋 Purpose: Store low-quality chunks (quality <0.70) for admin review")
                return True
            else:
                print(f"⚠️  Collection created but verification failed")
                return True
                
        else:
            print(f"❌ Failed to create collection: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error creating collection: {e}")
        return False


def main():
    """Main execution"""
    print("="*80)
    print("T037: CREATE LOW-QUALITY COLLECTION")
    print("="*80)
    print()
    
    # Check if collection already exists
    try:
        check_response = requests.get(f"{QDRANT_URL}/collections/{COLLECTION_NAME}")
        if check_response.status_code == 200:
            print(f"⚠️  Collection {COLLECTION_NAME} already exists")
            data = check_response.json()
            point_count = data.get("result", {}).get("points_count", 0)
            print(f"   Point count: {point_count}")
            print("\n✅ No action needed - collection already configured")
            return 0
    except:
        pass
    
    # Create collection
    success = create_low_quality_collection()
    
    print()
    print("="*80)
    if success:
        print("✅ T037 REMEDIATION COMPLETE")
        print("="*80)
        print()
        print("Next steps:")
        print("1. Re-run verification: python3 scripts/verify_qdrant_collections.py")
        print("2. Update plan.md with dual-collection documentation")
        print("3. Verify include_low_quality parameter in search endpoints")
        return 0
    else:
        print("❌ T037 REMEDIATION FAILED")
        print("="*80)
        return 1


if __name__ == "__main__":
    sys.exit(main())
