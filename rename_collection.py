#!/usr/bin/env python3
"""
Rename Qdrant collection by copying data to new collection
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'bms-agent' / 'scr'))

from qdrant_client import QdrantClient
from qdrant_schema_v4 import QdrantSchemaV4, QdrantConfig

def rename_collection(old_name: str, new_name: str):
    """Copy collection to new name and delete old one"""

    client = QdrantClient(url="http://localhost:6333")

    print(f"Starting collection rename: {old_name} -> {new_name}")
    print("="*70)

    # 1. Verify old collection exists
    try:
        old_info = client.get_collection(old_name)
        print(f"✅ Source collection '{old_name}' found")
        print(f"   Points: {old_info.points_count}")
        print(f"   Status: {old_info.status}")
    except Exception as e:
        print(f"❌ Source collection '{old_name}' not found: {e}")
        return False

    # 2. Create new collection with same schema
    print(f"\n📦 Creating new collection '{new_name}'...")
    new_config = QdrantConfig(
        collection_name=new_name,
        enable_railway_optimization=True
    )
    new_schema = QdrantSchemaV4(new_config)
    try:
        new_schema.create_collection()
        print(f"✅ Collection '{new_name}' created")
    except Exception as e:
        print(f"⚠️  Collection creation: {e}")

    # 3. Copy all points
    print(f"\n🔄 Copying points from '{old_name}' to '{new_name}'...")

    batch_size = 100
    offset = None
    total_copied = 0

    while True:
        # Scroll through old collection
        records, next_offset = client.scroll(
            collection_name=old_name,
            limit=batch_size,
            offset=offset,
            with_payload=True,
            with_vectors=True
        )

        if not records:
            break

        # Batch upsert to new collection
        client.upsert(
            collection_name=new_name,
            points=records
        )

        total_copied += len(records)
        print(f"   Copied {total_copied} points...", end='\r')

        if next_offset is None:
            break
        offset = next_offset

    print(f"\n✅ Copied {total_copied} points")

    # 4. Verify new collection
    new_info = client.get_collection(new_name)
    print(f"\n📊 New collection status:")
    print(f"   Name: {new_name}")
    print(f"   Points: {new_info.points_count}")
    print(f"   Status: {new_info.status}")

    if new_info.points_count == old_info.points_count:
        print(f"\n✅ Point count matches! ({new_info.points_count} == {old_info.points_count})")

        # 5. Delete old collection
        print(f"\n🗑️  Deleting old collection '{old_name}'...")
        client.delete_collection(old_name)
        print(f"✅ Old collection deleted")

        print(f"\n{'='*70}")
        print(f"✅ Collection successfully renamed to '{new_name}'")
        print(f"{'='*70}")
        return True
    else:
        print(f"\n❌ Point count mismatch! {new_info.points_count} != {old_info.points_count}")
        print(f"   Old collection '{old_name}' preserved for safety")
        return False

if __name__ == "__main__":
    success = rename_collection("railway_documents_v4", "nomad_bms_documents")
    sys.exit(0 if success else 1)
