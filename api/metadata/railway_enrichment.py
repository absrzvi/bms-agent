"""Railway-specific metadata enrichment."""

import re
import logging
from typing import Dict, List, Optional, Set

from api.metadata.ontology import RailwayOntology

logger = logging.getLogger(__name__)


class RailwayMetadataEnricher:
    """Enrich document metadata with railway-specific information."""
    
    # Train ID patterns
    TRAIN_ID_PATTERNS = [
        r'\bR\d{4}\b',  # R4600, R1234
        r'\b(FLIRT\d?)\b',  # FLIRT, FLIRT3
        r'\b(Cityjet)\b',
        r'\b(Talent\d?)\b',  # Talent, Talent3
        r'\b(KISS)\b',
        r'\b(Stadler)\b',
        r'\b(Siemens)\b',
        r'\b(Bombardier)\b'
    ]
    
    # Component patterns
    COMPONENT_PATTERNS = {
        "traction": r'\b(traction|motor|inverter|transformer|converter)\b',
        "braking": r'\b(brak(e|ing)|disc brake|emergency brake)\b',
        "hvac": r'\b(hvac|cooling|heating|ventilation|air conditioning)\b',
        "doors": r'\b(door|sliding door|plug door)\b',
        "pantograph": r'\b(pantograph|carbon strip)\b',
        "signaling": r'\b(signal(ing)?|etcs|atc|atp|cab signal)\b',
        "lighting": r'\b(light(ing)?|interior light|exterior light)\b',
        "battery": r'\b(battery|traction battery|auxiliary battery)\b'
    }
    
    # Standard patterns
    STANDARD_PATTERNS = [
        r'\bEN\s?\d{5}\b',  # EN50155, EN 50155
        r'\bEN\s?\d{5}-\d+\b',  # EN50155-1
        r'\bTSI\b',
        r'\bIEC\s?\d{5}\b'
    ]
    
    def __init__(self, ontology: Optional[RailwayOntology] = None):
        """
        Initialize metadata enricher.
        
        Args:
            ontology: RailwayOntology instance (creates new if None)
        """
        self.ontology = ontology or RailwayOntology()
    
    def extract_train_ids(self, text: str) -> List[str]:
        """
        Extract train IDs from text.
        
        Args:
            text: Text to extract from
            
        Returns:
            List of unique train IDs
        """
        train_ids = set()
        
        for pattern in self.TRAIN_ID_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                # Normalize
                if isinstance(match, tuple):
                    match = match[0]
                train_ids.add(match.upper())
        
        return list(train_ids)
    
    def extract_components(self, text: str) -> List[str]:
        """
        Extract component types from text.
        
        Args:
            text: Text to extract from
            
        Returns:
            List of unique component types
        """
        components = set()
        text_lower = text.lower()
        
        for component, pattern in self.COMPONENT_PATTERNS.items():
            if re.search(pattern, text_lower, re.IGNORECASE):
                components.add(component)
        
        return list(components)
    
    def extract_standards(self, text: str) -> List[str]:
        """
        Extract standard references from text.
        
        Args:
            text: Text to extract from
            
        Returns:
            List of unique standards
        """
        standards = set()
        
        for pattern in self.STANDARD_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                # Normalize (remove spaces)
                normalized = match.upper().replace(" ", "")
                standards.add(normalized)
        
        return list(standards)
    
    def enrich_document_metadata(
        self,
        text: str,
        filename: str = "",
        existing_metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Enrich document metadata with extracted railway information.
        
        Args:
            text: Document text content
            filename: Document filename
            existing_metadata: Existing metadata to enrich
            
        Returns:
            Enriched metadata dictionary
        """
        metadata = existing_metadata.copy() if existing_metadata else {}
        
        # Extract train IDs
        train_ids = self.extract_train_ids(text + " " + filename)
        if train_ids and "train_id" not in metadata:
            # Use first found train ID
            metadata["train_id"] = train_ids[0]
            if len(train_ids) > 1:
                metadata["related_train_ids"] = train_ids[1:]
        
        # Extract components
        components = self.extract_components(text + " " + filename)
        if components:
            if "component_type" not in metadata:
                # Use first found component
                metadata["component_type"] = components[0]
            if len(components) > 1:
                metadata["related_components"] = components
        
        # Extract standards
        standards = self.extract_standards(text)
        if standards:
            if "standards" not in metadata:
                metadata["standards"] = standards
            else:
                # Merge with existing
                existing_standards = metadata.get("standards", [])
                if isinstance(existing_standards, list):
                    all_standards = set(existing_standards + standards)
                    metadata["standards"] = list(all_standards)
        
        # Classify document
        doc_categories = self.ontology.classify_document(text, filename)
        if doc_categories:
            metadata["document_categories"] = doc_categories
        
        # Enrich with ontology information
        enriched_metadata = self.ontology.enrich_metadata(metadata)
        
        # Add safety flags
        if "component_type" in enriched_metadata:
            component = enriched_metadata["component_type"]
            enriched_metadata["safety_critical"] = self.ontology.is_safety_critical(component)
        
        return enriched_metadata
    
    def batch_enrich(
        self,
        documents: List[Dict]
    ) -> List[Dict]:
        """
        Batch enrich multiple documents.
        
        Args:
            documents: List of documents with 'text' and optional 'filename', 'metadata'
            
        Returns:
            List of documents with enriched metadata
        """
        enriched_documents = []
        
        for doc in documents:
            text = doc.get("text", "")
            filename = doc.get("filename", "")
            existing_metadata = doc.get("metadata", {})
            
            enriched_metadata = self.enrich_document_metadata(
                text,
                filename,
                existing_metadata
            )
            
            enriched_doc = doc.copy()
            enriched_doc["metadata"] = enriched_metadata
            enriched_documents.append(enriched_doc)
        
        return enriched_documents
    
    def get_enrichment_stats(self, documents: List[Dict]) -> Dict:
        """
        Get statistics about metadata enrichment.
        
        Args:
            documents: List of enriched documents
            
        Returns:
            Statistics dictionary
        """
        stats = {
            "total_documents": len(documents),
            "with_train_id": 0,
            "with_component": 0,
            "with_standards": 0,
            "with_categories": 0,
            "safety_critical": 0,
            "train_id_distribution": {},
            "component_distribution": {},
            "standard_distribution": {}
        }
        
        for doc in documents:
            metadata = doc.get("metadata", {})
            
            if "train_id" in metadata:
                stats["with_train_id"] += 1
                train_id = metadata["train_id"]
                stats["train_id_distribution"][train_id] = \
                    stats["train_id_distribution"].get(train_id, 0) + 1
            
            if "component_type" in metadata:
                stats["with_component"] += 1
                component = metadata["component_type"]
                stats["component_distribution"][component] = \
                    stats["component_distribution"].get(component, 0) + 1
            
            if "standards" in metadata and metadata["standards"]:
                stats["with_standards"] += 1
                for standard in metadata["standards"]:
                    stats["standard_distribution"][standard] = \
                        stats["standard_distribution"].get(standard, 0) + 1
            
            if "document_categories" in metadata and metadata["document_categories"]:
                stats["with_categories"] += 1
            
            if metadata.get("safety_critical", False):
                stats["safety_critical"] += 1
        
        return stats
