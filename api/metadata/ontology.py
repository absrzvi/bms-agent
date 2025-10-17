"""Railway domain ontology for metadata enrichment."""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class RailwayOntology:
    """Railway domain ontology for metadata enrichment."""
    
    def __init__(self, ontology_path: Optional[str] = None):
        """
        Initialize railway ontology.
        
        Args:
            ontology_path: Path to ontology JSON file
        """
        if ontology_path is None:
            # Default path
            ontology_path = Path(__file__).parent.parent.parent / "data" / "railway_ontology.json"
        
        self.ontology_path = Path(ontology_path)
        self.ontology = self._load_ontology()
    
    def _load_ontology(self) -> Dict:
        """Load ontology from JSON file."""
        try:
            with open(self.ontology_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Ontology file not found: {self.ontology_path}")
            return self._get_default_ontology()
        except json.JSONDecodeError as e:
            logger.error(f"Invalid ontology JSON: {e}")
            return self._get_default_ontology()
    
    def _get_default_ontology(self) -> Dict:
        """Get minimal default ontology."""
        return {
            "train_models": {},
            "components": {},
            "standards": {},
            "document_categories": {}
        }
    
    def get_train_model_info(self, train_id: str) -> Optional[Dict]:
        """
        Get information about a train model.
        
        Args:
            train_id: Train model identifier
            
        Returns:
            Train model information or None
        """
        train_models = self.ontology.get("train_models", {})
        
        # Direct lookup
        if train_id in train_models:
            return train_models[train_id]
        
        # Check aliases
        for model_id, info in train_models.items():
            aliases = info.get("aliases", [])
            if train_id.upper() in [a.upper() for a in aliases]:
                return info
        
        return None
    
    def get_component_info(self, component: str) -> Optional[Dict]:
        """
        Get information about a component.
        
        Args:
            component: Component name
            
        Returns:
            Component information or None
        """
        components = self.ontology.get("components", {})
        component_lower = component.lower()
        
        if component_lower in components:
            return components[component_lower]
        
        return None
    
    def get_standard_info(self, standard: str) -> Optional[Dict]:
        """
        Get information about a standard.
        
        Args:
            standard: Standard identifier (e.g., EN50155)
            
        Returns:
            Standard information or None
        """
        standards = self.ontology.get("standards", {})
        standard_upper = standard.upper().replace(" ", "")
        
        if standard_upper in standards:
            return standards[standard_upper]
        
        return None
    
    def get_related_standards(self, component: str) -> List[str]:
        """
        Get standards related to a component.
        
        Args:
            component: Component name
            
        Returns:
            List of related standard identifiers
        """
        component_info = self.get_component_info(component)
        if component_info:
            return component_info.get("related_standards", [])
        return []
    
    def is_safety_critical(self, component: str) -> bool:
        """
        Check if a component is safety-critical.
        
        Args:
            component: Component name
            
        Returns:
            True if safety-critical, False otherwise
        """
        component_info = self.get_component_info(component)
        if component_info:
            return component_info.get("safety_critical", False)
        return False
    
    def get_component_category(self, component: str) -> Optional[str]:
        """
        Get the category of a component.
        
        Args:
            component: Component name
            
        Returns:
            Component category or None
        """
        component_info = self.get_component_info(component)
        if component_info:
            return component_info.get("category")
        return None
    
    def get_component_hierarchy(self, component: str) -> Dict[str, any]:
        """
        Get the full hierarchy for a component.
        
        Args:
            component: Component name
            
        Returns:
            Dictionary with component, category, subcategories
        """
        component_info = self.get_component_info(component)
        if not component_info:
            return {}
        
        return {
            "component": component,
            "category": component_info.get("category"),
            "subcategories": component_info.get("subcategories", []),
            "related_standards": component_info.get("related_standards", []),
            "safety_critical": component_info.get("safety_critical", False)
        }
    
    def classify_document(self, text: str, filename: str = "") -> List[str]:
        """
        Classify document based on content and filename.
        
        Args:
            text: Document text content
            filename: Document filename
            
        Returns:
            List of document categories
        """
        categories = []
        doc_categories = self.ontology.get("document_categories", {})
        
        text_lower = text.lower()
        filename_lower = filename.lower()
        
        for category, info in doc_categories.items():
            keywords = info.get("keywords", [])
            
            # Check if any keywords appear in text or filename
            for keyword in keywords:
                if keyword in text_lower or keyword in filename_lower:
                    categories.append(category)
                    break
        
        return categories
    
    def get_all_train_models(self) -> List[str]:
        """Get list of all train model identifiers."""
        return list(self.ontology.get("train_models", {}).keys())
    
    def get_all_components(self) -> List[str]:
        """Get list of all component names."""
        return list(self.ontology.get("components", {}).keys())
    
    def get_all_standards(self) -> List[str]:
        """Get list of all standard identifiers."""
        return list(self.ontology.get("standards", {}).keys())
    
    def validate_metadata(self, metadata: Dict) -> Dict[str, List[str]]:
        """
        Validate metadata against ontology.
        
        Args:
            metadata: Metadata dictionary to validate
            
        Returns:
            Dictionary with validation results (warnings, errors)
        """
        warnings = []
        errors = []
        
        # Validate train_id
        if "train_id" in metadata:
            train_id = metadata["train_id"]
            if not self.get_train_model_info(train_id):
                warnings.append(f"Unknown train model: {train_id}")
        
        # Validate component_type
        if "component_type" in metadata:
            component = metadata["component_type"]
            if not self.get_component_info(component):
                warnings.append(f"Unknown component: {component}")
        
        # Validate standards
        if "standards" in metadata:
            standards = metadata["standards"]
            if isinstance(standards, list):
                for standard in standards:
                    if not self.get_standard_info(standard):
                        warnings.append(f"Unknown standard: {standard}")
        
        return {
            "warnings": warnings,
            "errors": errors,
            "valid": len(errors) == 0
        }
    
    def enrich_metadata(self, metadata: Dict) -> Dict:
        """
        Enrich metadata with ontology information.
        
        Args:
            metadata: Original metadata
            
        Returns:
            Enriched metadata
        """
        enriched = metadata.copy()
        
        # Enrich train model information
        if "train_id" in metadata:
            train_info = self.get_train_model_info(metadata["train_id"])
            if train_info:
                enriched["train_manufacturer"] = train_info.get("manufacturer")
                enriched["train_type"] = train_info.get("type")
        
        # Enrich component information
        if "component_type" in metadata:
            component_info = self.get_component_info(metadata["component_type"])
            if component_info:
                enriched["component_category"] = component_info.get("category")
                enriched["safety_critical"] = component_info.get("safety_critical", False)
                
                # Add related standards if not already present
                if "standards" not in enriched:
                    enriched["standards"] = component_info.get("related_standards", [])
        
        # Enrich standard information
        if "standards" in metadata and isinstance(metadata["standards"], list):
            standard_details = []
            for standard in metadata["standards"]:
                std_info = self.get_standard_info(standard)
                if std_info:
                    standard_details.append({
                        "id": standard,
                        "title": std_info.get("title"),
                        "category": std_info.get("category"),
                        "mandatory": std_info.get("mandatory", False)
                    })
            if standard_details:
                enriched["standard_details"] = standard_details
        
        return enriched
