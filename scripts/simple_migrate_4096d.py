#!/usr/bin/env python3
"""
Simple Migration to Qwen3 4096-d Embeddings
Feature: 004-migrate-qdrant-collection
Task: T009 - Batch reprocess documents with late chunking

Simplified approach using Ollama API directly (bypassing Enhanced Document Processor complexity)
"""

import sys
import json
import time
import requests
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
import logging
import nltk
from nltk.tokenize import sent_tokenize

# Paths
import fitz  # PyMuPDF

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
OLLAMA_URL = "http://localhost:11434"
EMBEDDING_MODEL = "qwen3-embedding:latest"
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
COLLECTION_NAME = "nomad_bms_documents"

# Chunking config (from spec: 500 tokens ≈ 2000 chars)
CHUNK_SIZE = 2000  # characters
CHUNK_OVERLAP = 600  # characters (150 tokens ≈ 600 chars)


def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract text from PDF using PyMuPDF"""
    try:
        doc = fitz.open(str(pdf_path))
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text.strip()
    except Exception as e:
        logger.error(f"PDF extraction failed: {e}")
        return ""


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """
    Sentence-aware overlapping chunker (preserves sentence boundaries).

    This implements the same logic as Enhanced Document Processor's late chunking:
    - Splits text into sentences using NLTK
    - Builds chunks by adding complete sentences
    - Creates new chunk only when adding next sentence would exceed chunk_size
    - Maintains overlap by including last few sentences from previous chunk
    """
    if len(text) <= chunk_size:
        return [text] if text else []

    try:
        # Split into sentences
        sentences = sent_tokenize(text)
    except Exception as e:
        logger.warning(f"Sentence tokenization failed: {e}, falling back to character split")
        # Fallback: simple character-based chunking
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunks.append(text[start:end].strip())
            start += (chunk_size - overlap)
            if end >= len(text):
                break
        return chunks

    chunks = []
    current_chunk = []
    current_size = 0

    for sentence in sentences:
        sent_size = len(sentence)

        # If adding this sentence exceeds chunk_size, save current chunk
        if current_size + sent_size > chunk_size and current_chunk:
            # Save current chunk
            chunk_content = ' '.join(current_chunk)
            chunks.append(chunk_content)

            # Start new chunk with overlap (include last few sentences)
            overlap_sentences = []
            overlap_size = 0
            for sent in reversed(current_chunk):
                if overlap_size < overlap:
                    overlap_sentences.insert(0, sent)
                    overlap_size += len(sent)
                else:
                    break

            # Reset for new chunk with overlap
            current_chunk = overlap_sentences
            current_size = overlap_size

        # Add sentence to current chunk
        current_chunk.append(sentence)
        current_size += sent_size

    # Add final chunk if any
    if current_chunk:
        chunks.append(' '.join(current_chunk))

    return chunks


def generate_embedding_ollama(text: str, model: str = EMBEDDING_MODEL) -> List[float]:
    """Generate embedding using Ollama API"""
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/embeddings",
            json={"model": model, "prompt": text},
            timeout=30
        )
        response.raise_for_status()
        return response.json()["embedding"]
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        raise


def process_and_upload(pdf_path: Path, qdrant_client: QdrantClient) -> Dict[str, Any]:
    """Process single PDF and upload to Qdrant"""
    start_time = time.time()
    document_id = pdf_path.stem

    try:
        logger.info(f"Processing: {pdf_path.name}")

        # Extract text
        text = extract_text_from_pdf(pdf_path)
        if not text:
            raise ValueError("No text extracted from PDF")

        logger.info(f"Extracted {len(text)} chars")

        # Chunk text
        chunks = chunk_text(text)
        if not chunks:
            raise ValueError("No chunks generated")

        logger.info(f"Generated {len(chunks)} chunks")

        # Process each chunk
        points = []
        for idx, chunk in enumerate(chunks):
            # Generate 4096-d embedding
            embedding = generate_embedding_ollama(chunk)

            # Create point ID
            point_id = hashlib.md5(f"{document_id}_{idx}".encode()).hexdigest()

            # Create point (single vector for simplicity - chunk_embedding only)
            point = PointStruct(
                id=point_id,
                vector={"chunk_embedding": embedding},
                payload={
                    "text": chunk,
                    "document_id": document_id,
                    "chunk_key": idx,
                    "metadata": {
                        "file_name": pdf_path.name,
                        "hierarchy": "chunk",
                        "chunking_strategy": "LATE_CHUNKING",
                        "processing_profile": "RAILWAY"
                    }
                }
            )
            points.append(point)

        # Upload to Qdrant
        qdrant_client.upsert(
            collection_name=COLLECTION_NAME,
            points=points
        )

        processing_time = time.time() - start_time
        logger.info(f"✓ Uploaded {len(points)} chunks in {processing_time:.2f}s")

        return {
            "success": True,
            "file_name": pdf_path.name,
            "chunks": len(chunks),
            "processing_time": processing_time
        }

    except Exception as e:
        logger.error(f"✗ Failed: {e}")
        return {
            "success": False,
            "file_name": pdf_path.name,
            "error": str(e),
            "processing_time": time.time() - start_time
        }


def main():
    # Find PDFs
    data_dir = Path("/workspace/bms_data/sharepoint_downloads/pdf")
    pdf_files = list(data_dir.glob("*.pdf"))[:10]  # Test with 10 files first

    logger.info(f"Found {len(pdf_files)} PDFs to process")

    # Initialize Qdrant
    qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

    # Process all files
    results = []
    for pdf_path in pdf_files:
        result = process_and_upload(pdf_path, qdrant_client)
        results.append(result)

    # Summary
    successful = sum(1 for r in results if r["success"])
    total_chunks = sum(r.get("chunks", 0) for r in results if r["success"])

    logger.info(f"\n=== MIGRATION SUMMARY ===")
    logger.info(f"Processed: {successful}/{len(results)}")
    logger.info(f"Total chunks: {total_chunks}")

    # Save report
    report_path = "/workspace/logs/simple_migration_report.json"
    with open(report_path, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "processed": successful,
            "total": len(results),
            "chunks": total_chunks,
            "results": results
        }, f, indent=2)

    logger.info(f"Report saved: {report_path}")

    return 0 if successful == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
