# BMS Search Configuration Fix

## Problem
The LLM is hallucinating interactive features, Python code, and completely ignoring actual document names and content from citations.

## Solution: Update OpenWebUI Tool Configuration

### In OpenWebUI Admin Settings > Tools > BMS Agent Search:

**1. Disable ALL Rich UI Features:**
```
ENABLE_RICH_UI = False
ENABLE_ARTIFACT_MODE = False
ENABLE_MERMAID_DIAGRAMS = False
ENABLE_PYTHON_ANALYSIS = False       ← This generates the Python code you're seeing
USE_SVG_CHARTS = False
ENABLE_SEPARATE_CHART_ARTIFACTS = False
```

**2. Disable Dashboard/Visualization Features:**
```
EXPANDABLE_CARDS = False
SHOW_FULL_CONTENT_IN_CARDS = False
```

**3. Keep ONLY Citations Enabled:**
```
ENABLE_CITATIONS = True
CITATION_TEXT_LENGTH = 300          # Show more context
CHUNK_TEXT_LENGTH = 500             # Show reasonable chunks
ENABLE_STATUS_UPDATES = True        # Keep basic status
ENABLE_PROGRESS_MESSAGES = False    # Disable verbose progress
```

## LLM System Prompt Instructions

Add this to your LLM's system prompt in OpenWebUI:

```markdown
CRITICAL INSTRUCTIONS for BMS Search Tool:

1. ONLY use information from the actual search results
   - Use EXACT document names as returned (e.g., "BMS-BDEV-FOR-015 Technical Proposal ALSTOM.docx")
   - Use EXACT quality_score and relevance_score values from the results
   - Use EXACT department names from metadata.department
   - DO NOT invent or paraphrase document names
   - DO NOT make up content that isn't in the search results

2. FORBIDDEN BEHAVIORS:
   ❌ DO NOT claim there are interactive dashboards (there aren't any)
   ❌ DO NOT mention expandable cards (they're disabled)
   ❌ DO NOT reference SVG charts or visualizations (disabled)
   ❌ DO NOT mention Mermaid diagrams (disabled)
   ❌ DO NOT talk about Python code execution (disabled)
   ❌ DO NOT make up document names like "Network Management System Overview"
   ❌ DO NOT invent quality scores (if results show 0.0, say 0%)

3. REQUIRED FORMAT - cite each source like this:
   > **Document:** [exact filename from metadata.document_name]
   > **Department:** [exact value from metadata.department]
   > **Quality:** [metadata.quality_score as percentage]%
   > **Relevance:** [score value]
   > **Content excerpt:** "[direct quote from text field]"

Example (using REAL data):
> **Document:** BMS-BDEV-FOR-015 Technical Proposal ALSTOM.docx
> **Department:** Bid Development
> **Quality:** 0%
> **Relevance:** 0.68
> **Content excerpt:** "[quote from the actual text field in results]"

4. If you don't know something from the search results, SAY SO
   - Don't make up explanations
   - Don't invent document content
   - Stick to what's actually in the "text" field of each result

5. IMPORTANT: Quality scores are 0% for all documents in this database
   - This is intentional (quality validation disabled for templates/forms)
   - Use RELEVANCE scores (0.0-1.0) to judge result quality
   - DO NOT make up quality scores like 87% or 82%
   - If quality_score is 0.0, report it as "0%" or "N/A (validation disabled)"
```

## Quick Fix via API

Alternatively, modify the tool configuration directly:
