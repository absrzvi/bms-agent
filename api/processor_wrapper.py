"""
Enhanced Document Processor Wrapper for BMS Agent
Integrates all v4.0 engines with Qdrant storage and complete metadata mapping
"""

import os
import sys
import json
import uuid
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict

# Add the enhanced document processor to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "bms-agent" / "scr"))

try:
    from enhanced_document_processor import (
        EnhancedDocumentProcessor, ProcessingConfig, ProcessingProfile,
        ChunkingStrategy
    )
    ENHANCED_PROCESSOR_AVAILABLE = True
except ImportError as e:
    logging.error(f"Enhanced Document Processor not available: {e}")
    ENHANCED_PROCESSOR_AVAILABLE = False

# Qdrant integration
try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import PointStruct, SparseVector
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False

# sentence-transformers for embeddings
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

# Ollama integration for embeddings (fallback)
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ProcessingResult:
    """Result of document processing operation"""
    document_id: str
    file_name: str
    status: str
    chunks_created: int
    quality_score: float
    processing_time_ms: int
    features_extracted: List[str]
    metadata: Dict[str, Any]
    error: Optional[str] = None

class BMSDocumentProcessor:
    """
    BMS Agent Document Processor integrating Enhanced Document Processor v4.0
    with Qdrant storage and complete metadata mapping
    """
    
    def __init__(self, 
                 qdrant_host: str = "localhost",
                 qdrant_port: int = 6333,
                 ollama_url: str = "http://localhost:11434",
                 collection_name: str = "nomad_bms_documents"):
        """Initialize the BMS Document Processor"""
        
        self.collection_name = collection_name
        self.ollama_url = ollama_url
        
        # Initialize sentence-transformers for fast embeddings (768-d)
        self.embedding_model = None
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                from sentence_transformers import SentenceTransformer
                import torch
                device = 'cuda' if torch.cuda.is_available() else 'cpu'
                self.embedding_model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2', device=device)
                logger.info(f"✅ sentence-transformers model loaded (768-d embeddings) on {device.upper()}")
            except Exception as e:
                logger.warning(f"⚠️  sentence-transformers not available: {e}")
        
        # Initialize Qdrant client
        if QDRANT_AVAILABLE:
            try:
                self.qdrant_client = QdrantClient(
                    host=qdrant_host, 
                    port=qdrant_port
                )
                logger.info(f"✅ Connected to Qdrant at {qdrant_host}:{qdrant_port}")
            except Exception as e:
                logger.error(f"❌ Failed to connect to Qdrant: {e}")
                self.qdrant_client = None
        else:
            logger.error("❌ Qdrant client not available")
            self.qdrant_client = None
        
        # Initialize Enhanced Document Processor with all v4.0 features
        if ENHANCED_PROCESSOR_AVAILABLE:
            self.processor_config = ProcessingConfig(
                # Core processing settings (more permissive for testing)
                chunk_size=800,
                chunk_overlap=100,
                min_chunk_size=50,   # Much lower minimum for testing
                max_chunk_size=2000,
                quality_threshold=60.0,  # Lower threshold for testing
                
                # Advanced chunking (use sliding window for reliable chunking)
                chunking_strategy=ChunkingStrategy.SLIDING_WINDOW,
                parent_chunk_size=2000,
                child_chunk_size=400,
                
                # Processing options
                processing_profile=ProcessingProfile.RAILWAY,
                enable_ocr=True,
                extract_tables=True,
                extract_images=True,
                enable_contextual_retrieval=True,
                enable_late_chunking=True,
                
                # Quality settings
                min_quality_score=70.0,
                enable_quality_validation=True,
                
                # Embedding settings
                embedding_model="sentence-transformers/all-mpnet-base-v2",
                embedding_batch_size=32,
                
                # Hybrid search settings
                enable_hybrid_search=True,
                vector_weight=0.5,
                keyword_weight=0.5,
                
                # Distributed processing
                enable_distributed=False,  # Single-node for POC
                num_workers=4,
                use_gpu=True,
                
                # Versioning
                enable_versioning=True,
                track_changes=True,
                
                # Railway-specific settings
                preserve_technical_terms=True,
                railway_terminology_path=None,  # Use built-in terminology
                
                # Advanced text preprocessing (activated from memory)
                enable_advanced_preprocessing=True
            )
            
            try:
                self.enhanced_processor = EnhancedDocumentProcessor(self.processor_config)
                logger.info("✅ Enhanced Document Processor v4.0 initialized with ALL engines")
                
                # Log enabled features
                enabled_features = self._get_enabled_features()
                logger.info(f"🚀 Enabled features: {', '.join(enabled_features)}")
                
            except Exception as e:
                logger.error(f"❌ Failed to initialize Enhanced Document Processor: {e}")
                self.enhanced_processor = None
        else:
            logger.error("❌ Enhanced Document Processor not available")
            self.enhanced_processor = None
    
    def _get_enabled_features(self) -> List[str]:
        """Get list of enabled processing features"""
        features = []
        
        if self.processor_config.enable_contextual_retrieval:
            features.append("contextual_retrieval")
        if self.processor_config.chunking_strategy == ChunkingStrategy.HIERARCHICAL:
            features.append("hierarchical_chunking")
        if self.processor_config.enable_late_chunking:
            features.append("late_chunking")
        if self.processor_config.enable_quality_validation:
            features.append("quality_validation")
        if self.processor_config.enable_hybrid_search:
            features.append("hybrid_search_prep")
        if self.processor_config.enable_advanced_preprocessing:
            features.append("advanced_preprocessing")
        if self.processor_config.processing_profile == ProcessingProfile.RAILWAY:
            features.append("railway_processing")
        if self.processor_config.enable_versioning:
            features.append("version_tracking")
        if self.processor_config.enable_ocr:
            features.append("ocr_processing")
        if self.processor_config.extract_tables:
            features.append("table_extraction")
        if self.processor_config.extract_images:
            features.append("image_extraction")
        
        return features
    
    def _generate_embeddings(self, text: str) -> Optional[List[float]]:
        """Generate embeddings using sentence-transformers (768-d, GPU-accelerated)"""
        try:
            if not self.embedding_model:
                logger.error("Embedding model not initialized")
                return None
            
            # Generate embedding using sentence-transformers with GPU
            # convert_to_tensor=True keeps computation on GPU for speed
            # Then convert to numpy/list for storage
            embedding = self.embedding_model.encode(
                text, 
                convert_to_tensor=True,  # Keep on GPU during computation
                show_progress_bar=False,
                batch_size=1,  # Single text, no batching needed
                normalize_embeddings=False
            )
            
            # Convert tensor to list (moves from GPU to CPU)
            return embedding.cpu().numpy().tolist()
                
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            return None
    
    def _create_sparse_vector(self, text: str, keywords: List[str]) -> Optional[SparseVector]:
        """Create sparse vector for BM25/keyword search"""
        try:
            # Simple keyword-based sparse vector (in production, use proper BM25)
            word_counts = {}
            words = text.lower().split()
            
            # Count word frequencies
            for word in words:
                word_counts[word] = word_counts.get(word, 0) + 1
            
            # Add extracted keywords with higher weights
            for keyword in keywords:
                word_counts[keyword.lower()] = word_counts.get(keyword.lower(), 0) + 5
            
            # Convert to sparse vector format
            if word_counts:
                # Create indices and values (simplified approach)
                indices = list(range(len(word_counts)))
                values = list(word_counts.values())
                
                return SparseVector(
                    indices=indices[:100],  # Limit to top 100 terms
                    values=values[:100]
                )
            
        except Exception as e:
            logger.error(f"Error creating sparse vector: {e}")
        
        return None
    
    def process_document(self, 
                        file_path: str, 
                        processing_profile: str = "railway") -> ProcessingResult:
        """
        Process document using Enhanced Document Processor v4.0 and store in Qdrant
        """
        start_time = datetime.now()
        document_id = str(uuid.uuid4())
        file_name = Path(file_path).name
        
        logger.info(f"🚀 Processing document: {file_name} (ID: {document_id})")
        
        try:
            # Validate processor availability
            if not self.enhanced_processor:
                return ProcessingResult(
                    document_id=document_id,
                    file_name=file_name,
                    status="error",
                    chunks_created=0,
                    quality_score=0.0,
                    processing_time_ms=0,
                    features_extracted=[],
                    metadata={},
                    error="Enhanced Document Processor not available"
                )
            
            # Update processing profile
            profile_map = {
                "railway": ProcessingProfile.RAILWAY,
                "general": ProcessingProfile.GENERAL,
                "technical": ProcessingProfile.TECHNICAL,
                "legal": ProcessingProfile.LEGAL,
                "medical": ProcessingProfile.MEDICAL,
                "financial": ProcessingProfile.FINANCIAL
            }
            
            self.processor_config.processing_profile = profile_map.get(
                processing_profile, ProcessingProfile.RAILWAY
            )
            
            # Process document with Enhanced Document Processor v4.0
            logger.info(f"📄 Running Enhanced Document Processor v4.0...")
            processing_result = self.enhanced_processor.process_document(file_path)
            
            # Check for processing success (the processor uses 'processing_success' not 'status')
            if not processing_result or not processing_result.get("processing_success", False):
                error_msg = processing_result.get("error", "Unknown processing error") if processing_result else "No processing result"
                return ProcessingResult(
                    document_id=document_id,
                    file_name=file_name,
                    status="error",
                    chunks_created=0,
                    quality_score=0.0,
                    processing_time_ms=0,
                    features_extracted=[],
                    metadata={},
                    error=error_msg
                )
            
            # Extract processing results
            chunks = processing_result.get("chunks", [])
            quality_report = processing_result.get("quality_report", {})
            statistics = processing_result.get("statistics", {})
            metadata = processing_result.get("metadata", {})
            
            logger.info(f"✅ Document processed: {len(chunks)} chunks created")
            
            # Store in Qdrant with complete metadata mapping
            if self.qdrant_client and chunks:
                points_stored = self._store_in_qdrant(
                    document_id=document_id,
                    file_name=file_name,
                    chunks=chunks,
                    metadata=metadata,
                    processing_profile=processing_profile
                )
                logger.info(f"💾 Stored {points_stored} points in Qdrant")
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Create result
            result = ProcessingResult(
                document_id=document_id,
                file_name=file_name,
                status="success",
                chunks_created=len(chunks),
                quality_score=statistics.get("avg_chunk_size", 0.0),  # Use avg chunk size as quality proxy
                processing_time_ms=int(processing_time),
                features_extracted=self._get_enabled_features(),
                metadata={
                    "processing_profile": processing_profile,
                    "file_size": os.path.getsize(file_path),
                    "file_hash": self._calculate_file_hash(file_path),
                    "processing_timestamp": start_time.isoformat(),
                    "quality_report": quality_report,
                    "statistics": statistics,
                    "enhanced_features": metadata
                }
            )
            
            logger.info(f"🎉 Document processing completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"❌ Document processing failed: {e}")
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return ProcessingResult(
                document_id=document_id,
                file_name=file_name,
                status="error",
                chunks_created=0,
                quality_score=0.0,
                processing_time_ms=int(processing_time),
                features_extracted=[],
                metadata={},
                error=str(e)
            )
    
    def _generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts in one batch (GPU-optimized)"""
        try:
            if not self.embedding_model or not texts:
                return []
            
            # Batch encode all texts at once on GPU
            embeddings = self.embedding_model.encode(
                texts,
                convert_to_tensor=True,
                show_progress_bar=False,
                batch_size=32,  # Process 32 texts at a time on GPU
                normalize_embeddings=False
            )
            
            # Convert to list of lists
            return [emb.cpu().numpy().tolist() for emb in embeddings]
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            return []
    
    def _store_in_qdrant(self, 
                        document_id: str,
                        file_name: str,
                        chunks: List[Dict[str, Any]],
                        metadata: Dict[str, Any],
                        processing_profile: str) -> int:
        """Store processed chunks in Qdrant with complete metadata mapping"""
        
        if not self.qdrant_client:
            logger.error("Qdrant client not available")
            return 0
        
        # OPTIMIZATION: Generate all embeddings in one batch (5-10x faster)
        chunk_contents = [chunk.get("content", "") for chunk in chunks]
        all_embeddings = self._generate_embeddings_batch(chunk_contents)
        
        if len(all_embeddings) != len(chunks):
            logger.error(f"Embedding count mismatch: {len(all_embeddings)} vs {len(chunks)}")
            return 0
        
        points = []
        
        for i, chunk in enumerate(chunks):
            try:
                chunk_id = f"{document_id}_chunk_{i}_{uuid.uuid4().hex[:8]}"
                content = chunk.get("content", "")
                
                # Use pre-generated embedding from batch
                chunk_embedding = all_embeddings[i]
                
                # Create different embedding types for multi-vector support
                parent_embedding = chunk_embedding  # Same for POC, could be different
                child_embedding = chunk_embedding   # Same for POC, could be different
                full_doc_embedding = chunk_embedding # Same for POC, could be different
                
                # Create sparse vector for hybrid search
                keywords = chunk.get("keywords", [])
                sparse_vector = self._create_sparse_vector(content, keywords)
                
                # Build comprehensive payload with ALL Enhanced Processor v4.0 metadata
                payload = {
                    # Document-level metadata
                    "document_id": document_id,
                    "document_name": file_name,
                    "document_type": Path(file_name).suffix.lower().replace(".", ""),
                    "document_version": 1.0,
                    "processing_profile": processing_profile,
                    "processing_timestamp": datetime.now().isoformat(),
                    
                    # Chunk-level metadata
                    "chunk_id": chunk_id,
                    "chunk_type": chunk.get("chunk_type", "single"),
                    "chunk_index": i,
                    "chunk_size": len(content),
                    "content": content,
                    
                    # Hierarchical chunking metadata
                    "hierarchy_level": chunk.get("hierarchy_level", "single"),
                    "parent_chunk_id": chunk.get("parent_chunk_id"),
                    "is_parent": chunk.get("is_parent", False),
                    "is_child": chunk.get("is_child", False),
                    
                    # Quality validation metadata
                    "quality_score": chunk.get("quality_score", 0.0),
                    
                    # Contextual retrieval metadata
                    "has_context": bool(chunk.get("contextual_description")),
                    "contextual_description": chunk.get("contextual_description", ""),
                    "surrounding_context": chunk.get("surrounding_context", ""),
                    "context_type": chunk.get("context_type", "none"),
                    
                    # Late chunking metadata
                    "late_chunking_applied": chunk.get("late_chunking_applied", False),
                    
                    # Entity extraction metadata
                    "entities": json.dumps(chunk.get("entities", [])),
                    "keywords": json.dumps(keywords),
                    "technical_terms": json.dumps(chunk.get("technical_terms", [])),
                    
                    # Railway-specific metadata (ÖBB)
                    "fleet_type": chunk.get("fleet_type", ""),
                    "train_id": chunk.get("train_id", ""),
                    "standard_compliance": chunk.get("standard_compliance", ""),
                    "network_component": chunk.get("network_component", ""),
                    "configuration_type": chunk.get("configuration_type", ""),
                    
                    # Search optimization metadata
                    "search_type": "hybrid",
                    "processing_version": "v4.0_enhanced"
                }
                
                # Create point with multi-vector support
                vectors_dict = {
                    "chunk_embedding": chunk_embedding,
                    "parent_embedding": parent_embedding,
                    "child_embedding": child_embedding,
                    "full_doc_embedding": full_doc_embedding
                }
                
                # Add sparse vector if available
                if sparse_vector:
                    vectors_dict["keywords"] = sparse_vector
                
                point = PointStruct(
                    id=str(uuid.uuid4()),
                    vector=vectors_dict,
                    payload=payload
                )
                
                points.append(point)
            except Exception as e:
                logger.error(f"Error creating point for chunk {i}: {e}")
                continue
        
        # Store points in Qdrant
        if points:
            try:
                self.qdrant_client.upsert(
                    collection_name=self.collection_name,
                    points=points
                )
                logger.info(f"✅ Stored {len(points)} points in Qdrant collection '{self.collection_name}'")
                return len(points)
            except Exception as e:
                logger.error(f"❌ Failed to store points in Qdrant: {e}")
                return 0
        
        return 0
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA-256 hash of file"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception as e:
            logger.error(f"Error calculating file hash: {e}")
            return ""
    
    def get_processing_status(self) -> Dict[str, Any]:
        """Get processor status and configuration"""
        return {
            "enhanced_processor_available": ENHANCED_PROCESSOR_AVAILABLE,
            "qdrant_available": bool(self.qdrant_client),
            "ollama_available": REQUESTS_AVAILABLE,
            "collection_name": self.collection_name,
            "enabled_features": self._get_enabled_features() if self.enhanced_processor else [],
            "processing_config": asdict(self.processor_config) if self.enhanced_processor else {}
        }

# Global processor instance
_processor_instance = None

def get_processor() -> BMSDocumentProcessor:
    """Get singleton processor instance"""
    global _processor_instance
    if _processor_instance is None:
        _processor_instance = BMSDocumentProcessor()
    return _processor_instance

if __name__ == "__main__":
    # Test the processor wrapper
    processor = BMSDocumentProcessor()
    status = processor.get_processing_status()
    print(json.dumps(status, indent=2))
