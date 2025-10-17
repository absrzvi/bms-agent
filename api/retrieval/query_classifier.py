"""Query classification for domain-specific query handling."""

from enum import Enum
from typing import Dict, List
import re


class QueryType(str, Enum):
    """Query type classifications."""
    TECHNICAL = "technical"
    PROCEDURAL = "procedural"
    SAFETY = "safety"
    GENERAL = "general"


class QueryClassifier:
    """Classify queries into domain-specific categories."""
    
    # Technical keywords
    TECHNICAL_KEYWORDS = {
        "voltage", "current", "power", "circuit", "signal", "frequency",
        "traction", "braking", "hvac", "cooling", "heating", "ventilation",
        "motor", "inverter", "transformer", "converter", "battery",
        "sensor", "actuator", "relay", "contactor", "switch",
        "diagnostic", "fault", "error", "alarm", "warning",
        "specification", "parameter", "tolerance", "rating",
        "r4600", "cityjet", "talent3", "flirt", "stadler", "siemens"
    }
    
    # Procedural keywords
    PROCEDURAL_KEYWORDS = {
        "procedure", "process", "step", "instruction", "guide", "manual",
        "how to", "maintenance", "repair", "installation", "commissioning",
        "testing", "inspection", "calibration", "adjustment",
        "checklist", "workflow", "sequence", "order", "install", "replace",
        "remove", "assemble", "disassemble", "configure", "setup"
    }
    
    # Safety keywords
    SAFETY_KEYWORDS = {
        "safety", "hazard", "risk", "danger", "warning", "caution",
        "emergency", "accident", "incident", "injury",
        "protection", "guard", "interlock", "lockout",
        "en50155", "en45545", "tsi", "standard", "regulation", "compliance",
        "fire", "smoke", "toxic", "flammable", "explosive"
    }
    
    def classify(self, query: str) -> QueryType:
        """
        Classify a query into a domain-specific category.
        
        Args:
            query: The search query
            
        Returns:
            QueryType classification
        """
        query_lower = query.lower()
        
        # Count keyword matches for each category
        scores = {
            QueryType.TECHNICAL: self._count_matches(query_lower, self.TECHNICAL_KEYWORDS),
            QueryType.PROCEDURAL: self._count_matches(query_lower, self.PROCEDURAL_KEYWORDS),
            QueryType.SAFETY: self._count_matches(query_lower, self.SAFETY_KEYWORDS),
        }
        
        # Safety takes priority if any safety keywords present
        if scores[QueryType.SAFETY] > 0:
            return QueryType.SAFETY
        
        # Return category with highest score, or GENERAL if all zero
        max_score = max(scores.values())
        if max_score == 0:
            return QueryType.GENERAL
        
        return max(scores.items(), key=lambda x: x[1])[0]
    
    def _count_matches(self, query: str, keywords: set) -> int:
        """Count how many keywords from the set appear in the query."""
        count = 0
        for keyword in keywords:
            if keyword in query:
                count += 1
        return count
    
    def extract_entities(self, query: str) -> Dict[str, List[str]]:
        """
        Extract domain-specific entities from the query.
        
        Args:
            query: The search query
            
        Returns:
            Dictionary of entity types and their values
        """
        entities = {
            "train_ids": [],
            "components": [],
            "standards": []
        }
        
        # Extract train IDs (e.g., R4600, Cityjet, Talent3)
        train_patterns = [
            r'\bR\d{4}\b',  # R4600
            r'\b(Cityjet|FLIRT|Talent\d?|Stadler|Siemens)\b'
        ]
        for pattern in train_patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            entities["train_ids"].extend(matches)
        
        # Extract component types
        component_keywords = [
            "traction", "braking", "hvac", "cooling", "heating",
            "motor", "inverter", "transformer", "converter", "battery",
            "door", "window", "seat", "lighting", "pantograph"
        ]
        query_lower = query.lower()
        for component in component_keywords:
            if component in query_lower:
                entities["components"].append(component)
        
        # Extract standards (e.g., EN50155, EN45545, TSI)
        standard_patterns = [
            r'\bEN\s?\d{5}\b',  # EN50155, EN 50155
            r'\bTSI\b'
        ]
        for pattern in standard_patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            entities["standards"].extend(matches)
        
        return entities
