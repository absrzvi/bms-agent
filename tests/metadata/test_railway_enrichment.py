"""Tests for railway metadata enrichment."""

import pytest
from api.metadata.ontology import RailwayOntology
from api.metadata.railway_enrichment import RailwayMetadataEnricher


class TestRailwayOntology:
    """Test railway ontology."""
    
    @pytest.fixture
    def ontology(self):
        """Create ontology instance."""
        return RailwayOntology()
    
    def test_load_ontology(self, ontology):
        """Test ontology loading."""
        assert ontology.ontology is not None
        assert "train_models" in ontology.ontology
        assert "components" in ontology.ontology
        assert "standards" in ontology.ontology
    
    def test_get_train_model_info(self, ontology):
        """Test getting train model information."""
        info = ontology.get_train_model_info("R4600")
        
        assert info is not None
        assert info["manufacturer"] == "Stadler"
        assert info["type"] == "EMU"
    
    def test_get_train_model_by_alias(self, ontology):
        """Test getting train model by alias."""
        info = ontology.get_train_model_info("FLIRT")
        
        assert info is not None
        assert info["manufacturer"] == "Stadler"
    
    def test_get_component_info(self, ontology):
        """Test getting component information."""
        info = ontology.get_component_info("traction")
        
        assert info is not None
        assert info["category"] == "propulsion"
        assert info["safety_critical"] is True
    
    def test_get_standard_info(self, ontology):
        """Test getting standard information."""
        info = ontology.get_standard_info("EN50155")
        
        assert info is not None
        assert "Electronic equipment" in info["title"]
        assert info["mandatory"] is True
    
    def test_get_related_standards(self, ontology):
        """Test getting related standards for a component."""
        standards = ontology.get_related_standards("traction")
        
        assert len(standards) > 0
        assert "EN50155" in standards
    
    def test_is_safety_critical(self, ontology):
        """Test safety critical check."""
        assert ontology.is_safety_critical("braking") is True
        assert ontology.is_safety_critical("lighting") is False
    
    def test_get_component_category(self, ontology):
        """Test getting component category."""
        category = ontology.get_component_category("hvac")
        assert category == "comfort"
        
        category = ontology.get_component_category("braking")
        assert category == "safety"
    
    def test_get_component_hierarchy(self, ontology):
        """Test getting component hierarchy."""
        hierarchy = ontology.get_component_hierarchy("traction")
        
        assert hierarchy["component"] == "traction"
        assert hierarchy["category"] == "propulsion"
        assert "motor" in hierarchy["subcategories"]
        assert hierarchy["safety_critical"] is True
    
    def test_classify_document(self, ontology):
        """Test document classification."""
        text = "This is a maintenance manual for the traction motor system"
        categories = ontology.classify_document(text)
        
        assert "maintenance_manual" in categories
    
    def test_get_all_train_models(self, ontology):
        """Test getting all train models."""
        models = ontology.get_all_train_models()
        
        assert "R4600" in models
        assert "Cityjet" in models
    
    def test_get_all_components(self, ontology):
        """Test getting all components."""
        components = ontology.get_all_components()
        
        assert "traction" in components
        assert "braking" in components
        assert "hvac" in components
    
    def test_get_all_standards(self, ontology):
        """Test getting all standards."""
        standards = ontology.get_all_standards()
        
        assert "EN50155" in standards
        assert "EN45545" in standards
        assert "TSI" in standards
    
    def test_validate_metadata_valid(self, ontology):
        """Test metadata validation with valid data."""
        metadata = {
            "train_id": "R4600",
            "component_type": "traction",
            "standards": ["EN50155", "TSI"]
        }
        
        result = ontology.validate_metadata(metadata)
        
        assert result["valid"] is True
        assert len(result["errors"]) == 0
    
    def test_validate_metadata_warnings(self, ontology):
        """Test metadata validation with unknown values."""
        metadata = {
            "train_id": "UNKNOWN_TRAIN",
            "component_type": "unknown_component"
        }
        
        result = ontology.validate_metadata(metadata)
        
        assert len(result["warnings"]) > 0
        assert result["valid"] is True  # Warnings don't invalidate
    
    def test_enrich_metadata(self, ontology):
        """Test metadata enrichment."""
        metadata = {
            "train_id": "R4600",
            "component_type": "traction"
        }
        
        enriched = ontology.enrich_metadata(metadata)
        
        assert "train_manufacturer" in enriched
        assert enriched["train_manufacturer"] == "Stadler"
        assert "component_category" in enriched
        assert enriched["component_category"] == "propulsion"
        assert "safety_critical" in enriched
        assert enriched["safety_critical"] is True


class TestRailwayMetadataEnricher:
    """Test railway metadata enricher."""
    
    @pytest.fixture
    def enricher(self):
        """Create enricher instance."""
        return RailwayMetadataEnricher()
    
    def test_extract_train_ids(self, enricher):
        """Test train ID extraction."""
        text = "The R4600 FLIRT train operates on the network"
        train_ids = enricher.extract_train_ids(text)
        
        assert "R4600" in train_ids
        assert "FLIRT" in train_ids
    
    def test_extract_train_ids_case_insensitive(self, enricher):
        """Test case-insensitive train ID extraction."""
        text = "The r4600 and cityjet trains"
        train_ids = enricher.extract_train_ids(text)
        
        assert "R4600" in train_ids
        assert "CITYJET" in train_ids
    
    def test_extract_components(self, enricher):
        """Test component extraction."""
        text = "The traction motor and braking system require maintenance"
        components = enricher.extract_components(text)
        
        assert "traction" in components
        assert "braking" in components
    
    def test_extract_components_hvac(self, enricher):
        """Test HVAC component extraction."""
        text = "HVAC cooling and heating system specifications"
        components = enricher.extract_components(text)
        
        assert "hvac" in components
    
    def test_extract_standards(self, enricher):
        """Test standard extraction."""
        text = "Complies with EN50155 and EN 45545 standards, TSI requirements"
        standards = enricher.extract_standards(text)
        
        assert "EN50155" in standards
        assert "EN45545" in standards
        assert "TSI" in standards
    
    def test_extract_standards_with_spaces(self, enricher):
        """Test standard extraction with spaces."""
        text = "According to EN 50155 specification"
        standards = enricher.extract_standards(text)
        
        assert "EN50155" in standards
    
    def test_enrich_document_metadata(self, enricher):
        """Test document metadata enrichment."""
        text = "R4600 traction motor maintenance manual. Complies with EN50155."
        filename = "R4600_traction_maintenance.pdf"
        
        metadata = enricher.enrich_document_metadata(text, filename)
        
        assert "train_id" in metadata
        assert metadata["train_id"] == "R4600"
        assert "component_type" in metadata
        assert metadata["component_type"] == "traction"
        assert "standards" in metadata
        assert "EN50155" in metadata["standards"]
    
    def test_enrich_with_existing_metadata(self, enricher):
        """Test enrichment with existing metadata."""
        text = "Traction motor specifications"
        existing = {"quality_score": 0.95}
        
        metadata = enricher.enrich_document_metadata(text, existing_metadata=existing)
        
        assert "quality_score" in metadata
        assert metadata["quality_score"] == 0.95
        assert "component_type" in metadata
    
    def test_enrich_safety_critical_flag(self, enricher):
        """Test safety critical flag enrichment."""
        text = "Braking system safety requirements"
        
        metadata = enricher.enrich_document_metadata(text)
        
        assert "safety_critical" in metadata
        assert metadata["safety_critical"] is True
    
    def test_enrich_non_safety_critical(self, enricher):
        """Test non-safety-critical component."""
        text = "Interior lighting specifications"
        
        metadata = enricher.enrich_document_metadata(text)
        
        if "safety_critical" in metadata:
            assert metadata["safety_critical"] is False
    
    def test_enrich_document_categories(self, enricher):
        """Test document category classification."""
        text = "Maintenance procedure for traction motor inspection and repair"
        
        metadata = enricher.enrich_document_metadata(text)
        
        assert "document_categories" in metadata
        assert "maintenance_manual" in metadata["document_categories"]
    
    def test_batch_enrich(self, enricher):
        """Test batch enrichment."""
        documents = [
            {"text": "R4600 traction specifications", "filename": "spec.pdf"},
            {"text": "Cityjet braking manual", "filename": "manual.pdf"}
        ]
        
        enriched = enricher.batch_enrich(documents)
        
        assert len(enriched) == 2
        assert "metadata" in enriched[0]
        assert "metadata" in enriched[1]
        assert enriched[0]["metadata"]["train_id"] == "R4600"
        assert enriched[1]["metadata"]["train_id"] == "CITYJET"
    
    def test_get_enrichment_stats(self, enricher):
        """Test enrichment statistics."""
        documents = [
            {
                "metadata": {
                    "train_id": "R4600",
                    "component_type": "traction",
                    "standards": ["EN50155"],
                    "safety_critical": True
                }
            },
            {
                "metadata": {
                    "train_id": "R4600",
                    "component_type": "braking",
                    "standards": ["EN14198", "TSI"]
                }
            }
        ]
        
        stats = enricher.get_enrichment_stats(documents)
        
        assert stats["total_documents"] == 2
        assert stats["with_train_id"] == 2
        assert stats["with_component"] == 2
        assert stats["with_standards"] == 2
        assert stats["train_id_distribution"]["R4600"] == 2
        assert stats["component_distribution"]["traction"] == 1
        assert stats["component_distribution"]["braking"] == 1
    
    def test_multiple_train_ids(self, enricher):
        """Test extraction of multiple train IDs."""
        text = "Comparison between R4600 and Cityjet trains"
        
        metadata = enricher.enrich_document_metadata(text)
        
        assert "train_id" in metadata
        if "related_train_ids" in metadata:
            assert len(metadata["related_train_ids"]) >= 1
    
    def test_multiple_components(self, enricher):
        """Test extraction of multiple components."""
        text = "Integration of traction, braking, and HVAC systems"
        
        metadata = enricher.enrich_document_metadata(text)
        
        assert "component_type" in metadata
        if "related_components" in metadata:
            assert len(metadata["related_components"]) >= 2
    
    def test_standard_merging(self, enricher):
        """Test merging of extracted and existing standards."""
        text = "Complies with EN50155"
        existing = {"standards": ["TSI"]}
        
        metadata = enricher.enrich_document_metadata(text, existing_metadata=existing)
        
        assert "standards" in metadata
        assert "EN50155" in metadata["standards"]
        assert "TSI" in metadata["standards"]
        assert len(metadata["standards"]) == 2
