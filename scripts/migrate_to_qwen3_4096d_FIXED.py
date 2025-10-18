#!/usr/bin/env python3
"""
FIXED: Migrate Qdrant Collection to Qwen3 4096-d Embeddings
Feature: 004-migrate-qdrant-collection
Task: T009 - Batch reprocess documents with late chunking

FIXES IMPLEMENTED:
1. ✅ Deterministic UUID v5 point IDs (prevents duplicates)
2. ✅ Collection recreation (clean slate)
3. ✅ 15-minute timeout with admin pause
4. ✅ Retry logic with exponential backoff
5. ✅ Checkpoint/resume capability
6. ✅ Better error handling and logging
7. ✅ Full metadata preservation

This script processes all documents in /workspace/bms_data with:
- Qwen3-embedding:latest model (4096-dimensional vectors)
- Late chunking strategy (500 tokens, 150 overlap)
- RAGAS quality validation (threshold 50.0)
- Multi-vector embeddings (chunk, parent, child, full_doc)
"""

import sys
import json
import time
import uuid
import argparse
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Set
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import numpy as np

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
from qdrant_client.models import PointStruct, Distance, VectorParams, Filter, FieldCondition, MatchValue
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/workspace/logs/migration_4096d_FIXED.log'),
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
QUALITY_THRESHOLD = 0.5  # RAGAS minimum score (0.0-1.0 scale)

# Migration control
TIMEOUT_MINUTES = 15  # NFR-004: Pause at 15 minutes
CHECKPOINT_INTERVAL = 10  # Save checkpoint every N documents
MAX_RETRIES = 3  # Retry failed uploads
UUID_NAMESPACE = uuid.UUID('a1b2c3d4-e5f6-7890-abcd-ef1234567890')  # For deterministic UUIDs


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

    def generate_embedding(self, text: str, timeout: int = 30) -> List[float]:
        """Generate single embedding (30s timeout - GPU memory freed after chunking)"""
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


def generate_deterministic_point_id(document_id: str, chunk_idx: int) -> str:
    """
    Generate deterministic UUID v5 from document ID and chunk index.
    This ensures consistent point IDs across runs, enabling true upsert behavior.
    """
    name = f"{document_id}_chunk_{chunk_idx}"
    return str(uuid.uuid5(UUID_NAMESPACE, name))


class QdrantMigrationClient:
    """Client for upserting 4096-d embeddings to Qdrant with retry logic"""

    def __init__(self, host: str = QDRANT_HOST, port: int = QDRANT_PORT, recreate: bool = False):
        self.client = QdrantClient(host=host, port=port)
        self.collection_name = COLLECTION_NAME
        self.low_quality_collection = LOW_QUALITY_COLLECTION

        if recreate:
            self._recreate_collections()
        else:
            self._ensure_low_quality_collection()

    def _recreate_collections(self):
        """Drop and recreate collections for clean migration"""
        logger.info("⚠️  RECREATING COLLECTIONS (deleting old data)")

        # Delete existing collections
        try:
            self.client.delete_collection(collection_name=self.collection_name)
            logger.info(f"✓ Deleted old collection: {self.collection_name}")
        except:
            logger.info(f"Collection {self.collection_name} didn't exist")

        try:
            self.client.delete_collection(collection_name=self.low_quality_collection)
            logger.info(f"✓ Deleted old low-quality collection")
        except:
            pass

        # Create fresh collections
        vector_config = {
            "chunk_embedding": VectorParams(size=EXPECTED_DIMENSION, distance=Distance.COSINE),
            "parent_embedding": VectorParams(size=EXPECTED_DIMENSION, distance=Distance.COSINE),
            "child_embedding": VectorParams(size=EXPECTED_DIMENSION, distance=Distance.COSINE),
            "full_doc_embedding": VectorParams(size=EXPECTED_DIMENSION, distance=Distance.COSINE),
        }

        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=vector_config
        )
        logger.info(f"✓ Created new collection: {self.collection_name}")

        self.client.create_collection(
            collection_name=self.low_quality_collection,
            vectors_config=vector_config
        )
        logger.info(f"✓ Created new low-quality collection")

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

    def upsert_chunk_with_retry(
        self,
        point_id: str,
        chunk_text: str,
        chunk_embedding: List[float],
        parent_embedding: List[float],
        child_embedding: List[float],
        full_doc_embedding: List[float],
        metadata: Dict[str, Any],
        quality_score: float,
        max_retries: int = MAX_RETRIES
    ) -> Optional[str]:
        """Upsert single chunk with retry logic and exponential backoff"""

        # Determine target collection based on quality
        target_collection = (
            self.low_quality_collection
            if quality_score < QUALITY_THRESHOLD
            else self.collection_name
        )

        point = PointStruct(
            id=point_id,  # Now using deterministic UUID
            vector={
                "chunk_embedding": chunk_embedding,
                "parent_embedding": parent_embedding,
                "child_embedding": child_embedding,
                "full_doc_embedding": full_doc_embedding,
            },
            payload={
                **metadata,  # Unpack all metadata
                "text": chunk_text,
                "quality_score": quality_score
            }
        )

        # Retry logic with exponential backoff
        for attempt in range(max_retries):
            try:
                self.client.upsert(
                    collection_name=target_collection,
                    points=[point]
                )
                return target_collection

            except Exception as e:
                error_str = str(e)
                if "Corruption" in error_str or "Connection refused" in error_str:
                    logger.warning(f"⚠️  Retry {attempt+1}/{max_retries} for point {point_id}: {e}")
                    if attempt < max_retries - 1:
                        sleep_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                        time.sleep(sleep_time)
                    else:
                        logger.error(f"❌ Failed after {max_retries} retries: {point_id}")
                        return None
                else:
                    logger.error(f"❌ Unrecoverable error for {point_id}: {e}")
                    raise

        return None


class MigrationProcessor:
    """Main migration processor with timeout and checkpoint support"""

    def __init__(
        self,
        batch_size: int = 16,
        max_workers: int = 4,
        recreate_collection: bool = False,
        checkpoint_path: str = "/workspace/logs/migration_checkpoint.json"
    ):
        self.batch_size = batch_size
        self.max_workers = max_workers
        self.checkpoint_path = checkpoint_path

        # Initialize components
        self.embedding_generator = OllamaEmbeddingGenerator()
        self.qdrant_client = QdrantMigrationClient(recreate=recreate_collection)

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

        # FIX: Disable processor's Qdrant storage - migration script handles storage with 4096-d embeddings
        if hasattr(self.processor, 'qdrant_client'):
            self.processor.qdrant_client = None

        # Statistics
        self.stats = {
            "total_documents": 0,
            "processed_documents": 0,
            "failed_documents": 0,
            "total_chunks": 0,
            "high_quality_chunks": 0,
            "low_quality_chunks": 0,
            "failed_uploads": 0,
            "start_time": datetime.now(),
            "processing_times": []
        }

        # Processed files tracking (for checkpoint/resume)
        self.processed_files: Set[str] = self.load_checkpoint()

    def load_checkpoint(self) -> Set[str]:
        """Load checkpoint and return set of processed files"""
        if not Path(self.checkpoint_path).exists():
            logger.info("No checkpoint found, starting fresh migration")
            return set()

        try:
            with open(self.checkpoint_path) as f:
                checkpoint = json.load(f)

            self.stats = checkpoint.get("stats", self.stats)
            processed_files = set(checkpoint.get("processed_files", []))

            logger.info(f"✓ Loaded checkpoint: {len(processed_files)} files already processed")
            return processed_files

        except Exception as e:
            logger.warning(f"Failed to load checkpoint: {e}, starting fresh")
            return set()

    def save_checkpoint(self):
        """Save current progress for resume capability"""
        try:
            checkpoint = {
                "timestamp": datetime.now().isoformat(),
                "processed_documents": self.stats["processed_documents"],
                "processed_files": list(self.processed_files),
                "stats": self.stats
            }

            with open(self.checkpoint_path, "w") as f:
                json.dump(checkpoint, f, indent=2)

            logger.info(f"✓ Checkpoint saved: {len(self.processed_files)} files")

        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")

    def process_document(self, file_path: Path) -> Dict[str, Any]:
        """Process single document and upload to Qdrant"""
        start_time = time.time()
        document_id = file_path.stem

        try:
            logger.info(f"Processing: {file_path.name}")

            # Extract and chunk document (using Enhanced Document Processor)
            result = self.processor.process_document(str(file_path))

            # FIX: Enhanced Document Processor returns 'processing_success', not 'success'
            if not result.get("processing_success"):
                errors = result.get("errors", [])
                error_msg = errors[0] if errors else "Unknown processing error"
                raise Exception(error_msg)

            chunks = result.get("chunks", [])
            if not chunks:
                raise Exception("No chunks generated")

            logger.info(f"  Generated {len(chunks)} chunks")

            # SOLUTION: Use processor's Qwen3 model directly (eliminates GPU contention!)
            if not hasattr(self.processor, 'embedding_model') or self.processor.embedding_model is None:
                raise Exception("Processor's Qwen3 embedding model not available")

            # Process each chunk
            high_quality_count = 0
            low_quality_count = 0
            failed_upload_count = 0

            for idx, chunk_data in enumerate(chunks):
                # FIX: Processor returns "content" key, not "text"
                chunk_text = chunk_data.get("content", chunk_data.get("text", ""))
                quality_score = chunk_data.get("quality", {}).get("overall_score", 0.0)

                # Generate 4096-d embeddings using processor's Qwen3 model (NO GPU CONTENTION!)
                try:
                    import torch

                    # Main chunk embedding
                    chunk_embedding_tensor = self.processor.embedding_model.encode(
                        chunk_text,
                        convert_to_tensor=True,
                        device='cuda:0' if torch.cuda.is_available() else 'cpu',
                        show_progress_bar=False
                    )
                    chunk_embedding = chunk_embedding_tensor.cpu().detach().numpy().tolist()

                    # Verify dimension
                    if len(chunk_embedding) != EXPECTED_DIMENSION:
                        raise Exception(
                            f"Expected {EXPECTED_DIMENSION}-d embedding, got {len(chunk_embedding)}-d"
                        )

                    # Parent/child/full_doc embeddings
                    parent_text = chunk_data.get("parent_text", chunk_text)
                    child_text = chunk_data.get("child_text", chunk_text)
                    full_doc_text = " ".join([c.get("content", c.get("text", "")) for c in chunks])[:8000]

                    parent_embedding_tensor = self.processor.embedding_model.encode(
                        parent_text, convert_to_tensor=True,
                        device='cuda:0' if torch.cuda.is_available() else 'cpu',
                        show_progress_bar=False
                    )
                    parent_embedding = parent_embedding_tensor.cpu().detach().numpy().tolist()

                    child_embedding_tensor = self.processor.embedding_model.encode(
                        child_text, convert_to_tensor=True,
                        device='cuda:0' if torch.cuda.is_available() else 'cpu',
                        show_progress_bar=False
                    )
                    child_embedding = child_embedding_tensor.cpu().detach().numpy().tolist()

                    full_doc_embedding_tensor = self.processor.embedding_model.encode(
                        full_doc_text, convert_to_tensor=True,
                        device='cuda:0' if torch.cuda.is_available() else 'cpu',
                        show_progress_bar=False
                    )
                    full_doc_embedding = full_doc_embedding_tensor.cpu().detach().numpy().tolist()

                except Exception as e:
                    logger.error(f"    ❌ Failed to generate embeddings for chunk {idx}: {e}")
                    failed_upload_count += 1
                    continue

                # FULL Metadata (preserve ALL processor output, excluding tensors/embeddings)
                # FIX: Filter out torch.Tensor objects and embeddings (we generate our own 4096-d embeddings)
                filtered_chunk_data = {}
                for k, v in chunk_data.items():
                    if k in ["text", "content", "quality", "parent_text", "child_text"]:
                        continue  # Skip these keys (handled separately)
                    # Skip embedding fields (we generate our own)
                    if "embedding" in k.lower() or "vector" in k.lower():
                        continue
                    # Convert torch.Tensor to list
                    if hasattr(v, '__class__') and 'torch' in str(v.__class__):
                        continue  # Skip torch tensors entirely
                    filtered_chunk_data[k] = v

                metadata = {
                    "file_name": file_path.name,
                    "document_id": document_id,
                    "chunk_key": idx,
                    "chunk_index": idx,
                    "hierarchy": chunk_data.get("hierarchy", "chunk"),
                    "has_context": chunk_data.get("has_context", False),
                    "processing_profile": "RAILWAY",
                    "chunking_strategy": "LATE_CHUNKING",
                    "processing_version": "v5.0_qwen3_4096d",
                    "processing_timestamp": datetime.now().isoformat(),
                    "late_chunking_applied": True,
                    # Add filtered metadata from chunk_data
                    **filtered_chunk_data
                }

                # Generate deterministic point ID
                point_id = generate_deterministic_point_id(document_id, idx)

                # Upsert to Qdrant with retry
                target_collection = self.qdrant_client.upsert_chunk_with_retry(
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
                elif target_collection == LOW_QUALITY_COLLECTION:
                    low_quality_count += 1
                else:
                    failed_upload_count += 1

            processing_time = time.time() - start_time
            logger.info(f"  ✓ Completed in {processing_time:.2f}s: {high_quality_count} high-quality, {low_quality_count} low-quality, {failed_upload_count} failed uploads")

            return {
                "success": True,
                "file_name": file_path.name,
                "chunks": len(chunks),
                "high_quality": high_quality_count,
                "low_quality": low_quality_count,
                "failed_uploads": failed_upload_count,
                "processing_time": processing_time
            }

        except Exception as e:
            logger.error(f"❌ Failed to process {file_path.name}: {e}")
            return {
                "success": False,
                "file_name": file_path.name,
                "error": str(e),
                "processing_time": time.time() - start_time
            }

    def check_timeout(self, total_documents: int) -> bool:
        """
        Check if migration has exceeded timeout threshold.
        Returns True if should continue, False if aborted.
        """
        elapsed_minutes = (datetime.now() - self.stats["start_time"]).total_seconds() / 60

        if elapsed_minutes > TIMEOUT_MINUTES:
            logger.warning("=" * 60)
            logger.warning(f"⏰ ALERT: Processing time exceeded {TIMEOUT_MINUTES}:00")
            logger.warning(f"Elapsed time: {elapsed_minutes:.1f} minutes")
            logger.warning(f"Progress: {self.stats['processed_documents']}/{total_documents} documents")
            logger.warning(f"Chunks created: {self.stats['total_chunks']}")
            logger.warning(f"Success rate: {self.stats['processed_documents'] / max(self.stats['total_documents'], 1) * 100:.1f}%")
            logger.warning("=" * 60)

            # Prompt for admin decision (Session 2025-10-18 requirement)
            decision = input("\n🔔 Decision required: [c] Continue  [a] Abort migration: ").strip().lower()

            if decision == 'a':
                logger.info("🛑 Migration aborted by admin decision")
                self.save_checkpoint()  # Save progress before exit
                return False
            else:
                logger.info("▶️  Continuing migration by admin decision")
                return True

        return True  # Continue normally

    def process_batch_with_timeout(self, file_paths: List[Path]):
        """Process multiple documents with timeout checking"""
        total_documents = len(file_paths)
        logger.info(f"Starting batch processing: {total_documents} documents")

        for file_path in file_paths:
            # Skip if already processed (from checkpoint)
            if str(file_path) in self.processed_files:
                logger.info(f"⏭️  Skipping (already processed): {file_path.name}")
                continue

            # Check timeout BEFORE processing next document
            if not self.check_timeout(total_documents):
                logger.info("Migration paused/aborted by admin")
                break

            # Process document
            result = self.process_document(file_path)

            # Update statistics
            self.stats["total_documents"] += 1
            if result["success"]:
                self.stats["processed_documents"] += 1
                self.stats["total_chunks"] += result["chunks"]
                self.stats["high_quality_chunks"] += result.get("high_quality", 0)
                self.stats["low_quality_chunks"] += result.get("low_quality", 0)
                self.stats["failed_uploads"] += result.get("failed_uploads", 0)
                self.processed_files.add(str(file_path))
            else:
                self.stats["failed_documents"] += 1

            self.stats["processing_times"].append(result["processing_time"])

            # Save checkpoint every N documents
            if self.stats["total_documents"] % CHECKPOINT_INTERVAL == 0:
                self.save_checkpoint()
                self.print_progress()

        # Final checkpoint
        self.save_checkpoint()

    def print_progress(self):
        """Print current progress"""
        elapsed = (datetime.now() - self.stats["start_time"]).total_seconds()
        avg_time = np.mean(self.stats["processing_times"]) if self.stats["processing_times"] else 0

        logger.info(f"""
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        Progress: {self.stats['processed_documents']}/{self.stats['total_documents']} documents
        Chunks: {self.stats['total_chunks']} total ({self.stats['high_quality_chunks']} high-quality, {self.stats['low_quality_chunks']} low-quality)
        Failed: {self.stats['failed_documents']} documents, {self.stats['failed_uploads']} uploads
        Elapsed: {elapsed:.1f}s ({elapsed/60:.1f} min) | Avg: {avg_time:.2f}s/doc
        Rate: {self.stats['processed_documents'] / max(elapsed, 1):.2f} docs/sec
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        """)

    def generate_report(self) -> Dict[str, Any]:
        """Generate final migration report"""
        elapsed = (datetime.now() - self.stats["start_time"]).total_seconds()

        return {
            "migration_id": "qwen3-4096d-fixed",
            "migration_timestamp": datetime.now().isoformat(),
            "total_documents": self.stats["total_documents"],
            "processed_documents": self.stats["processed_documents"],
            "failed_documents": self.stats["failed_documents"],
            "total_chunks": self.stats["total_chunks"],
            "high_quality_chunks": self.stats["high_quality_chunks"],
            "low_quality_chunks": self.stats["low_quality_chunks"],
            "failed_uploads": self.stats["failed_uploads"],
            "elapsed_seconds": elapsed,
            "elapsed_minutes": elapsed / 60,
            "avg_time_per_doc": np.mean(self.stats["processing_times"]) if self.stats["processing_times"] else 0,
            "quality_rate": self.stats["high_quality_chunks"] / self.stats["total_chunks"] if self.stats["total_chunks"] > 0 else 0,
            "success_rate": self.stats["processed_documents"] / max(self.stats["total_documents"], 1) * 100,
            "upload_success_rate": (self.stats["total_chunks"] - self.stats["failed_uploads"]) / max(self.stats["total_chunks"], 1) * 100,
            "fixes_applied": [
                "Deterministic UUID v5 point IDs",
                "Collection recreation (clean slate)",
                "15-minute timeout with admin pause",
                "Retry logic with exponential backoff",
                "Checkpoint/resume capability",
                "Full metadata preservation"
            ]
        }


def main():
    parser = argparse.ArgumentParser(
        description="FIXED: Migrate Qdrant collection to Qwen3 4096-d embeddings",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full migration with collection recreation
  python migrate_to_qwen3_4096d_FIXED.py --recreate

  # Test with 10 documents
  python migrate_to_qwen3_4096d_FIXED.py --limit 10 --recreate

  # Resume from checkpoint (without recreating collection)
  python migrate_to_qwen3_4096d_FIXED.py
        """
    )
    parser.add_argument("--data-dir", type=str, default="/workspace/bms_data", help="Data directory")
    parser.add_argument("--batch-size", type=int, default=16, help="Batch size for processing")
    parser.add_argument("--max-workers", type=int, default=4, help="Max parallel workers")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of documents (for testing)")
    parser.add_argument("--recreate", action="store_true", help="Recreate collection (deletes old data)")
    parser.add_argument("--checkpoint-path", type=str, default="/workspace/logs/migration_checkpoint.json", help="Checkpoint file path")
    parser.add_argument("--report-path", type=str, default="/workspace/logs/migration_report_4096d_FIXED.json", help="Output report path")
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("FIXED MIGRATION SCRIPT - Qwen3 4096-d Embeddings")
    logger.info("=" * 60)

    if args.recreate:
        logger.warning("⚠️  RECREATE MODE: Will delete existing collection data!")
        confirm = input("Type 'YES' to confirm: ").strip()
        if confirm != 'YES':
            logger.info("Migration cancelled")
            return 1

    # Find all documents
    data_dir = Path(args.data_dir)
    file_patterns = ["*.pdf", "*.docx", "*.xlsx"]
    all_files = []

    for pattern in file_patterns:
        all_files.extend(data_dir.rglob(pattern))

    # Sort for consistent ordering
    all_files = sorted(all_files)

    if args.limit:
        all_files = all_files[:args.limit]

    logger.info(f"Found {len(all_files)} documents to process")

    if not all_files:
        logger.error("No documents found!")
        return 1

    # Initialize processor
    processor = MigrationProcessor(
        batch_size=args.batch_size,
        max_workers=args.max_workers,
        recreate_collection=args.recreate,
        checkpoint_path=args.checkpoint_path
    )

    # Process all documents
    processor.process_batch_with_timeout(all_files)

    # Final progress
    processor.print_progress()

    # Generate report
    report = processor.generate_report()

    with open(args.report_path, "w") as f:
        json.dump(report, f, indent=2)

    logger.info("=" * 60)
    logger.info(f"✅ MIGRATION COMPLETE!")
    logger.info(f"Report: {args.report_path}")
    logger.info(f"Processed: {report['processed_documents']}/{report['total_documents']} ({report['success_rate']:.1f}%)")
    logger.info(f"Chunks: {report['total_chunks']} ({report['high_quality_chunks']} high-quality)")
    logger.info(f"Quality rate: {report['quality_rate']:.1%}")
    logger.info(f"Upload success: {report['upload_success_rate']:.1f}%")
    logger.info(f"Time: {report['elapsed_minutes']:.1f} minutes")
    logger.info("=" * 60)

    # Return 0 if success, 1 if any failures
    return 0 if report["failed_documents"] == 0 and report["failed_uploads"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
