# Quick Test Prompts - BMS Agent Enhanced Search

## 🚀 Quick Function Tests (Copy & Paste)

### 1. search_semantic() - Conceptual
```
What is business continuity and how does it apply to railway operations?
```

### 2. search_hybrid() - Specific Terms
```
What does BMS-HUMR-POL-010 say about notification requirements?
```

### 3. search_by_document_type() - Format Filter
```
Show me Excel spreadsheets about employee records
```

### 4. search_by_fleet_type() - Railway Fleet
```
What are the maintenance procedures for Railjet trains?
```

### 5. search_by_standard() - Compliance
```
What are the EN50155 compliance requirements for electronic equipment?
```

### 6. search_by_department() - Department Filter
```
What HR policies exist for employee leave and absences?
```

### 7. search_with_context() - Detailed Context
```
Explain the complete process for incident reporting and escalation
```

### 8. search_high_quality() - Quality Filter
```
What are the official safety procedures for emergency situations? I need verified information.
```

### 9. compare_search_types() - Comparison
```
Show me different ways to find information about network architecture
```

### 10. search_documents() - Advanced Custom
```
Find high-quality PDF documents from the Engineering department about network components
```

### 11. get_api_status() - Health Check
```
Is the BMS search system working properly?
```

---

## 🎯 Metadata Display Test

**Test All Metadata Fields:**
```
Search for "BMS-HUMR-POL-010" and show me all available metadata including department, quality score, keywords, entities, technical terms, and any railway-specific information.
```

**Expected to see:**
- Document name, type, department
- Quality & relevance scores
- Keywords, entities, technical terms
- Contextual description
- Fleet type, standards, network components (if applicable)

---

## 🔥 Advanced Multi-Step Scenarios

### Scenario 1: Progressive Refinement
```
1. What are the safety procedures?
2. Specifically for Railjet trains
3. According to EN50155 standards
4. I need the official verified version
```

### Scenario 2: Department Investigation
```
1. What policies does HR have?
2. What about Engineering?
3. Show me only high-quality ones
```

### Scenario 3: Comprehensive Research
```
1. Tell me about material management
2. Show me different search approaches
3. I need detailed context
4. Filter by Engineering department
```

---

## ⚡ One-Liner Tests

**Keyword Matching:**
```
BMS-ENGI-FOR-003 material requisition
```

**Entity Recognition:**
```
Railjet EN50155 compliance
```

**Quality Filtering:**
```
Official safety procedures verified only
```

**Department Context:**
```
HUMR sick leave policy
```

**Fleet Operations:**
```
Cityjet maintenance schedule
```

**Standards Compliance:**
```
EN45545 fire safety requirements
```

**Technical Terms:**
```
Network architecture specifications
```

**Contextual Search:**
```
Detailed onboarding process steps
```

---

## 🧪 Edge Case Tests

**No Results:**
```
Find information about quantum computing in railways
```

**Ambiguous Query:**
```
Who handles employee IT access requests?
```

**Multiple Matches:**
```
What maintenance procedures apply to all train types?
```

**Low Quality:**
```
Any information about [obscure internal process]
```

---

## ✅ Success Checklist

Test each and verify:

- [ ] Correct function chosen for query type
- [ ] Metadata displayed (keywords, entities, quality)
- [ ] Proper citations with document names
- [ ] Confidence levels based on quality scores
- [ ] Railway context (fleets, standards, departments)
- [ ] Enhanced ranking visible in results
- [ ] Filters working correctly
- [ ] Graceful handling of no results

---

## 📊 Expected Response Format

Good response should include:

```
According to [Document Name] ([Department], Quality: [Score]):
[Answer to question]

Source: [Document Name] | Type: [Type] | Relevance: [Score]
Keywords: [keyword1, keyword2, ...]
Technical Terms: [term1, term2, ...]
[Additional metadata as relevant]
```

---

## 🎓 Testing Tips

1. **Start Simple**: Test basic functions individually
2. **Add Complexity**: Combine filters and functions
3. **Check Metadata**: Verify all fields are used
4. **Test Ranking**: Higher scores should appear first
5. **Verify Citations**: Sources properly attributed
6. **Edge Cases**: Test with unusual queries
7. **Multi-Step**: Test progressive refinement
8. **Cross-Reference**: Compare different search types

---

## 🚨 Common Issues to Check

- [ ] Are keywords from metadata being displayed?
- [ ] Are entities being recognized and matched?
- [ ] Are technical terms being highlighted?
- [ ] Is quality boost being applied?
- [ ] Are department filters working?
- [ ] Are fleet type filters working?
- [ ] Are standard filters working?
- [ ] Is contextual information being shown?

---

## 💡 Pro Tips

**For Best Results:**
- Use specific document codes when known
- Mention department for targeted search
- Request "verified" or "official" for high-quality filter
- Ask for "detailed" or "complete" for contextual search
- Specify fleet type or standard when relevant
- Use "compare" to see different search approaches

**Example Pro Query:**
```
Find the official verified EN50155 compliance requirements for Railjet from the Engineering department, with detailed context and all technical terms.
```

This should trigger:
- `search_by_fleet_type()` or `search_by_standard()`
- Quality filtering (0.85+)
- Department filter (ENGI)
- Contextual search
- Full metadata display
