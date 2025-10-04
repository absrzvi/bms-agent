"""
Prompt templates for answer generation
"""

# System prompts for different query types
SYSTEM_PROMPTS = {
    "general": """You are a helpful assistant for railway documentation. 
Provide accurate, clear answers based on the provided context.""",
    
    "safety": """You are a railway safety expert with deep knowledge of safety standards and procedures.
Prioritize safety information and include all relevant warnings.""",
    
    "technical": """You are a railway technical expert with expertise in systems, components, and specifications.
Provide precise technical information with proper terminology.""",
    
    "procedural": """You are a railway procedures expert specializing in operational processes.
Provide clear, step-by-step guidance with safety considerations."""
}

# Answer format templates
ANSWER_FORMATS = {
    "default": """Based on the provided context, here is the answer:

{answer}

{citations}""",
    
    "with_confidence": """Answer (Confidence: {confidence}%):

{answer}

Sources:
{citations}""",
    
    "structured": """## Answer

{answer}

## Sources
{citations}

## Confidence: {confidence}%"""
}

# Citation formats
CITATION_FORMATS = {
    "inline": "[{index}] {document_name}",
    "detailed": "[{index}] {document_name} (Relevance: {score:.2%})",
    "full": """[{index}] {document_name}
   Chunk {chunk_index} | Relevance: {score:.2%}
   "{preview}..." """
}
