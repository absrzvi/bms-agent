# T032.1: Formatting Improvements for bms_search.py

**Current Version**: Enhanced v3.0  
**File**: `/workspace/001-bms-agent/tools/bms_search.py`  
**Focus**: Lines 1003-1057 (_format_results method)

---

## Current Formatting Analysis

### ✅ What Works Well
1. Clear structure with numbered results
2. Metadata display (type, quality, relevance)
3. Content preview (800 chars)
4. Keywords display
5. Department/fleet/standard metadata

### ⚠️ What Needs Improvement

#### 1. **Citations & Document Titles**
**Current**:
```
**1. BMS-BDEV-FOR-005 Bid Action Log Check List.xlsx**
   📄 Type: xlsx | Quality: 0.85 | Relevance: 0.723
```

**Issues**:
- No page numbers
- No section information
- Document title could be clearer
- No document ID separate from title

**Improved**:
```
**1. Bid Action Log Check List**
   📋 Document ID: BMS-BDEV-FOR-005
   📄 Type: Excel Spreadsheet (XLSX) | Quality: ⭐⭐⭐⭐☆ (85%)
   📊 Relevance: 72% (High Confidence)
   📍 Location: Section 3.2, Pages 12-14
```

---

#### 2. **Relevance Score Display**
**Current**:
```
Relevance: 0.723
```

**Issues**:
- Raw decimal is not user-friendly
- No confidence indicator
- No visual representation

**Improved Options**:

**Option A - Percentage with Confidence**:
```
📊 Relevance: 72% (High Confidence)
```

**Option B - Star Rating with Percentage**:
```
📊 Match Quality: ⭐⭐⭐⭐☆ (72%)
```

**Option C - Visual Bar**:
```
📊 Relevance: ████████░░ 72% (High)
```

**Recommendation**: Use Option A (Percentage with Confidence)

---

#### 3. **Error Messages**
**Current**:
```python
# Line 174
return f"❌ Search failed: {response.status_code} - {response.text}"

# Line 180
return f"🔍 No results found for query: '{query}'"

# Line 185
return f"❌ Search timed out after {self.valves.TIMEOUT} seconds"

# Line 187
return f"❌ Cannot connect to BMS API at {self.valves.BMS_API_URL}"
```

**Issues**:
- No suggestions for what to do next
- No context for why it failed
- No alternative actions

**Improved**:

```python
# Connection Error
return f"""❌ Cannot connect to BMS API

**Issue**: Unable to reach the BMS search service at {self.valves.BMS_API_URL}

**Possible Causes**:
- API service may be down
- Network connectivity issues
- Invalid API URL configuration

**What to try**:
1. Check if the BMS API is running
2. Verify your network connection
3. Contact support if the issue persists
"""

# No Results
return f"""🔍 No results found for: '{query}'

**Suggestions**:
- Try different keywords or phrases
- Check spelling and try simpler terms
- Use broader search terms (e.g., "safety" instead of "EN45545-2:2020")
- Try using the document code if you know it (e.g., "BMS-HUMR-FOR-005")

**Need help?** Try these searches:
- "forms" - to browse all forms
- "safety" - for safety documentation
- "procurement" - for business documents
"""

# Timeout
return f"""❌ Search timed out after {self.valves.TIMEOUT} seconds

**What happened**: Your search took too long to complete

**What to try**:
- Simplify your query (use fewer words)
- Try again in a moment
- If this persists, contact support

**Your query**: {query}
"""

# Search Failed
return f"""❌ Search failed (Error {response.status_code})

**Technical Details**: {response.text[:200]}

**What to do**:
1. Try your search again
2. If the error persists, note the error code above
3. Contact support with the error code

**Your query**: {query}
"""
```

---

#### 4. **Empty Result Handling**
**Current**:
```python
if not results:
    return f"🔍 No results found for query: '{query}'"
```

**Improved with Query Suggestions**:

```python
def _format_empty_results(self, query: str) -> str:
    """Format empty results with helpful suggestions."""
    
    # Detect query characteristics
    query_lower = query.lower()
    is_code_query = bool(re.search(r'BMS-[A-Z]{4}-[A-Z]{3}-\d{3}', query, re.IGNORECASE))
    is_form_query = any(w in query_lower for w in ["form", "template", "checklist"])
    is_technical = any(w in query_lower for w in ["technical", "specification", "architecture"])
    
    output = [f"🔍 **No results found for**: '{query}'\n"]
    output.append("**Suggestions to improve your search:**\n")
    
    if is_code_query:
        output.append("✓ Your search looks like a document code")
        output.append("  - Check if the code format is correct (BMS-DEPT-TYPE-###)")
        output.append("  - Try removing the file extension (.xlsx, .pdf, etc.)")
        output.append("  - Example: 'BMS-HUMR-FOR-005'\n")
    
    elif is_form_query:
        output.append("✓ Looking for forms? Try:")
        output.append("  - 'forms' - to see all available forms")
        output.append("  - 'HUMR forms' - for HR forms")
        output.append("  - 'procurement checklist' - for business forms\n")
    
    elif is_technical:
        output.append("✓ Looking for technical docs? Try:")
        output.append("  - 'BMS architecture'")
        output.append("  - 'network specifications'")
        output.append("  - 'system requirements'\n")
    
    else:
        output.append("**General tips:**")
        output.append("  • Use fewer, more specific keywords")
        output.append("  • Try synonyms (e.g., 'employee' → 'staff' or 'personnel')")
        output.append("  • Check spelling")
        output.append("  • Use broader terms first, then refine\n")
    
    # Add browse suggestions
    output.append("**Browse by category:**")
    output.append("  • Type 'forms' for all forms")
    output.append("  • Type 'safety' for safety documentation")
    output.append("  • Type 'procurement' for business documents")
    output.append("  • Type 'technical' for engineering docs")
    
    return "\n".join(output)
```

---

#### 5. **Quality Score Visualization**
**Current**:
```
Quality: 0.85
```

**Improved**:

```python
def _format_quality_score(self, score: float) -> str:
    """Convert quality score to user-friendly format."""
    percentage = int(score * 100)
    
    # Star rating (1-5 stars)
    stars = int((score * 5) + 0.5)  # Round to nearest star
    star_display = "⭐" * stars + "☆" * (5 - stars)
    
    # Quality label
    if score >= 0.90:
        label = "Excellent"
    elif score >= 0.80:
        label = "Very Good"
    elif score >= 0.70:
        label = "Good"
    elif score >= 0.60:
        label = "Fair"
    else:
        label = "Low"
    
    return f"{star_display} {percentage}% ({label})"

# Usage:
output.append(f"   ✨ Quality: {self._format_quality_score(quality)}")
```

---

#### 6. **Complete Improved _format_results Method**

Here's the full improved version:

```python
def _format_results(
    self,
    results: List[Dict],
    query: str,
    search_type: str
) -> str:
    """Format search results for display with improved UX."""
    if not results:
        return self._format_empty_results(query)
    
    output = [f"📚 **Found {len(results)} documents for**: '{query}'\n"]
    
    for i, result in enumerate(results, 1):
        score = result.get("score", 0.0)
        doc_name_raw = result.get("document_name") or result.get("payload", {}).get("document_name", "Unknown")
        doc_type = result.get("document_type") or result.get("payload", {}).get("document_type", "unknown")
        metadata = result.get("metadata", {})
        quality = metadata.get("quality_score", 0.0) or result.get("quality_score", 0.0)
        content = result.get("content", "")
        
        # Extract enhanced metadata
        keywords = metadata.get("keywords", [])
        department = metadata.get("department", "")
        fleet_type = metadata.get("fleet_type", "")
        standard = metadata.get("standard_compliance", "")
        page_range = metadata.get("page_range", "")  # If available
        section = metadata.get("section", "")  # If available
        
        # Parse document name and ID
        doc_id = ""
        doc_title = doc_name_raw
        
        # Try to extract document ID pattern (BMS-XXXX-XXX-XXX)
        id_match = re.search(r'(BMS-[A-Z]{4}-[A-Z]{3}-\d{3})', doc_name_raw)
        if id_match:
            doc_id = id_match.group(1)
            # Remove ID and file extension from title
            doc_title = re.sub(r'BMS-[A-Z]{4}-[A-Z]{3}-\d{3}\s*', '', doc_name_raw)
            doc_title = re.sub(r'\.(xlsx?|docx?|pdf|pptx?|csv|txt)$', '', doc_title, flags=re.IGNORECASE)
            doc_title = doc_title.strip()
        
        # Format document type nicely
        type_display = {
            "xlsx": "Excel Spreadsheet",
            "xls": "Excel Spreadsheet",
            "docx": "Word Document",
            "doc": "Word Document",
            "pdf": "PDF Document",
            "pptx": "PowerPoint Presentation",
            "ppt": "PowerPoint Presentation",
            "csv": "CSV Data File",
            "txt": "Text Document"
        }.get(doc_type.lower(), doc_type.upper())
        
        # Truncate content intelligently (find sentence boundary)
        content_preview = content[:800]
        if len(content) > 800:
            # Try to end at sentence
            last_period = content_preview.rfind('.')
            if last_period > 600:  # Only if period is reasonably far in
                content_preview = content_preview[:last_period + 1]
            content_preview += "..."
        
        # === BUILD OUTPUT ===
        output.append(f"\n**{i}. {doc_title}**")
        
        # Document ID (if found)
        if doc_id:
            output.append(f"   📋 Document ID: {doc_id}")
        
        # Document type and quality
        quality_display = self._format_quality_score(quality)
        output.append(f"   📄 Type: {type_display}")
        output.append(f"   ✨ Quality: {quality_display}")
        
        # Relevance score
        relevance_display = self._format_relevance_score(score)
        output.append(f"   {relevance_display}")
        
        # Location (if available)
        location_parts = []
        if section:
            location_parts.append(f"Section {section}")
        if page_range:
            location_parts.append(f"Pages {page_range}")
        if location_parts:
            output.append(f"   📍 Location: {', '.join(location_parts)}")
        
        # Metadata badges
        badges = []
        if department:
            badges.append(f"🏢 {department}")
        if fleet_type:
            badges.append(f"🚆 {fleet_type}")
        if standard:
            badges.append(f"📜 {standard}")
        
        if badges:
            output.append(f"   {' | '.join(badges)}")
        
        # Keywords (top 5)
        if keywords:
            keywords_str = ", ".join(str(k) for k in keywords[:5])
            output.append(f"   🔑 Keywords: {keywords_str}")
        
        # Content preview
        output.append(f"\n   📝 **Excerpt**:")
        output.append(f"   {content_preview}\n")
        
        # Show boost info if smart search
        if search_type == "smart" and "boosts_applied" in result:
            boosts = result.get("boosts_applied", [])
            if boosts:
                boost_str = ", ".join(boosts)
                original_score = result.get("original_score", score)
                boost_factor = score / original_score if original_score > 0 else 1.0
                output.append(f"   🚀 **Boosted**: {boost_str} (×{boost_factor:.1f})\n")
    
    # Footer
    output.append(f"\n{'─' * 70}")
    output.append(f"🔍 Search Type: {search_type.title()} | Results: {len(results)}")
    output.append(f"🌐 API: {self.valves.BMS_API_URL}")
    
    return "\n".join(output)


def _format_relevance_score(self, score: float) -> str:
    """Format relevance score as percentage with confidence level."""
    percentage = int(score * 100)
    
    # Determine confidence level
    if percentage >= 80:
        confidence = "Very High"
        icon = "🎯"
    elif percentage >= 60:
        confidence = "High"
        icon = "📊"
    elif percentage >= 40:
        confidence = "Medium"
        icon = "📈"
    elif percentage >= 20:
        confidence = "Low"
        icon = "📉"
    else:
        confidence = "Very Low"
        icon = "⚠️"
    
    return f"{icon} Relevance: {percentage}% ({confidence} Confidence)"


def _format_quality_score(self, score: float) -> str:
    """Convert quality score to user-friendly format with stars."""
    percentage = int(score * 100)
    
    # Star rating (1-5 stars)
    stars = min(5, max(1, int((score * 5) + 0.5)))
    star_display = "⭐" * stars + "☆" * (5 - stars)
    
    # Quality label
    if score >= 0.90:
        label = "Excellent"
    elif score >= 0.80:
        label = "Very Good"
    elif score >= 0.70:
        label = "Good"
    elif score >= 0.60:
        label = "Fair"
    else:
        label = "Needs Review"
    
    return f"{star_display} {percentage}% ({label})"


def _format_empty_results(self, query: str) -> str:
    """Format empty results with context-aware suggestions."""
    import re
    
    query_lower = query.lower()
    is_code_query = bool(re.search(r'BMS-[A-Z]{4}-[A-Z]{3}-\d{3}', query, re.IGNORECASE))
    is_form_query = any(w in query_lower for w in ["form", "template", "checklist"])
    is_technical = any(w in query_lower for w in ["technical", "specification", "architecture", "network"])
    
    output = [f"🔍 **No results found for**: '{query}'\n"]
    output.append("**💡 Suggestions to improve your search:**\n")
    
    if is_code_query:
        output.append("✓ **Document Code Detected**")
        output.append("  • Check the code format (BMS-DEPT-TYPE-###)")
        output.append("  • Remove file extensions (.xlsx, .pdf)")
        output.append("  • Example: 'BMS-HUMR-FOR-005'\n")
    
    elif is_form_query:
        output.append("✓ **Looking for forms? Try:**")
        output.append("  • 'forms' → see all forms")
        output.append("  • 'HUMR forms' → HR forms")
        output.append("  • 'procurement checklist' → business forms\n")
    
    elif is_technical:
        output.append("✓ **Looking for technical docs? Try:**")
        output.append("  • 'BMS architecture'")
        output.append("  • 'network requirements'")
        output.append("  • 'system specifications'\n")
    
    else:
        output.append("**General search tips:**")
        output.append("  • Use 2-4 keywords instead of full sentences")
        output.append("  • Try synonyms (e.g., 'staff' instead of 'employee')")
        output.append("  • Check spelling")
        output.append("  • Start broad, then refine\n")
    
    output.append("**📂 Browse by category:**")
    output.append("  • `forms` - all forms and templates")
    output.append("  • `safety` - safety & compliance docs")
    output.append("  • `procurement` - business & procurement")
    output.append("  • `engineering` - technical documentation")
    
    return "\n".join(output)
```

---

## Implementation Priority

### 🔴 HIGH PRIORITY (Do First)
1. **Relevance Score Display** - Lines 1036, 1015
   - Change from decimal to percentage with confidence
   - Impact: Immediate user comprehension improvement

2. **Error Messages** - Lines 174, 180, 185, 187
   - Add helpful suggestions and next steps
   - Impact: Reduces user frustration

3. **Empty Results** - Line 1011
   - Add context-aware suggestions
   - Impact: Helps users succeed on retry

### 🟡 MEDIUM PRIORITY (Do Second)
4. **Quality Score Visualization** - Line 1020
   - Add stars and labels
   - Impact: Better quality perception

5. **Document Title Parsing** - Line 1017
   - Separate ID from title
   - Impact: Cleaner presentation

### 🟢 LOW PRIORITY (Nice to Have)
6. **Citation Information** - Lines 1023-1029
   - Add page numbers/sections (if available in metadata)
   - Impact: Better academic/professional use

---

## Testing Checklist

After implementing improvements, test:

- [ ] Normal search with results
- [ ] Empty search (no results)
- [ ] Connection error (API down)
- [ ] Timeout error
- [ ] Search with exact document code
- [ ] Search with form keyword
- [ ] Search with technical terms
- [ ] Smart search with metadata boost
- [ ] Relevance scores display correctly
- [ ] Quality stars display correctly

---

## Example: Before vs After

### BEFORE:
```
🔍 **Found 3 results for:** 'bid checklist'

**1. BMS-BDEV-FOR-005 Bid Action Log Check List.xlsx**
   📄 Type: xlsx | Quality: 0.85 | Relevance: 0.723 | Dept: BDEV
   🔑 Keywords: bid, checklist, action, log
   📝 This form is used to track bid actions and ensure all requirements are met...
```

### AFTER:
```
📚 **Found 3 documents for**: 'bid checklist'

**1. Bid Action Log Check List**
   📋 Document ID: BMS-BDEV-FOR-005
   📄 Type: Excel Spreadsheet
   ✨ Quality: ⭐⭐⭐⭐☆ 85% (Very Good)
   🎯 Relevance: 72% (High Confidence)
   🏢 BDEV
   🔑 Keywords: bid, checklist, action, log

   📝 **Excerpt**:
   This form is used to track bid actions and ensure all requirements are met...

   🚀 **Boosted**: form, department (×1.8)
```

---

## Ready to Implement?

Choose your approach:

**Option A**: I implement all HIGH PRIORITY improvements now (~15 min)  
**Option B**: I create a side-by-side comparison file for you to review first  
**Option C**: We implement one improvement at a time and test each

**Recommendation**: Option A - Implement HIGH PRIORITY changes now for immediate user benefit.
