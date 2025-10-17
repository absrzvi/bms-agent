#!/usr/bin/env python3
"""
Migrate Qdrant Collection to Qwen3 4096-d Embeddings
Feature: 004-migrate-qdrant-collection
Task: T009 - Batch reprocess documents with late chunking

This script processes all documents in /workspace/bms_data with:
- Qwen3-embedding:latest model (4096-dimensional vectors)
- Late chunking strategy (500 tokens, 150 overlap)
- RAGAS quality validation (threshold 50.0)
- Multi-vector embeddings (chunk, parent, child, full_doc)
"""

import sys
import json
import time
import argparse
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "bms-agent" / "scr"))

from enhanced_document_processor import (
    EnhancedDocumentProcessor,
    ProcessingConfig,
    ProcessingProfile,
    ChunkingStrategy
)
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Distance, VectorParams
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/workspace/logs/migration_4096d.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Migration configuration
OLLAMA_URL = "http://localhost:11434"
EMBEDDING_MODEL = "qwen3-embedding:latest"
EXPECTED_DIMENSION = 4096
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
COLLECTION_NAME = "nomad_bms_documents"
LOW_QUALITY_COLLECTION = "nomad_bms_documents_low_quality"

# Chunking configuration (from spec)
CHUNK_SIZE = 500  # tokens
CHUNK_OVERLAP = 150  # tokens
QUALITY_THRESHOLD = 50.0  # RAGAS minimum score


class OllamaEmbeddingGenerator:
    """Generate embeddings using Ollama API"""

    def __init__(self, model: str = EMBEDDING_MODEL, base_url: str = OLLAMA_URL):
        self.model = model
        self.base_url = base_url
        self.api_url = f"{base_url}/api/embeddings"

        # Validate model availability
        logger.info(f"Validating embedding model: {model}")
        test_embedding = self.generate_embedding("test")
        if len(test_embedding) != EXPECTED_DIMENSION:
            raise ValueError(
                f"Model {model} produces {len(test_embedding)}-d embeddings, "
                f"expected {EXPECTED_DIMENSION}-d"
            )
        logger.info(f"✓ Model validated: {EXPECTED_DIMENSION}-d embeddings")

    def generate_embedding(self, text: str, timeout: int = 10) -> List[float]:
        """Generate single embedding"""
        try:
            response = requests.post(
                self.api_url,
                json={"model": self.model, "prompt": text},
                timeout=timeout
            )
            response.raise_for_status()
            return response.json()["embedding"]
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise

    def generate_batch(self, texts: List[str], timeout: int = 30) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        embeddings = []
        for text in texts:
            embeddings.append(self.generate_embedding(text, timeout=timeout))
        return embeddings


class QdrantMigrationClient:
    """Client for upserting 4096-d embeddings to Qdrant"""

    def __init__(self, host: str = QDRANT_HOST, port: int = QDRANT_PORT):
        self.client = QdrantClient(host=host, port=port)
        self.collection_name = COLLECTION_NAME
        self.low_quality_collection = LOW_QUALITY_COLLECTION

        # Ensure low-quality collection exists
        self._ensure_low_quality_collection()

    def _ensure_low_quality_collection(self):
        """Create low-quality collection if it doesn't exist"""
        collections = [c.name for c in self.client.get_collections().collections]

        if self.low_quality_collection not in collections:
            logger.info(f"Creating low-quality collection: {self.low_quality_collection}")
            self.client.create_collection(
                collection_name=self.low_quality_collection,
                vectors_config={
                    "chunk_embedding": VectorParams(size=EXPECTED_DIMENSION, distance=Distance.COSINE),
                    "parent_embedding": VectorParams(size=EXPECTED_DIMENSION, distance=Distance.COSINE),
                    "child_embedding": VectorParams(size=EXPECTED_DIMENSION, distance=Distance.COSINE),
                    "full_doc_embedding": VectorParams(size=EXPECTED_DIMENSION, distance=Distance.COSINE),
                }
            )

    def upsert_chunk(
        self,
        point_id: str,
        chunk_text: str,
        chunk_embedding: List[float],
        parent_embedding: List[float],
        child_embedding: List[float],
        full_doc_embedding: List[float],
        metadata: Dict[str, Any],
        quality_score: float
    ):
        """Upsert single chunk with multi-vector embeddings"""
        # Determine target collection based on quality
        target_collection = (
            self.low_quality_collection
            if quality_score < QUALITY_THRESHOLD
            else self.collection_name
        )

        point = PointStruct(
            id=point_id,
            vector={
                "chunk_embedding": chunk_embedding,
                "parent_embedding": parent_embedding,
                "child_embedding": child_embedding,
                "full_doc_embedding": full_doc_embedding,
            },
            payload={
                "text": chunk_text,
                "metadata": metadata,
                "quality": {
                    "overall_score": quality_score
                }
            }
        )

        self.client.upsert(
            collection_name=target_collection,
            points=[point]
        )

        return target_collection


class MigrationProcessor:
    """Main migration processor"""

    def __init__(self, batch_size: int = 16, max_workers: int = 4):
        self.batch_size = batch_size
        self.max_workers = max_workers

        # Initialize components
        self.embedding_generator = OllamaEmbeddingGenerator()
        self.qdrant_client = QdrantMigrationClient()

        # Initialize document processor with late chunking
        config = ProcessingConfig(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            quality_threshold=QUALITY_THRESHOLD,
            enable_quality_validation=True,
            enable_contextual_retrieval=True,
            enable_late_chunking=True,
            chunking_strategy=ChunkingStrategy.LATE_CHUNKING,
            processing_profile=ProcessingProfile.RAILWAY,
            use_gpu=True
        )
        self.processor = EnhancedDocumentProcessor(config)

        # Statistics
        self.stats = {
            "total_documents": 0,
            "processed_documents": 0,
            "failed_documents": 0,
            "total_chunks": 0,
            "high_quality_chunks": 0,
            "low_quality_chunks": 0,
            "start_time": datetime.now(),
            "processing_times": []
        }

    def process_document(self, file_path: Path) -> Dict[str, Any]:
        """Process single document and upload to Qdrant"""
        start_time = time.time()
        document_id = file_path.stem

        try:
            logger.info(f"Processing: {file_path.name}")

            # Extract and chunk document (using Enhanced Document Processor)
            # This handles PDF/DOCX/XLSX, applies late chunking, computes RAGAS scores
            result = self.processor.process_document(str(file_path))

            if not result.get("success"):
                raise Exception(result.get("error", "Unknown processing error"))

            chunks = result.get("chunks", [])
            if not chunks:
                raise Exception("No chunks generated")

            # Process each chunk
            high_quality_count = 0
            low_quality_count = 0

            for idx, chunk_data in enumerate(chunks):
                chunk_text = chunk_data.get("text", "")
                quality_score = chunk_data.get("quality", {}).get("overall_score", 0.0)

                # Generate 4096-d embeddings
                chunk_embedding = self.embedding_generator.generate_embedding(chunk_text)

                # For parent/child/full_doc, use placeholder or aggregate logic
                # (Enhanced processor should provide these, fallback to chunk_embedding)
                parent_text = chunk_data.get("parent_text", chunk_text)
                child_text = chunk_data.get("child_text", chunk_text)
                full_doc_text = " ".join([c.get("text", "") for c in chunks])

                parent_embedding = self.embedding_generator.generate_embedding(parent_text)
                child_embedding = self.embedding_generator.generate_embedding(child_text)
                full_doc_embedding = self.embedding_generator.generate_embedding(full_doc_text[:8000])  # Limit length

                # Metadata
                metadata = {
                    "file_name": file_path.name,
                    "document_id": document_id,
                    "chunk_key": idx,
                    "hierarchy": chunk_data.get("hierarchy", "chunk"),
                    "has_context": chunk_data.get("has_context", False),
                    "processing_profile": "RAILWAY",
                    "chunking_strategy": "LATE_CHUNKING"
                }

                # Upsert to Qdrant
                point_id = f"{document_id}_{idx}"
                target_collection = self.qdrant_client.upsert_chunk(
                    point_id=point_id,
                    chunk_text=chunk_text,
                    chunk_embedding=chunk_embedding,
                    parent_embedding=parent_embedding,
                    child_embedding=child_embedding,
                    full_doc_embedding=full_doc_embedding,
                    metadata=metadata,
                    quality_score=quality_score
                )

                if target_collection == COLLECTION_NAME:
                    high_quality_count += 1
                else:
                    low_quality_count += 1

            processing_time = time.time() - start_time

            return {
                "success": True,
                "file_name": file_path.name,
                "chunks": len(chunks),
                "high_quality": high_quality_count,
                "low_quality": low_quality_count,
                "processing_time": processing_time
            }

        except Exception as e:
            logger.error(f"Failed to process {file_path.name}: {e}")
            return {
                "success": False,
                "file_name": file_path.name,
                "error": str(e),
                "processing_time": time.time() - start_time
            }

    def process_batch(self, file_paths: List[Path]):
        """Process multiple documents"""
        logger.info(f"Processing batch of {len(file_paths)} documents")

        for file_path in file_paths:
            result = self.process_document(file_path)

            # Update statistics
            self.stats["total_documents"] += 1
            if result["success"]:
                self.stats["processed_documents"] += 1
                self.stats["total_chunks"] += result["chunks"]
                self.stats["high_quality_chunks"] += result.get("high_quality", 0)
                self.stats["low_quality_chunks"] += result.get("low_quality", 0)
            else:
                self.stats["failed_documents"] += 1

            self.stats["processing_times"].append(result["processing_time"])

            # Log progress every 10 documents
            if self.stats["total_documents"] % 10 == 0:
                self.print_progress()

    def print_progress(self):
        """Print current progress"""
        elapsed = (datetime.now() - self.stats["start_time"]).total_seconds()
        avg_time = np.mean(self.stats["processing_times"]) if self.stats["processing_times"] else 0

        logger.info(f"""
        Progress: {self.stats['processed_documents']}/{self.stats['total_documents']} documents
        Chunks: {self.stats['total_chunks']} total ({self.stats['high_quality_chunks']} high-quality, {self.stats['low_quality_chunks']} low-quality)
        Failed: {self.stats['failed_documents']}
        Elapsed: {elapsed:.1f}s | Avg: {avg_time:.2f}s/doc
        """)

    def generate_report(self) -> Dict[str, Any]:
        """Generate final migration report"""
        elapsed = (datetime.now() - self.stats["start_time"]).total_seconds()

        return {
            "migration_timestamp": datetime.now().isoformat(),
            "total_documents": self.stats["total_documents"],
            "processed_documents": self.stats["processed_documents"],
            "failed_documents": self.stats["failed_documents"],
            "total_chunks": self.stats["total_chunks"],
            "high_quality_chunks": self.stats["high_quality_chunks"],
            "low_quality_chunks": self.stats["low_quality_chunks"],
            "elapsed_seconds": elapsed,
            "avg_time_per_doc": np.mean(self.stats["processing_times"]) if self.stats["processing_times"] else 0,
            "quality_rate": self.stats["high_quality_chunks"] / self.stats["total_chunks"] if self.stats["total_chunks"] > 0 else 0
        }


def main():
    parser = argparse.ArgumentParser(description="Migrate Qdrant collection to Qwen3 4096-d embeddings")
    parser.add_argument("--data-dir", type=str, default="/workspace/bms_data", help="Data directory")
    parser.add_argument("--batch-size", type=int, default=16, help="Batch size for processing")
    parser.add_argument("--max-workers", type=int, default=4, help="Max parallel workers")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of documents (for testing)")
    parser.add_argument("--report-path", type=str, default="/workspace/logs/migration_report_4096d.json", help="Output report path")
    args = parser.parse_args()

    # Find all documents
    data_dir = Path(args.data_dir)
    file_patterns = ["*.pdf", "*.docx", "*.xlsx"]
    all_files = []

    for pattern in file_patterns:
        all_files.extend(data_dir.rglob(pattern))

    if args.limit:
        all_files = all_files[:args.limit]

    logger.info(f"Found {len(all_files)} documents to process")

    # Initialize processor
    processor = MigrationProcessor(
        batch_size=args.batch_size,
        max_workers=args.max_workers
    )

    # Process all documents
    processor.process_batch(all_files)

    # Generate report
    report = processor.generate_report()

    with open(args.report_path, "w") as f:
        json.dump(report, f, indent=2)

    logger.info(f"Migration complete! Report: {args.report_path}")
    logger.info(f"Processed: {report['processed_documents']}/{report['total_documents']}")
    logger.info(f"Chunks: {report['total_chunks']} ({report['high_quality_chunks']} high-quality)")
    logger.info(f"Quality rate: {report['quality_rate']:.1%}")

    return 0 if report["failed_documents"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
