"""Optimize Qdrant vector index configuration."""

import argparse
import logging
from typing import Dict, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import (
    VectorParams, Distance, HnswConfigDiff, OptimizersConfigDiff,
    QuantizationConfig, ScalarQuantization, ScalarType, ScalarQuantizationConfig
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QdrantIndexOptimizer:
    """Optimize Qdrant index parameters for production."""
    
    # Production-optimized HNSW parameters
    HNSW_CONFIGS = {
        "balanced": {
            "m": 16,
            "ef_construct": 100,
            "full_scan_threshold": 10000
        },
        "high_recall": {
            "m": 32,
            "ef_construct": 200,
            "full_scan_threshold": 20000
        },
        "fast_search": {
            "m": 8,
            "ef_construct": 64,
            "full_scan_threshold": 5000
        },
        "memory_efficient": {
            "m": 12,
            "ef_construct": 80,
            "full_scan_threshold": 8000
        }
    }
    
    def __init__(self, qdrant_url: str = "http://localhost:6333"):
        """
        Initialize optimizer.
        
        Args:
            qdrant_url: Qdrant server URL
        """
        self.client = QdrantClient(url=qdrant_url)
    
    def get_collection_info(self, collection_name: str) -> Dict:
        """
        Get current collection configuration.
        
        Args:
            collection_name: Collection name
            
        Returns:
            Collection info dictionary
        """
        try:
            info = self.client.get_collection(collection_name)
            return {
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "status": info.status,
                "config": info.config.dict() if info.config else {}
            }
        except Exception as e:
            logger.error(f"Failed to get collection info: {e}")
            return {}
    
    def update_hnsw_config(
        self,
        collection_name: str,
        preset: str = "balanced",
        custom_config: Optional[Dict] = None
    ) -> bool:
        """
        Update HNSW configuration for collection.
        
        Args:
            collection_name: Collection name
            preset: Configuration preset (balanced, high_recall, fast_search, memory_efficient)
            custom_config: Custom HNSW parameters
            
        Returns:
            True if successful
        """
        if custom_config:
            config = custom_config
        elif preset in self.HNSW_CONFIGS:
            config = self.HNSW_CONFIGS[preset]
        else:
            logger.error(f"Unknown preset: {preset}")
            return False
        
        try:
            logger.info(f"Updating HNSW config for {collection_name}: {config}")
            
            self.client.update_collection(
                collection_name=collection_name,
                hnsw_config=HnswConfigDiff(**config)
            )
            
            logger.info("HNSW config updated successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to update HNSW config: {e}")
            return False
    
    def enable_quantization(
        self,
        collection_name: str,
        quantization_type: str = "scalar"
    ) -> bool:
        """
        Enable quantization for memory efficiency.
        
        Args:
            collection_name: Collection name
            quantization_type: Type of quantization (scalar, product)
            
        Returns:
            True if successful
        """
        try:
            if quantization_type == "scalar":
                logger.info(f"Enabling scalar quantization for {collection_name}")
                
                quantization_config = ScalarQuantization(
                    scalar=ScalarQuantizationConfig(
                        type=ScalarType.INT8,
                        quantile=0.99,
                        always_ram=True
                    )
                )
                
                self.client.update_collection(
                    collection_name=collection_name,
                    quantization_config=quantization_config
                )
                
                logger.info("Quantization enabled successfully")
                return True
            else:
                logger.error(f"Unsupported quantization type: {quantization_type}")
                return False
        except Exception as e:
            logger.error(f"Failed to enable quantization: {e}")
            return False
    
    def optimize_for_production(
        self,
        collection_name: str,
        enable_quantization: bool = True
    ) -> bool:
        """
        Apply production-optimized settings.
        
        Args:
            collection_name: Collection name
            enable_quantization: Whether to enable quantization
            
        Returns:
            True if successful
        """
        logger.info(f"Optimizing {collection_name} for production...")
        
        # Get current info
        info = self.get_collection_info(collection_name)
        points_count = info.get("points_count", 0)
        
        logger.info(f"Collection has {points_count} points")
        
        # Choose preset based on collection size
        if points_count < 10000:
            preset = "balanced"
        elif points_count < 100000:
            preset = "high_recall"
        else:
            preset = "memory_efficient"
        
        logger.info(f"Using preset: {preset}")
        
        # Update HNSW config
        if not self.update_hnsw_config(collection_name, preset=preset):
            return False
        
        # Enable quantization for large collections
        if enable_quantization and points_count > 10000:
            if not self.enable_quantization(collection_name):
                logger.warning("Quantization failed, continuing without it")
        
        logger.info("Production optimization complete")
        return True
    
    def benchmark_search(
        self,
        collection_name: str,
        query_vector: list,
        num_queries: int = 100,
        k: int = 10
    ) -> Dict:
        """
        Benchmark search performance.
        
        Args:
            collection_name: Collection name
            query_vector: Query vector
            num_queries: Number of queries to run
            k: Number of results per query
            
        Returns:
            Benchmark results
        """
        import time
        
        logger.info(f"Running {num_queries} search queries...")
        
        latencies = []
        
        for i in range(num_queries):
            start = time.time()
            
            try:
                self.client.search(
                    collection_name=collection_name,
                    query_vector=query_vector,
                    limit=k
                )
                
                latency = (time.time() - start) * 1000  # ms
                latencies.append(latency)
            except Exception as e:
                logger.error(f"Query {i} failed: {e}")
        
        if not latencies:
            return {"error": "All queries failed"}
        
        latencies.sort()
        
        return {
            "num_queries": len(latencies),
            "avg_latency_ms": sum(latencies) / len(latencies),
            "p50_latency_ms": latencies[len(latencies) // 2],
            "p95_latency_ms": latencies[int(len(latencies) * 0.95)],
            "p99_latency_ms": latencies[int(len(latencies) * 0.99)],
            "min_latency_ms": latencies[0],
            "max_latency_ms": latencies[-1]
        }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Optimize Qdrant index")
    parser.add_argument("--collection", required=True, help="Collection name")
    parser.add_argument("--url", default="http://localhost:6333", help="Qdrant URL")
    parser.add_argument("--preset", default="balanced", 
                       choices=["balanced", "high_recall", "fast_search", "memory_efficient"],
                       help="HNSW preset")
    parser.add_argument("--quantization", action="store_true", help="Enable quantization")
    parser.add_argument("--info", action="store_true", help="Show collection info only")
    parser.add_argument("--production", action="store_true", help="Apply production optimizations")
    
    args = parser.parse_args()
    
    optimizer = QdrantIndexOptimizer(qdrant_url=args.url)
    
    if args.info:
        info = optimizer.get_collection_info(args.collection)
        print(f"\nCollection Info for '{args.collection}':")
        print(f"  Points: {info.get('points_count', 0)}")
        print(f"  Vectors: {info.get('vectors_count', 0)}")
        print(f"  Status: {info.get('status', 'unknown')}")
        return
    
    if args.production:
        success = optimizer.optimize_for_production(
            args.collection,
            enable_quantization=args.quantization
        )
        if success:
            print(f"\n✅ Production optimization complete for '{args.collection}'")
        else:
            print(f"\n❌ Production optimization failed for '{args.collection}'")
        return
    
    # Manual configuration
    if args.quantization:
        optimizer.enable_quantization(args.collection)
    
    optimizer.update_hnsw_config(args.collection, preset=args.preset)
    
    print(f"\n✅ Index optimization complete for '{args.collection}'")


if __name__ == "__main__":
    main()
