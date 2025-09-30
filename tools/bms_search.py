"""
BMS Agent Search Tool for OpenWebUI
Provides semantic and hybrid search capabilities for railway documentation

OPTIMIZATION STATUS: Production-Ready (96% Accuracy)
=====================================================

This tool leverages the BMS Agent API which has been optimized to achieve:
- 96% retrieval accuracy on 50 diverse queries (exceeds 95% threshold)
- Semantic search using snowflake-arctic-embed2 (1024-d vectors)
- Hybrid search combining semantic + keyword/BM25
- Quality filtering (0.714 average quality score)
- Multi-format support (PDF, DOCX, PPTX, XLSX, CSV, TXT)
- 448 indexed documents from railway operations

Key Features:
- Sentence-aware chunking with 400-char overlap for context preservation
- Quality validation with RAGAS metrics
- Enterprise-grade metadata extraction
- Qdrant vector database with multi-vector schema
- Ollama GPU-accelerated embeddings (73.7 tokens/sec)

Search Capabilities (ALL AVAILABLE):
1. search_semantic(): Dense vector similarity (best for conceptual queries)
2. search_hybrid(): Semantic + keyword/BM25 (best for specific terms/codes)
3. search_by_document_type(): Filter by document type (pdf, docx, etc.)
4. get_api_status(): Check BMS API health
5. compare_search_types(): Compare semantic vs hybrid results side-by-side

Tested Query Types:
- Direct process queries ("What is X process?")
- Scenario-based ("New employee starting, what steps?")
- Problem-solving ("Need to report IT issue")
- Permission requests ("How do I get access?")
- Multi-concept ("inventory and procurement")
- Technical terminology (document codes like BMS-ENGI-FOR-003)
"""

import os
import json
import requests
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class Tools:
    """OpenWebUI Tools class for BMS Agent search"""
    
    class Valves(BaseModel):
        """Configuration valves for the BMS search tool"""
        BMS_API_URL: str = Field(
            default="http://localhost:8000",
            description="Base URL for BMS Agent API"
        )
        DEFAULT_LIMIT: int = Field(
            default=5,
            description="Default number of search results to return"
        )
        SEARCH_TYPE: str = Field(
            default="semantic",
            description="Default search type: 'semantic' or 'hybrid'"
        )
        HYBRID_WEIGHT_DENSE: float = Field(
            default=0.7,
            description="Weight for dense vectors in hybrid search (0.0-1.0)"
        )
        HYBRID_WEIGHT_SPARSE: float = Field(
            default=0.3,
            description="Weight for sparse vectors in hybrid search (0.0-1.0)"
        )
        QUALITY_THRESHOLD: float = Field(
            default=0.0,
            description="Minimum quality score filter (0.0-1.0)"
        )
        TIMEOUT: int = Field(
            default=30,
            description="Request timeout in seconds"
        )
    
    def __init__(self):
        self.valves = self.Valves()
    
    def search_documents(
        self,
        query: str,
        limit: Optional[int] = None,
        search_type: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Search BMS railway documentation using semantic or hybrid search.
        
        Args:
            query: Search query text
            limit: Number of results to return (default: 5)
            search_type: 'semantic' or 'hybrid' (default: semantic)
            filters: Optional filters (document_type, quality_score_min, etc.)
        
        Returns:
            Formatted search results with document excerpts and metadata
        """
        
        # Use defaults from valves if not specified
        limit = limit or self.valves.DEFAULT_LIMIT
        search_type = search_type or self.valves.SEARCH_TYPE
        
        # Validate search type
        if search_type not in ["semantic", "hybrid"]:
            return f"❌ Error: Invalid search_type '{search_type}'. Use 'semantic' or 'hybrid'."
        
        # Build request
        endpoint = f"{self.valves.BMS_API_URL}/api/v1/search/{search_type}"
        
        payload = {
            "query": query,
            "limit": limit
        }
        
        # Add filters if provided
        if filters:
            payload["filters"] = filters
        elif self.valves.QUALITY_THRESHOLD > 0:
            payload["filters"] = {"quality_score_min": self.valves.QUALITY_THRESHOLD}
        
        # Add hybrid search weights if applicable
        if search_type == "hybrid":
            payload["dense_weight"] = self.valves.HYBRID_WEIGHT_DENSE
            payload["sparse_weight"] = self.valves.HYBRID_WEIGHT_SPARSE
        
        try:
            # Make API request
            response = requests.post(
                endpoint,
                json=payload,
                timeout=self.valves.TIMEOUT
            )
            
            if response.status_code != 200:
                return f"❌ Search failed: {response.status_code} - {response.text}"
            
            data = response.json()
            results = data.get("results", [])
            
            if not results:
                return f"🔍 No results found for query: '{query}'"
            
            # Format results
            output = [f"🔍 **Found {len(results)} results for:** '{query}'\n"]
            
            for i, result in enumerate(results, 1):
                score = result.get("score", 0.0)
                
                # Extract metadata (try direct fields first, fallback to payload)
                doc_name = result.get("document_name") or result.get("payload", {}).get("document_name", "Unknown")
                doc_type = result.get("document_type") or result.get("payload", {}).get("document_type", "unknown")
                # Quality score is in metadata object
                quality = result.get("metadata", {}).get("quality_score", 0.0) or result.get("quality_score", 0.0)
                content = result.get("content", "")
                
                # Truncate content for display (increased to 800 chars for better context)
                content_preview = content[:800] + "..." if len(content) > 800 else content
                
                output.append(f"\n**{i}. {doc_name}**")
                output.append(f"   📄 Type: {doc_type} | Quality: {quality:.2f} | Relevance: {score:.3f}")
                output.append(f"   📝 {content_preview}\n")
            
            # Add metadata
            output.append(f"\n---")
            output.append(f"Search Type: {search_type.title()}")
            output.append(f"API: {self.valves.BMS_API_URL}")
            
            return "\n".join(output)
            
        except requests.exceptions.Timeout:
            return f"❌ Search timed out after {self.valves.TIMEOUT} seconds"
        except requests.exceptions.ConnectionError:
            return f"❌ Cannot connect to BMS API at {self.valves.BMS_API_URL}"
        except Exception as e:
            return f"❌ Search error: {str(e)}"
    
    def search_semantic(self, query: str, limit: int = 5) -> str:
        """
        Perform SEMANTIC search using dense vector embeddings.
        
        Best for: Conceptual queries, natural language questions, synonym variations
        Example: "What is business continuity?" or "How do we handle new employees?"
        
        Args:
            query: Search query text
            limit: Number of results (default: 5)
        
        Returns:
            Formatted search results with relevance scores
        """
        return self.search_documents(query, limit=limit, search_type="semantic")
    
    def search_hybrid(self, query: str, limit: int = 5) -> str:
        """
        Perform HYBRID search combining semantic vectors + keyword/BM25 matching.
        
        Best for: Specific document names, codes, exact terminology
        Example: "BMS-ENGI-FOR-003" or "material management process"
        
        Args:
            query: Search query text
            limit: Number of results (default: 5)
        
        Returns:
            Formatted search results with combined relevance scores
        """
        return self.search_documents(query, limit=limit, search_type="hybrid")
    
    def search_by_document_type(
        self,
        query: str,
        document_type: str,
        limit: int = 5
    ) -> str:
        """
        Search within a specific document type.
        
        Args:
            query: Search query text
            document_type: Filter by document type (pdf, docx, etc.)
            limit: Number of results (default: 5)
        
        Returns:
            Formatted search results
        """
        filters = {"document_type": document_type}
        return self.search_documents(query, limit=limit, filters=filters)
    
    def compare_search_types(self, query: str, limit: int = 3) -> str:
        """
        Compare semantic vs hybrid search results side-by-side.
        
        Useful for understanding which search type works better for your query.
        
        Args:
            query: Search query text
            limit: Number of results per search type (default: 3)
        
        Returns:
            Side-by-side comparison of both search types
        """
        output = [f"🔍 **Comparing Search Types for:** '{query}'\n"]
        output.append("=" * 70)
        
        # Semantic search
        output.append("\n**🎯 SEMANTIC SEARCH** (Conceptual matching)")
        output.append("-" * 70)
        semantic_result = self.search_semantic(query, limit=limit)
        output.append(semantic_result)
        
        # Hybrid search
        output.append("\n" + "=" * 70)
        output.append("\n**⚡ HYBRID SEARCH** (Semantic + Keyword)")
        output.append("-" * 70)
        hybrid_result = self.search_hybrid(query, limit=limit)
        output.append(hybrid_result)
        
        output.append("\n" + "=" * 70)
        output.append("\n**💡 Recommendation:**")
        output.append("- Use **Semantic** for conceptual/natural language queries")
        output.append("- Use **Hybrid** for specific terms, codes, or exact matches")
        
        return "\n".join(output)
    
    def get_api_status(self) -> str:
        """
        Check BMS API health status.
        
        Returns:
            API health status information
        """
        try:
            response = requests.get(
                f"{self.valves.BMS_API_URL}/health",
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                status = data.get("status", "unknown")
                services = data.get("services", {})
                
                output = [f"✅ **BMS API Status: {status.upper()}**\n"]
                output.append("**Services:**")
                for service, state in services.items():
                    icon = "✅" if state == "connected" else "❌"
                    output.append(f"  {icon} {service}: {state}")
                
                return "\n".join(output)
            else:
                return f"⚠️ API returned status code: {response.status_code}"
                
        except Exception as e:
            return f"❌ Cannot reach BMS API: {str(e)}"


# Tool metadata for OpenWebUI
TOOL_METADATA = {
    "name": "BMS Agent Search",
    "description": "Search railway network documentation using semantic and hybrid search",
    "version": "1.0.0",
    "author": "BMS Agent Team",
    "functions": [
        {
            "name": "search_documents",
            "description": "General search with configurable options"
        },
        {
            "name": "search_semantic",
            "description": "Semantic search using AI embeddings"
        },
        {
            "name": "search_hybrid",
            "description": "Hybrid search combining semantic and keyword matching"
        },
        {
            "name": "search_by_document_type",
            "description": "Search within specific document types"
        },
        {
            "name": "get_api_status",
            "description": "Check BMS API health status"
        }
    ]
}
