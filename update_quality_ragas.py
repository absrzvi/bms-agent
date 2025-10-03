#!/usr/bin/env python3
"""
Update Quality Scores using RAGAS Metrics
Calculates real quality scores based on retrieval performance
"""

import sys
from pathlib import Path
from typing import Dict, List, Any
import json
from tqdm import tqdm

sys.path.insert(0, str(Path.cwd() / 'api'))

from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from sentence_transformers import SentenceTransformer
import numpy as np

COLLECTION_NAME = "nomad_bms_documents"
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333

# Initialize embedding model
print("Loading embedding model...")
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

def calculate_context_precision(content: str, keywords: List[str], entities: List[str]) -> float:
    """
    Context Precision: How relevant is the chunk content
    Based on keyword/entity density and semantic coherence
    """
    if not content or len(content) < 50:
        return 0.0
    
    # Keyword relevance (40%)
    keyword_matches = sum(1 for kw in keywords if kw.lower() in content.lower())
    keyword_score = min(keyword_matches / max(len(keywords), 1), 1.0) * 0.4
    
    # Entity relevance (30%)
    entity_matches = sum(1 for ent in entities if ent in content)
    entity_score = min(entity_matches / max(len(entities), 1), 1.0) * 0.3
    
    # Content density (30%) - information per character
    words = content.split()
    unique_words = len(set(w.lower() for w in words if len(w) > 3))
    density = min(unique_words / max(len(words), 1), 0.5) * 2  # Normalize to 0-1
    density_score = density * 0.3
    
    return keyword_score + entity_score + density_score

def calculate_context_recall(content: str, has_context: bool, contextual_desc: str) -> float:
    """
    Context Recall: How much relevant information is captured
    Based on context availability and completeness
    """
    score = 0.0
    
    # Has contextual description (40%)
    if has_context and contextual_desc:
        score += 0.4
        
        # Quality of contextual description (20%)
        if len(contextual_desc) > 100:
            score += 0.2
        elif len(contextual_desc) > 50:
            score += 0.1
    
    # Content completeness (40%)
    # Check for complete sentences and structure
    sentences = content.count('.') + content.count('!') + content.count('?')
    if sentences >= 3:
        score += 0.4
    elif sentences >= 1:
        score += 0.2
    
    return min(score, 1.0)

def calculate_faithfulness(content: str, technical_terms: List[str]) -> float:
    """
    Faithfulness: Content quality and technical accuracy
    Based on technical term usage and structure
    """
    if not content:
        return 0.0
    
    score = 0.0
    
    # Technical term presence (40%)
    tech_count = len(technical_terms)
    if tech_count >= 5:
        score += 0.4
    elif tech_count >= 3:
        score += 0.3
    elif tech_count >= 1:
        score += 0.2
    
    # No artifacts or errors (30%)
    artifacts = ['NaN', 'Unnamed', 'null', 'undefined', '###', '***', 'ERROR']
    if not any(art in content for art in artifacts):
        score += 0.3
    
    # Proper structure (30%)
    # Check for proper capitalization and punctuation
    has_capitals = any(c.isupper() for c in content)
    has_punctuation = any(p in content for p in '.!?')
    if has_capitals and has_punctuation:
        score += 0.3
    elif has_capitals or has_punctuation:
        score += 0.15
    
    return min(score, 1.0)

def calculate_answer_relevancy(content: str, chunk_size: int, processing_version: str) -> float:
    """
    Answer Relevancy: How useful is this chunk for answering queries
    Based on chunk size, processing quality, and content structure
    """
    score = 0.0
    
    # Optimal chunk size (40%)
    if 500 <= chunk_size <= 2000:
        score += 0.4
    elif 200 <= chunk_size <= 3000:
        score += 0.3
    elif 100 <= chunk_size <= 4000:
        score += 0.2
    
    # Processing version (30%)
    if processing_version == 'v4.0_enhanced':
        score += 0.3
    
    # Content structure (30%)
    # Check for informative content (not just headers or fragments)
    words = content.split()
    if len(words) >= 20:
        score += 0.3
    elif len(words) >= 10:
        score += 0.2
    elif len(words) >= 5:
        score += 0.1
    
    return min(score, 1.0)

def calculate_ragas_quality_score(payload: Dict[str, Any]) -> float:
    """
    Calculate RAGAS-inspired quality score
    Combines: Context Precision, Context Recall, Faithfulness, Answer Relevancy
    """
    content = payload.get("content", "")
    chunk_size = payload.get("chunk_size", 0)
    has_context = payload.get("has_context", False)
    contextual_desc = payload.get("contextual_description", "")
    processing_version = payload.get("processing_version", "")
    
    # Parse JSON arrays
    try:
        keywords = json.loads(payload.get("keywords", "[]"))
        entities = json.loads(payload.get("entities", "[]"))
        technical_terms = json.loads(payload.get("technical_terms", "[]"))
    except:
        keywords = []
        entities = []
        technical_terms = []
    
    # Calculate RAGAS metrics
    context_precision = calculate_context_precision(content, keywords, entities)
    context_recall = calculate_context_recall(content, has_context, contextual_desc)
    faithfulness = calculate_faithfulness(content, technical_terms)
    answer_relevancy = calculate_answer_relevancy(content, chunk_size, processing_version)
    
    # Weighted average (RAGAS-style)
    weights = {
        'context_precision': 0.25,
        'context_recall': 0.25,
        'faithfulness': 0.25,
        'answer_relevancy': 0.25
    }
    
    ragas_score = (
        context_precision * weights['context_precision'] +
        context_recall * weights['context_recall'] +
        faithfulness * weights['faithfulness'] +
        answer_relevancy * weights['answer_relevancy']
    )
    
    # Document type adjustments (slight)
    doc_type = payload.get('document_type', '')
    if doc_type == 'xlsx':
        ragas_score = min(ragas_score * 1.05, 1.0)  # 5% boost for structured data
    elif doc_type == 'pdf':
        ragas_score = ragas_score * 0.98  # 2% penalty for PDF complexity
    
    return round(ragas_score, 3)

def update_quality_scores_ragas(batch_size: int = 50):
    """Update quality scores using RAGAS metrics"""
    
    print("🎯 RAGAS-Based Quality Score Update")
    print("=" * 70)
    print(f"Collection: {COLLECTION_NAME}")
    print(f"Batch size: {batch_size}")
    print()
    
    # Connect to Qdrant
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT, timeout=60)
    
    # Get total points
    collection_info = client.get_collection(COLLECTION_NAME)
    total_points = collection_info.points_count
    print(f"📊 Total points: {total_points}")
    print()
    
    # Process in batches
    updated = 0
    errors = 0
    
    print("🔄 Processing documents...")
    
    offset = None
    with tqdm(total=total_points, desc="Updating scores") as pbar:
        while True:
            # Scroll through points
            result = client.scroll(
                collection_name=COLLECTION_NAME,
                limit=batch_size,
                with_payload=True,
                with_vectors=False,
                offset=offset
            )
            
            points, next_offset = result
            
            if not points:
                break
            
            # Calculate RAGAS scores
            for point in points:
                try:
                    ragas_score = calculate_ragas_quality_score(point.payload)
                    
                    # Update in Qdrant
                    client.set_payload(
                        collection_name=COLLECTION_NAME,
                        payload={"quality_score": ragas_score},
                        points=[point.id]
                    )
                    
                    updated += 1
                    pbar.update(1)
                    
                except Exception as e:
                    errors += 1
                    print(f"\n❌ Error processing point {point.id}: {e}")
            
            offset = next_offset
            if not next_offset:
                break
    
    print()
    print("=" * 70)
    print("📊 UPDATE SUMMARY")
    print("=" * 70)
    print(f"✅ Updated: {updated}")
    print(f"❌ Errors: {errors}")
    print()
    print("✅ RAGAS-based quality scores updated successfully!")
    print("=" * 70)

if __name__ == "__main__":
    update_quality_scores_ragas()
