#!/usr/bin/env python3
"""
Clean up test data from Qdrant database
"""

from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

print("=" * 60)
print("  Cleaning Test Data from Qdrant")
print("=" * 60)

# Connect to Qdrant
client = QdrantClient(url="localhost", port=6333)

collection_name = "railway_documents_v4"

# List of test document IDs we created
test_document_ids = [
    "chapter_test",
    "chapter_test_1",
    "chapter_test_2",
    "chapter_test_3",
    "test_simple"
]

print(f"\n📊 Collection: {collection_name}")

# Get collection info
try:
    collection_info = client.get_collection(collection_name)
    print(f"   Total points before cleanup: {collection_info.points_count}")
except Exception as e:
    print(f"❌ Error getting collection info: {e}")
    exit(1)

# Delete test documents
print(f"\n🗑️  Deleting test documents...")

total_deleted = 0

for doc_id in test_document_ids:
    try:
        # Count points with this document_id
        points = client.scroll(
            collection_name=collection_name,
            scroll_filter=Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=doc_id)
                    )
                ]
            ),
            limit=1000,
            with_payload=False,
            with_vectors=False
        )[0]

        count = len(points)

        if count > 0:
            print(f"   Found {count} chunks for document_id='{doc_id}'")

            # Delete by filter
            client.delete(
                collection_name=collection_name,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="document_id",
                            match=MatchValue(value=doc_id)
                        )
                    ]
                )
            )

            total_deleted += count
            print(f"   ✅ Deleted {count} chunks from '{doc_id}'")
        else:
            print(f"   ⚪ No chunks found for '{doc_id}'")

    except Exception as e:
        print(f"   ❌ Error deleting '{doc_id}': {e}")

# Get updated collection info
try:
    collection_info = client.get_collection(collection_name)
    print(f"\n📊 Total points after cleanup: {collection_info.points_count}")
    print(f"🗑️  Total deleted: {total_deleted} chunks")
except Exception as e:
    print(f"❌ Error getting updated collection info: {e}")

print("\n" + "=" * 60)
print("✅ Cleanup Complete!")
print("=" * 60)
