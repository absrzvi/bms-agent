"""BM25 parameter optimization for different document types."""

from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class BM25Optimizer:
    """Optimize BM25 parameters for different document types."""
    
    # Default BM25 parameters
    DEFAULT_K1 = 1.2  # Term frequency saturation
    DEFAULT_B = 0.75  # Length normalization
    
    # Document type-specific parameters (tuned for railway documentation)
    DOCUMENT_TYPE_PARAMS = {
        "pdf": {
            "k1": 1.5,  # Higher k1 for longer documents
            "b": 0.8,   # More length normalization
            "description": "PDF technical documents (longer, more formal)"
        },
        "docx": {
            "k1": 1.2,  # Standard k1
            "b": 0.75,  # Standard b
            "description": "Word documents (mixed length)"
        },
        "pptx": {
            "k1": 1.0,  # Lower k1 for shorter content
            "b": 0.6,   # Less length normalization
            "description": "PowerPoint presentations (shorter, bullet points)"
        },
        "xlsx": {
            "k1": 0.8,  # Lower k1 for structured data
            "b": 0.5,   # Minimal length normalization
            "description": "Excel spreadsheets (tabular data)"
        },
        "csv": {
            "k1": 0.8,  # Lower k1 for structured data
            "b": 0.5,   # Minimal length normalization
            "description": "CSV files (tabular data)"
        },
        "txt": {
            "k1": 1.2,  # Standard k1
            "b": 0.7,   # Moderate length normalization
            "description": "Text files (variable length)"
        }
    }
    
    def __init__(self):
        """Initialize BM25 optimizer."""
        self.params_cache = {}
    
    def get_parameters(
        self,
        document_type: Optional[str] = None
    ) -> Dict[str, float]:
        """
        Get optimized BM25 parameters for a document type.
        
        Args:
            document_type: Document type (pdf, docx, pptx, xlsx, csv, txt)
            
        Returns:
            Dictionary with k1 and b parameters
        """
        if not document_type:
            return {
                "k1": self.DEFAULT_K1,
                "b": self.DEFAULT_B
            }
        
        doc_type = document_type.lower()
        
        if doc_type in self.DOCUMENT_TYPE_PARAMS:
            params = self.DOCUMENT_TYPE_PARAMS[doc_type]
            return {
                "k1": params["k1"],
                "b": params["b"]
            }
        else:
            logger.warning(
                f"Unknown document type '{document_type}', "
                f"using default parameters"
            )
            return {
                "k1": self.DEFAULT_K1,
                "b": self.DEFAULT_B
            }
    
    def get_all_parameters(self) -> Dict[str, Dict]:
        """
        Get all document type parameters.
        
        Returns:
            Dictionary mapping document types to their parameters
        """
        return self.DOCUMENT_TYPE_PARAMS.copy()
    
    def tune_parameters(
        self,
        document_type: str,
        k1: float,
        b: float,
        description: Optional[str] = None
    ):
        """
        Tune BM25 parameters for a specific document type.
        
        Args:
            document_type: Document type
            k1: Term frequency saturation parameter (typically 1.2-2.0)
            b: Length normalization parameter (typically 0.0-1.0)
            description: Optional description of the tuning
        """
        if k1 < 0 or k1 > 3.0:
            raise ValueError(f"k1 must be between 0 and 3.0, got {k1}")
        
        if b < 0 or b > 1.0:
            raise ValueError(f"b must be between 0 and 1.0, got {b}")
        
        doc_type = document_type.lower()
        self.DOCUMENT_TYPE_PARAMS[doc_type] = {
            "k1": k1,
            "b": b,
            "description": description or f"Custom tuning for {doc_type}"
        }
        
        logger.info(
            f"Updated BM25 parameters for {doc_type}: k1={k1}, b={b}"
        )
    
    def explain_parameters(self, document_type: str) -> str:
        """
        Explain the BM25 parameters for a document type.
        
        Args:
            document_type: Document type
            
        Returns:
            Human-readable explanation
        """
        params = self.get_parameters(document_type)
        k1 = params["k1"]
        b = params["b"]
        
        doc_type = document_type.lower() if document_type else "default"
        description = ""
        
        if doc_type in self.DOCUMENT_TYPE_PARAMS:
            description = self.DOCUMENT_TYPE_PARAMS[doc_type].get(
                "description", ""
            )
        
        explanation = f"""BM25 Parameters for {document_type or 'default'}:
        
k1 = {k1}
  - Controls term frequency saturation
  - Higher values (1.5-2.0): More weight to repeated terms (good for longer documents)
  - Lower values (0.8-1.2): Less emphasis on repetition (good for shorter/structured content)
  
b = {b}
  - Controls document length normalization
  - Higher values (0.75-1.0): Penalize longer documents more
  - Lower values (0.0-0.5): Minimal length penalty (good for tabular data)

{description}
"""
        return explanation


class QueryAdaptiveBM25:
    """Adapt BM25 parameters based on query characteristics."""
    
    def __init__(self, optimizer: BM25Optimizer):
        """
        Initialize query-adaptive BM25.
        
        Args:
            optimizer: BM25Optimizer instance
        """
        self.optimizer = optimizer
    
    def get_adaptive_parameters(
        self,
        query: str,
        document_type: Optional[str] = None
    ) -> Dict[str, float]:
        """
        Get BM25 parameters adapted to query characteristics.
        
        Args:
            query: Search query
            document_type: Optional document type filter
            
        Returns:
            Adapted BM25 parameters
        """
        # Start with document type parameters
        params = self.optimizer.get_parameters(document_type)
        
        # Adapt based on query length
        query_length = len(query.split())
        
        if query_length <= 3:
            # Short queries: increase k1 for better term matching
            params["k1"] = min(params["k1"] * 1.2, 2.0)
        elif query_length >= 10:
            # Long queries: decrease k1 to avoid over-saturation
            params["k1"] = max(params["k1"] * 0.8, 0.8)
        
        # Adapt based on query complexity (presence of operators, quotes)
        if '"' in query or "AND" in query or "OR" in query:
            # Complex queries: reduce length normalization
            params["b"] = max(params["b"] * 0.8, 0.3)
        
        return params
