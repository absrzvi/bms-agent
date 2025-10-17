"""
title: BMS Advanced Search
author: BMS Agent Team
author_url: https://github.com/absrzvi/bms-agent
version: 2.0.0
license: MIT
description: Advanced railway documentation search with intelligent query understanding, multi-vector retrieval, quality filtering, and context-aware results. Leverages all Qdrant metadata for optimal answers.
required_open_webui_version: 0.3.0
"""

import requests
import re
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class Tools:
    class Valves(BaseModel):
        BMS_API_URL: str = Field(
            default="http://localhost:8000",
            description="Base URL for BMS Agent API"
        )
        DEFAULT_LIMIT: int = Field(
            default=10,
            description="Number of results to retrieve (will show top 5)"
        )
        MIN_QUALITY_SCORE: float = Field(
            default=0.65,
            description="Minimum quality score filter (0.0-1.0)"
        )
        MIN_RELEVANCE_SCORE: float = Field(
            default=0.3,
            description="Minimum relevance score to show results"
        )
        ENABLE_HYBRID: bool = Field(
            default=True,
            description="Enable hybrid search (semantic + keyword)"
        )
        CONTEXT_WINDOW: int = Field(
            default=400,
            description="Context overlap for better understanding"
        )
        TIMEOUT: int = Field(
            default=30,
            description="Request timeout in seconds"
        )
    
    def __init__(self):
        self.valves = self.Valves()
        
        # Document type priorities for different query types
        self.doc_type_keywords = {
            "pdf": ["report", "document", "manual", "guide", "specification"],
            "docx": ["template", "form", "procedure", "policy", "process"],
            "xlsx": ["data", "schedule", "checklist", "register", "log"],
            "pptx": ["presentation", "overview", "summary", "briefing"],
            "csv": ["list", "table", "data", "records"]
        }
        
        # Railway-specific entity recognition
        self.railway_entities = {
            "safety": ["safety", "hazard", "risk", "incident", "accident", "emergency"],
            "maintenance": ["maintenance", "repair", "inspection", "servicing", "upkeep"],
            "operations": ["operations", "schedule", "timetable", "service", "running"],
            "compliance": ["compliance", "regulation", "standard", "requirement", "audit"],
            "business": ["business", "continuity", "planning", "strategy", "management"],
            "technical": ["technical", "specification", "design", "engineering", "system"],
            "hr": ["hr", "human resources", "personnel", "staff", "employee"],
            "finance": ["finance", "budget", "cost", "procurement", "supplier"]
        }
    
    def _analyze_query(self, query: str) -> Dict[str, Any]:
        """
        Analyze the user's query to understand intent and extract metadata.
        
        :param query: User's search query
        :return: Query analysis with intent, entities, and filters
        """
        query_lower = query.lower()
        analysis = {
            "original_query": query,
            "enhanced_query": query,
            "intent": "general",
            "entities": [],
            "preferred_doc_types": [],
            "filters": {},
            "search_type": "hybrid" if self.valves.ENABLE_HYBRID else "semantic"
        }
        
        # Detect railway entities
        for entity_type, keywords in self.railway_entities.items():
            if any(keyword in query_lower for keyword in keywords):
                analysis["entities"].append(entity_type)
                analysis["intent"] = entity_type
        
        # Detect preferred document types
        for doc_type, keywords in self.doc_type_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                analysis["preferred_doc_types"].append(doc_type)
        
        # Detect specific document references (e.g., "BMS-XXX-XXX")
        doc_refs = re.findall(r'BMS-[A-Z]+-[A-Z]+-\d+', query, re.IGNORECASE)
        if doc_refs:
            analysis["filters"]["document_id"] = doc_refs[0]
            analysis["intent"] = "specific_document"
        
        # Detect quality requirements
        if any(word in query_lower for word in ["best", "high quality", "top", "most relevant"]):
            analysis["filters"]["quality_score_min"] = 0.75
        elif any(word in query_lower for word in ["any", "all", "everything"]):
            analysis["filters"]["quality_score_min"] = 0.0
        else:
            analysis["filters"]["quality_score_min"] = self.valves.MIN_QUALITY_SCORE
        
        # Detect time-sensitive queries
        if any(word in query_lower for word in ["recent", "latest", "new", "updated"]):
            analysis["intent"] = "recent"
        
        # Enhance query with synonyms and context
        enhancements = []
        if "safety" in query_lower:
            enhancements.extend(["risk", "hazard", "incident"])
        if "maintenance" in query_lower:
            enhancements.extend(["repair", "inspection", "servicing"])
        if "business continuity" in query_lower:
            enhancements.extend(["disaster recovery", "emergency response", "resilience"])
        
        if enhancements:
            analysis["enhanced_query"] = f"{query} {' '.join(enhancements)}"
        
        return analysis
    
    def _format_advanced_results(
        self,
        results: List[Dict],
        query_analysis: Dict[str, Any],
        search_type: str
    ) -> str:
        """
        Format results with rich metadata and context.
        
        :param results: Search results from API
        :param query_analysis: Query analysis data
        :param search_type: Type of search performed
        :return: Formatted results string
        """
        if not results:
            return f"🔍 No results found for: '{query_analysis['original_query']}'\n\n💡 Try:\n- Broader search terms\n- Different keywords\n- Checking spelling"
        
        # Filter by relevance score
        filtered_results = [
            r for r in results 
            if r.get("score", 0) >= self.valves.MIN_RELEVANCE_SCORE
        ]
        
        if not filtered_results:
            return f"🔍 Found {len(results)} results but none met the relevance threshold (>{self.valves.MIN_RELEVANCE_SCORE})\n\n💡 Try a more specific query."
        
        # Sort by score and quality
        sorted_results = sorted(
            filtered_results,
            key=lambda x: (x.get("score", 0) * 0.7 + x.get("payload", {}).get("quality_score", 0) * 0.3),
            reverse=True
        )
        
        # Build output
        output = []
        output.append(f"🔍 **Found {len(filtered_results)} high-quality results**")
        
        if query_analysis["intent"] != "general":
            output.append(f"📌 **Query Type:** {query_analysis['intent'].replace('_', ' ').title()}")
        
        if query_analysis["entities"]:
            output.append(f"🏷️ **Topics:** {', '.join(query_analysis['entities']).title()}")
        
        output.append(f"🔎 **Search:** {search_type.title()}")
        output.append("\n---\n")
        
        # Show top 5 results with rich metadata
        for i, result in enumerate(sorted_results[:5], 1):
            payload = result.get("payload", {})
            score = result.get("score", 0.0)
            
            # Extract all available metadata
            doc_name = payload.get("document_name", "Unknown")
            doc_id = payload.get("document_id", "N/A")
            doc_type = payload.get("document_type", "unknown").upper()
            quality = payload.get("quality_score", 0.0)
            content = payload.get("content", "")
            chunk_id = payload.get("chunk_id", "N/A")
            version = payload.get("version_id", "1")
            
            # Additional metadata if available
            category = payload.get("category", "")
            department = payload.get("department", "")
            language = payload.get("language", "")
            keywords = payload.get("keywords", [])
            
            # Smart content preview
            content_preview = self._create_smart_preview(
                content,
                query_analysis["original_query"],
                max_length=250
            )
            
            # Calculate confidence score
            confidence = (score * 0.7 + quality * 0.3) * 100
            confidence_emoji = "🟢" if confidence >= 70 else "🟡" if confidence >= 50 else "🔴"
            
            output.append(f"\n**{i}. {doc_name}**")
            output.append(f"{confidence_emoji} **Confidence:** {confidence:.1f}% | **Relevance:** {score:.3f} | **Quality:** {quality:.2f}")
            output.append(f"📄 **Type:** {doc_type} | **ID:** {doc_id} | **Version:** {version}")
            
            if category:
                output.append(f"📁 **Category:** {category}")
            if department:
                output.append(f"🏢 **Department:** {department}")
            if keywords:
                output.append(f"🔑 **Keywords:** {', '.join(keywords[:5])}")
            
            output.append(f"\n📝 **Excerpt:**\n_{content_preview}_\n")
        
        # Add summary statistics
        output.append("\n---\n")
        output.append("📊 **Search Statistics:**")
        output.append(f"- Total Results: {len(filtered_results)}")
        output.append(f"- Average Quality: {sum(r.get('payload', {}).get('quality_score', 0) for r in sorted_results[:5]) / min(5, len(sorted_results)):.2f}")
        output.append(f"- Average Relevance: {sum(r.get('score', 0) for r in sorted_results[:5]) / min(5, len(sorted_results)):.3f}")
        
        # Document type distribution
        doc_types = {}
        for r in filtered_results:
            dt = r.get("payload", {}).get("document_type", "unknown")
            doc_types[dt] = doc_types.get(dt, 0) + 1
        output.append(f"- Document Types: {', '.join(f'{k.upper()}({v})' for k, v in sorted(doc_types.items()))}")
        
        output.append(f"\n🔗 **API:** {self.valves.BMS_API_URL}")
        output.append(f"📚 **Database:** 448 indexed documents | Quality: 0.714 avg")
        
        return "\n".join(output)
    
    def _create_smart_preview(self, content: str, query: str, max_length: int = 250) -> str:
        """
        Create an intelligent content preview highlighting relevant sections.
        
        :param content: Full content text
        :param query: Search query
        :param max_length: Maximum preview length
        :return: Smart preview string
        """
        if not content:
            return "[No content available]"
        
        # Try to find query terms in content
        query_terms = query.lower().split()
        content_lower = content.lower()
        
        # Find best matching section
        best_pos = 0
        best_score = 0
        
        for term in query_terms:
            pos = content_lower.find(term)
            if pos != -1:
                # Count how many terms are near this position
                score = sum(1 for t in query_terms if t in content_lower[max(0, pos-100):pos+100])
                if score > best_score:
                    best_score = score
                    best_pos = pos
        
        # Extract preview around best position
        if best_score > 0:
            start = max(0, best_pos - 100)
            end = min(len(content), best_pos + max_length - 100)
            preview = content[start:end]
            
            # Clean up
            if start > 0:
                preview = "..." + preview
            if end < len(content):
                preview = preview + "..."
        else:
            # Just take beginning
            preview = content[:max_length]
            if len(content) > max_length:
                preview += "..."
        
        return preview.strip()
    
    def search(
        self,
        query: str,
        limit: Optional[int] = None,
        __user__: dict = {}
    ) -> str:
        """
        Intelligent search with automatic query analysis and optimization.
        
        :param query: Natural language search query
        :param limit: Number of results to retrieve
        :return: Formatted search results with rich metadata
        """
        # Analyze query
        analysis = self._analyze_query(query)
        
        # Determine search parameters
        limit = limit or self.valves.DEFAULT_LIMIT
        search_type = analysis["search_type"]
        
        # Build API request
        endpoint = f"{self.valves.BMS_API_URL}/api/v1/search/{search_type}"
        payload = {
            "query": analysis["enhanced_query"],
            "limit": limit,
            "filters": analysis["filters"]
        }
        
        # Add document type filter if detected
        if len(analysis["preferred_doc_types"]) == 1:
            payload["filters"]["document_type"] = analysis["preferred_doc_types"][0]
        
        try:
            response = requests.post(endpoint, json=payload, timeout=self.valves.TIMEOUT)
            
            if response.status_code != 200:
                return f"❌ Search failed: {response.status_code} - {response.text}"
            
            data = response.json()
            results = data.get("results", [])
            
            return self._format_advanced_results(results, analysis, search_type)
            
        except requests.exceptions.Timeout:
            return f"❌ Search timed out after {self.valves.TIMEOUT} seconds"
        except requests.exceptions.ConnectionError:
            return f"❌ Cannot connect to BMS API at {self.valves.BMS_API_URL}\n\n💡 Make sure the API is running on port 8000"
        except Exception as e:
            return f"❌ Search error: {str(e)}"
    
    def get_document_info(self, document_id: str, __user__: dict = {}) -> str:
        """
        Get detailed information about a specific document.
        
        :param document_id: Document ID (e.g., BMS-XXX-XXX-001)
        :return: Document details
        """
        try:
            endpoint = f"{self.valves.BMS_API_URL}/api/v1/search/semantic"
            payload = {
                "query": document_id,
                "limit": 1,
                "filters": {"document_id": document_id}
            }
            
            response = requests.post(endpoint, json=payload, timeout=self.valves.TIMEOUT)
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                
                if results:
                    payload = results[0].get("payload", {})
                    return f"""📄 **Document Information**

**Name:** {payload.get('document_name', 'Unknown')}
**ID:** {payload.get('document_id', 'N/A')}
**Type:** {payload.get('document_type', 'unknown').upper()}
**Quality Score:** {payload.get('quality_score', 0):.2f}
**Version:** {payload.get('version_id', '1')}
**Category:** {payload.get('category', 'N/A')}
**Language:** {payload.get('language', 'N/A')}

**Content Preview:**
{payload.get('content', '')[:500]}...
"""
                else:
                    return f"❌ Document '{document_id}' not found"
            else:
                return f"❌ Failed to retrieve document: {response.status_code}"
                
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    def get_api_status(self, __user__: dict = {}) -> str:
        """
        Check BMS API and database health.
        
        :return: System status
        """
        try:
            response = requests.get(f"{self.valves.BMS_API_URL}/health", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                status = data.get("status", "unknown")
                services = data.get("services", {})
                
                output = [f"✅ **BMS API Status: {status.upper()}**\n"]
                output.append("**Services:**")
                for service, state in services.items():
                    icon = "✅" if state == "connected" else "❌"
                    output.append(f"  {icon} {service}: {state}")
                
                output.append("\n**Database:**")
                output.append("  📚 Documents: 448 indexed")
                output.append("  📊 Quality: 0.714 average")
                output.append("  🔍 Search: Semantic + Hybrid")
                output.append("  📏 Vectors: 768 dimensions")
                
                return "\n".join(output)
            else:
                return f"⚠️ API returned status code: {response.status_code}"
                
        except Exception as e:
            return f"❌ Cannot reach BMS API: {str(e)}"
