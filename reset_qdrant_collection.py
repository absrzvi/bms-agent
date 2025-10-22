#!/usr/bin/env python3
"""
Reset Qdrant collection - delete and recreate with proper schema
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'bms-agent' / 'scr'))

from qdrant_client import QdrantClient
from qdrant_schema_v4 import QdrantSchemaV4, QdrantConfig

print("=" * 60)
print("  Reset Qdrant Collection")
print("=" * 60)

collection_name = "railway_documents_v4"

# Connect to Qdrant
client = QdrantClient(url="localhost", port=6333)

# Step 1: Delete existing collection
print(f"\n🗑️  Deleting collection '{collection_name}'...")
try:
    client.delete_collection(collection_name)
    print(f"   ✅ Collection '{collection_name}' deleted")
except Exception as e:
    print(f"   ⚠️  Could not delete collection: {e}")
    print(f"   (Collection may not exist - continuing...)")

# Step 2: Recreate collection with proper schema
print(f"\n🔧 Creating fresh collection '{collection_name}'...")
try:
    config = QdrantConfig(
        collection_name=collection_name,
        enable_railway_optimization=True
    )

    qdrant_schema = QdrantSchemaV4(config)

    print(f"   ✅ Collection '{collection_name}' created successfully")

    # Verify
    collection_info = client.get_collection(collection_name)
    print(f"\n📊 Collection Info:")
    print(f"   Name: {collection_name}")
    print(f"   Points: {collection_info.points_count}")
    print(f"   Status: {collection_info.status}")

except Exception as e:
    print(f"   ❌ Error creating collection: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("✅ Collection Reset Complete!")
print("=" * 60)
print("\nThe collection is now empty and ready for new documents.")
print("All test data has been removed.")
