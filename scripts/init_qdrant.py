#!/usr/bin/env python3
"""
Qdrant Collection Initializer for BMS Agent
Creates the nomad_bms_documents collection with multi-vector support
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "bms-agent" / "scr"))

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import (
        Distance, VectorParams, PointStruct, 
        CollectionInfo, OptimizersConfig, OptimizersConfigDiff, HnswConfigDiff,
        PayloadSchemaType, TextIndexParams,
        TokenizerType, SparseVectorParams
    )
except ImportError as e:
    print(f"❌ Error importing Qdrant client: {e}")
    print("Please install qdrant-client: pip install qdrant-client")
    sys.exit(1)

class QdrantInitializer:
    """Initialize Qdrant collection for BMS Agent"""
    
    def __init__(self, host: str = "localhost", port: int = 6333):
        self.client = QdrantClient(host=host, port=port, check_compatibility=False)
        self.collection_name = "nomad_bms_documents"
        
    def create_collection(self, force_recreate: bool = False) -> bool:
        """Create the BMS documents collection with multi-vector support"""
        
        try:
            # Check if collection exists
            collections = self.client.get_collections().collections
            exists = any(c.name == self.collection_name for c in collections)
            
            if exists and not force_recreate:
                print(f"✅ Collection '{self.collection_name}' already exists")
                return True
            elif exists and force_recreate:
                print(f"🗑️  Deleting existing collection '{self.collection_name}'")
                self.client.delete_collection(self.collection_name)
            
            print(f"🚀 Creating collection '{self.collection_name}' with multi-vector support...")
            
            # Create collection with multiple vector types
            self.client.create_collection(
                collection_name=self.collection_name,
                
                # Multi-vector configuration for Enhanced Document Processor v4.0
                vectors_config={
                    # Main chunk embedding (for standard retrieval)
                    "chunk_embedding": VectorParams(
                        size=1024,  # snowflake-arctic-embed2 dimensions
                        distance=Distance.COSINE
                    ),
                    
                    # Parent embedding (for hierarchical retrieval)
                    "parent_embedding": VectorParams(
                        size=1024,
                        distance=Distance.COSINE,
                        on_disk=False  # Keep in memory for fast access
                    ),
                    
                    # Child embedding (for precise matching)
                    "child_embedding": VectorParams(
                        size=1024,
                        distance=Distance.COSINE
                    ),
                    
                    # Full document embedding (from late chunking)
                    "full_doc_embedding": VectorParams(
                        size=1024,
                        distance=Distance.COSINE,
                        on_disk=True  # Can be on disk as accessed less frequently
                    )
                },
                
                # Sparse vectors for hybrid search (BM25)
                sparse_vectors_config={
                    "keyword_sparse": SparseVectorParams()
                },
                
                # Optimization settings
                optimizers_config=OptimizersConfigDiff(
                    deleted_threshold=0.2,
                    vacuum_min_vector_number=1000,
                    default_segment_number=0,
                    max_segment_size=200000,
                    indexing_threshold=20000,
                    flush_interval_sec=5
                ),
                
                # HNSW configuration for performance
                hnsw_config=HnswConfigDiff(
                    m=16,
                    ef_construct=100,
                    full_scan_threshold=10000
                )
            )
            
            print(f"✅ Collection '{self.collection_name}' created successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create collection: {e}")
            return False
    
    def create_payload_indexes(self) -> bool:
        """Create optimized payload indexes for filtering and search"""
        
        try:
            print("🔍 Creating payload indexes...")
            
            # Document-level indexes
            document_indexes = [
                ("document_id", PayloadSchemaType.KEYWORD),
                ("document_name", PayloadSchemaType.KEYWORD),
                ("document_type", PayloadSchemaType.KEYWORD),
                ("document_version", PayloadSchemaType.FLOAT),
                ("processing_profile", PayloadSchemaType.KEYWORD),
                ("processing_timestamp", PayloadSchemaType.KEYWORD),
            ]
            
            # Chunk-level indexes
            chunk_indexes = [
                ("chunk_id", PayloadSchemaType.KEYWORD),
                ("chunk_type", PayloadSchemaType.KEYWORD),
                ("hierarchy_level", PayloadSchemaType.KEYWORD),
                ("parent_chunk_id", PayloadSchemaType.KEYWORD),
                ("chunk_index", PayloadSchemaType.INTEGER),
                ("quality_score", PayloadSchemaType.FLOAT),
                ("chunk_size", PayloadSchemaType.INTEGER),
            ]
            
            # Railway-specific indexes (ÖBB)
            railway_indexes = [
                ("fleet_type", PayloadSchemaType.KEYWORD),
                ("train_id", PayloadSchemaType.KEYWORD),
                ("standard_compliance", PayloadSchemaType.KEYWORD),
                ("network_component", PayloadSchemaType.KEYWORD),
                ("configuration_type", PayloadSchemaType.KEYWORD),
            ]
            
            # Search optimization indexes
            search_indexes = [
                ("search_type", PayloadSchemaType.KEYWORD),
                ("has_context", PayloadSchemaType.BOOL),
                ("is_parent", PayloadSchemaType.BOOL),
                ("is_child", PayloadSchemaType.BOOL),
                ("context_type", PayloadSchemaType.KEYWORD),
                ("late_chunking_applied", PayloadSchemaType.BOOL),
                ("processing_version", PayloadSchemaType.KEYWORD),
            ]
            
            # Create all indexes
            all_indexes = (
                document_indexes + 
                chunk_indexes + 
                railway_indexes + 
                search_indexes
            )
            
            for field_name, field_type in all_indexes:
                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name=field_name,
                    field_schema=field_type
                )
                print(f"  ✓ Created index: {field_name} ({field_type})")
            
            # Create text indexes for full-text search
            text_indexes = [
                ("content", "Full-text search"),
                ("keywords", "Extracted keywords"),
                ("entities", "Named entities"),
                ("contextual_description", "Contextual descriptions"),
                ("surrounding_context", "Surrounding context"),
                ("technical_terms", "Technical terminology"),
            ]
            
            for field_name, description in text_indexes:
                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name=field_name,
                    field_schema=TextIndexParams(
                        type="text",
                        tokenizer=TokenizerType.WORD,
                        min_token_len=2,
                        max_token_len=20,
                        lowercase=True
                    )
                )
                print(f"  ✓ Created text index: {field_name} ({description})")
            
            print("✅ All payload indexes created successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create indexes: {e}")
            return False
    
    def verify_collection(self) -> bool:
        """Verify collection setup and configuration"""
        
        try:
            print("🔍 Verifying collection setup...")
            
            # Get collection info
            info = self.client.get_collection(self.collection_name)
            
            print(f"✅ Collection verified:")
            print(f"   Name: {info.config.params.vectors}")
            print(f"   Status: {info.status}")
            print(f"   Vectors count: {info.vectors_count}")
            print(f"   Points count: {info.points_count}")
            
            # Check vector configurations
            vectors_config = info.config.params.vectors
            expected_vectors = ["chunk_embedding", "parent_embedding", "child_embedding", "full_doc_embedding"]
            
            for vector_name in expected_vectors:
                if vector_name in vectors_config:
                    print(f"   ✓ Vector '{vector_name}': {vectors_config[vector_name].size}D")
                else:
                    print(f"   ❌ Missing vector: {vector_name}")
                    return False
            
            # Check sparse vectors
            if hasattr(info.config.params, 'sparse_vectors') and info.config.params.sparse_vectors:
                if "keyword_sparse" in info.config.params.sparse_vectors:
                    print(f"   ✓ Sparse vector 'keyword_sparse' configured")
                else:
                    print(f"   ❌ Missing sparse vector: keyword_sparse")
            
            return True
            
        except Exception as e:
            print(f"❌ Collection verification failed: {e}")
            return False

def main():
    """Main initialization function"""
    
    print("🚀 BMS Agent Qdrant Collection Initializer")
    print("=" * 50)
    
    # Parse command line arguments
    force_recreate = "--force" in sys.argv
    
    if force_recreate:
        print("⚠️  Force recreate mode enabled")
    
    # Initialize Qdrant
    try:
        initializer = QdrantInitializer()
        
        # Create collection
        if not initializer.create_collection(force_recreate=force_recreate):
            sys.exit(1)
        
        # Create indexes
        if not initializer.create_payload_indexes():
            sys.exit(1)
        
        # Verify setup
        if not initializer.verify_collection():
            sys.exit(1)
        
        print("\n🎉 Qdrant collection initialization completed successfully!")
        print(f"   Collection: {initializer.collection_name}")
        print(f"   Multi-vector support: ✅")
        print(f"   Sparse vectors: ✅")
        print(f"   Payload indexes: ✅")
        print(f"   Ready for Enhanced Document Processor v4.0!")
        
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
