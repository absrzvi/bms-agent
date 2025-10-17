# BMS Agent Enhanced Search - Test Prompts

## Test Suite for All 11 Search Functions

### 1. search_semantic() - Conceptual Queries

**Test Prompt 1.1 - General Concept**
```
What is business continuity and how does it apply to railway operations?
```
Expected: Should use `search_semantic()` for conceptual understanding

**Test Prompt 1.2 - Natural Language**
```
How should we handle a new employee starting their first day?
```
Expected: Should use `search_semantic()` for process-oriented query

**Test Prompt 1.3 - Synonym Variation**
```
What are the guidelines for staff absence due to illness?
```
Expected: Should use `search_semantic()` to find "sick leave" or "sickness absence" policies

---

### 2. search_hybrid() - Specific Terms & Codes

**Test Prompt 2.1 - Document Code**
```
What does BMS-HUMR-POL-010 say about notification requirements?
```
Expected: Should use `search_hybrid()` for exact document code matching

**Test Prompt 2.2 - Technical Terms**
```
Find information about material management and procurement processes
```
Expected: Should use `search_hybrid()` with keyword matching

**Test Prompt 2.3 - Mixed Query**
```
What are the inventory control procedures in BMS-ENGI-FOR-003?
```
Expected: Should use `search_hybrid()` combining document code and keywords

---

### 3. search_by_document_type() - Format Filtering

**Test Prompt 3.1 - Excel Data**
```
Show me data tables or spreadsheets about employee records
```
Expected: Should use `search_by_document_type(query, "xlsx")`

**Test Prompt 3.2 - PDF Policies**
```
Find all PDF policy documents about workplace safety
```
Expected: Should use `search_by_document_type(query, "pdf")`

**Test Prompt 3.3 - Word Documents**
```
Are there any Word documents with procedure templates?
```
Expected: Should use `search_by_document_type(query, "docx")`

---

### 4. search_by_fleet_type() - Railway Fleet Filtering

**Test Prompt 4.1 - Railjet Specific**
```
What are the maintenance procedures for Railjet trains?
```
Expected: Should use `search_by_fleet_type("maintenance procedures", "Railjet")`

**Test Prompt 4.2 - Cityjet Operations**
```
Find Cityjet operational guidelines and schedules
```
Expected: Should use `search_by_fleet_type("operational guidelines", "Cityjet")`

**Test Prompt 4.3 - Fleet Comparison**
```
What are the differences between Railjet and Cityjet maintenance requirements?
```
Expected: Should use `search_by_fleet_type()` twice or compare results

---

### 5. search_by_standard() - Compliance Filtering

**Test Prompt 5.1 - EN50155 Standard**
```
What are the EN50155 compliance requirements for electronic equipment?
```
Expected: Should use `search_by_standard("compliance requirements", "EN50155")`

**Test Prompt 5.2 - EN45545 Fire Safety**
```
Show me EN45545 fire protection requirements for railway vehicles
```
Expected: Should use `search_by_standard("fire protection requirements", "EN45545")`

**Test Prompt 5.3 - TSI Specifications**
```
What TSI technical specifications apply to our operations?
```
Expected: Should use `search_by_standard("technical specifications", "TSI")`

---

### 6. search_by_department() - Department Filtering

**Test Prompt 6.1 - Human Resources**
```
What HR policies exist for employee leave and absences?
```
Expected: Should use `search_by_department("leave and absences", "HUMR")`

**Test Prompt 6.2 - Engineering**
```
Find engineering technical specifications and standards
```
Expected: Should use `search_by_department("technical specifications", "ENGI")`

**Test Prompt 6.3 - Information Security**
```
What are the IT security policies for data protection?
```
Expected: Should use `search_by_department("data protection", "ISEC")`

**Test Prompt 6.4 - Multi-Department**
```
Are there any policies that apply to both HR and Engineering departments?
```
Expected: Should use `search_by_department()` twice and compare

---

### 7. search_with_context() - Contextual Search

**Test Prompt 7.1 - Complex Process**
```
Explain the complete process for incident reporting and escalation
```
Expected: Should use `search_with_context("incident reporting escalation")` for detailed context

**Test Prompt 7.2 - Multi-Step Procedure**
```
What are the detailed steps for onboarding a new contractor?
```
Expected: Should use `search_with_context("contractor onboarding")` for comprehensive info

**Test Prompt 7.3 - Integration Process**
```
How do different systems integrate for material requisition workflow?
```
Expected: Should use `search_with_context("material requisition workflow integration")`

---

### 8. search_high_quality() - Quality Filtering

**Test Prompt 8.1 - Critical Safety**
```
What are the official safety procedures for emergency situations? I need verified information.
```
Expected: Should use `search_high_quality("emergency safety procedures", min_quality=0.85)`

**Test Prompt 8.2 - Compliance Requirements**
```
Give me the exact compliance requirements for railway operations - this is for an audit
```
Expected: Should use `search_high_quality("compliance requirements", min_quality=0.80)`

**Test Prompt 8.3 - Official Procedures**
```
What are the verified procedures for handling hazardous materials?
```
Expected: Should use `search_high_quality("hazardous materials procedures", min_quality=0.85)`

---

### 9. compare_search_types() - Search Comparison

**Test Prompt 9.1 - Ambiguous Query**
```
I'm not sure how to search for this: material management
```
Expected: Should use `compare_search_types("material management")` to show both approaches

**Test Prompt 9.2 - Exploration**
```
Show me different ways to find information about network architecture
```
Expected: Should use `compare_search_types("network architecture")`

**Test Prompt 9.3 - Best Approach**
```
What's the best way to search for "employee training programs"?
```
Expected: Should use `compare_search_types("employee training programs")`

---

### 10. search_documents() - Advanced Custom Search

**Test Prompt 10.1 - Multiple Filters**
```
Find high-quality PDF documents from the Engineering department about network components
```
Expected: Should use `search_documents()` with filters: `{document_type: "pdf", department: "ENGI", quality_score_min: 0.75}`

**Test Prompt 10.2 - Hierarchical Search**
```
Show me only parent-level chunks about safety procedures
```
Expected: Should use `search_documents()` with filters: `{is_parent: true}`

**Test Prompt 10.3 - Context-Rich Quality Search**
```
Find high-quality documents with detailed context about compliance
```
Expected: Should use `search_documents()` with filters: `{has_context: true, quality_score_min: 0.80}`

---

### 11. get_api_status() - Health Check

**Test Prompt 11.1 - System Check**
```
Is the BMS search system working properly?
```
Expected: Should use `get_api_status()`

**Test Prompt 11.2 - Troubleshooting**
```
I'm having trouble searching - can you check if the system is online?
```
Expected: Should use `get_api_status()`

**Test Prompt 11.3 - Service Status**
```
What's the current status of the documentation database?
```
Expected: Should use `get_api_status()`

---

## Multi-Function Test Scenarios

### Scenario 1: Progressive Refinement

**Prompt Sequence:**
1. "What are the safety procedures?" → `search_semantic()`
2. "Specifically for Railjet trains" → `search_by_fleet_type()`
3. "According to EN50155 standards" → `search_by_standard()`
4. "I need the official verified version" → `search_high_quality()`

### Scenario 2: Department-Specific Investigation

**Prompt Sequence:**
1. "What policies does HR have?" → `search_by_department("policies", "HUMR")`
2. "What about Engineering?" → `search_by_department("policies", "ENGI")`
3. "Compare the two" → Synthesize results
4. "Show me high-quality ones only" → `search_high_quality()`

### Scenario 3: Comprehensive Research

**Prompt Sequence:**
1. "Tell me about material management" → `search_hybrid()`
2. "Show me different search approaches" → `compare_search_types()`
3. "I need detailed context" → `search_with_context()`
4. "Filter by Engineering department" → `search_by_department()`
5. "Only high-quality documents" → `search_high_quality()`

---

## Expected Metadata Usage Test

### Test Metadata Recognition

**Prompt:**
```
Find documents about "inventory management" and tell me:
- Which department owns this process
- What quality score the information has
- What keywords are associated
- Any technical terms mentioned
- Relevant compliance standards
```

**Expected Response Should Include:**
- Department: ENGI or relevant dept from metadata
- Quality Score: X.XX from quality_score field
- Keywords: List from keywords metadata
- Technical Terms: List from technical_terms metadata
- Standards: From standard_compliance metadata

---

## Edge Cases & Error Handling

### Test 1: No Results
```
Find information about "quantum computing in railways"
```
Expected: Should try multiple search types, then gracefully report no results

### Test 2: Ambiguous Department
```
Who handles employee IT access requests?
```
Expected: Should search both HUMR and ISEC departments

### Test 3: Multiple Fleet Types
```
What maintenance procedures apply to all train types?
```
Expected: Should search without fleet filter or aggregate multiple fleet searches

### Test 4: Low Quality Results
```
Find any information about [obscure topic]
```
Expected: Should return results but note lower quality scores

---

## Metadata Display Test

**Prompt:**
```
Search for "BMS-HUMR-POL-010" and show me all available metadata
```

**Expected Response Should Display:**
- Document name: BMS-HUMR-POL-010 [Name]
- Type: pdf/docx/etc
- Department: HUMR
- Quality: 0.XX
- Relevance: 0.XX
- Keywords: [list]
- Entities: [list]
- Technical Terms: [list]
- Has Context: Yes/No
- Contextual Description: [if available]
- Standard Compliance: [if available]
- Fleet Type: [if available]

---

## Performance & Ranking Test

### Test Enhanced Ranking

**Prompt 1: Keyword-Rich Query**
```
Find "BMS-ENGI-FOR-003 material requisition form"
```
Expected: Should rank results with:
- Document name match (3x weight)
- Keywords match (2.5x weight)
- High relevance score

**Prompt 2: Entity-Based Query**
```
What policies mention "Railjet" and "EN50155"?
```
Expected: Should boost results with:
- Entity matches (2x weight)
- Technical term matches (2x weight)

**Prompt 3: Quality-Sensitive Query**
```
Official safety procedures (verified only)
```
Expected: Should apply quality boost and filter

---

## Quick Test Checklist

Use these quick prompts to verify each function works:

- [ ] `search_semantic`: "What is business continuity?"
- [ ] `search_hybrid`: "BMS-HUMR-POL-010 sick leave"
- [ ] `search_by_document_type`: "Find Excel spreadsheets about inventory"
- [ ] `search_by_fleet_type`: "Railjet maintenance procedures"
- [ ] `search_by_standard`: "EN50155 requirements"
- [ ] `search_by_department`: "HR leave policies"
- [ ] `search_with_context`: "Detailed incident reporting process"
- [ ] `search_high_quality`: "Official safety procedures (verified)"
- [ ] `compare_search_types`: "Compare search for 'network architecture'"
- [ ] `search_documents`: "High-quality Engineering PDFs about networks"
- [ ] `get_api_status`: "Is the system working?"

---

## Success Criteria

A successful test should demonstrate:

1. ✅ **Correct function selection** based on query type
2. ✅ **Metadata utilization** in responses (keywords, entities, quality, etc.)
3. ✅ **Proper citations** with document names and metadata
4. ✅ **Quality awareness** noting confidence levels
5. ✅ **Multi-source synthesis** when using multiple searches
6. ✅ **Graceful degradation** when results are limited
7. ✅ **Railway context** understanding (fleets, standards, departments)
8. ✅ **Enhanced ranking** showing keyword/entity/technical term matches

---

## Notes for LLM Testing

When testing with an LLM:

1. **Start simple**: Test basic functions first
2. **Progress to complex**: Multi-step scenarios
3. **Verify metadata**: Check if all metadata fields are used
4. **Test edge cases**: No results, ambiguous queries
5. **Check citations**: Proper source attribution
6. **Validate ranking**: Higher quality/relevance shown first
7. **Confirm filters**: Department/fleet/standard filters work
8. **Test combinations**: Multiple filters together

The LLM should intelligently choose the right function based on query characteristics and use all available metadata to provide rich, contextual answers.
