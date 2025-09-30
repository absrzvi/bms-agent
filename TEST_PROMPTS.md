# 🧪 BMS Agent Test Prompts - Comprehensive Feature Testing

## 📊 Document Processing & Quality Testing

### Quality Score Testing
```
"Show me high quality documents about business continuity"
"Find documents with the best quality scores"
"Which documents have quality scores above 0.7?"
```

### Multi-Format Support Testing
```
"Find all PDF documents about safety"
"Show me Excel templates for reporting"
"What PowerPoint presentations do we have?"
"Find Word documents about HR processes"
"Show me CSV files in the system"
```

### Document Type Filtering
```
"Search for employee guidelines in PDF format only"
"Find Excel spreadsheets about finance"
"Show me all DOCX files about engineering"
"What PPTX presentations cover training?"
```

---

## 🔍 Search Capabilities Testing

### Semantic Search (Conceptual)
```
"What is business continuity?"
"How do we handle emergencies?"
"What are our safety procedures?"
"Explain the onboarding process"
"What policies cover employee benefits?"
"How do we manage risks?"
```

### Hybrid Search (Keyword + Semantic)
```
"Find BMS-ENGI-FOR-003"
"Show me documents with 'material management' in them"
"Search for 'SharePoint permission' documents"
"Find 'commissioning report' templates"
"Locate 'business continuity response' documents"
```

### Comparison Testing
```
"Compare semantic vs hybrid search for 'IT service management'"
"Show me the difference between search types for 'employee onboarding'"
"Compare results for 'risk assessment' using both methods"
```

---

## 📋 Metadata & Schema Testing

### Chunk-Level Metadata
```
"Find documents with multiple chunks about safety"
"Show me the first chunk of the onboarding document"
"What's the chunk index distribution for HR documents?"
```

### Document Metadata
```
"When was the business continuity document last modified?"
"Show me recently updated documents"
"Find documents modified in September 2025"
"What's the modification date of the IT disaster recovery process?"
```

### Hierarchy Testing
```
"Find parent-child relationships in engineering documents"
"Show me documents with hierarchical structure"
"What's the hierarchy level of safety procedure chunks?"
```

### Processing Version
```
"Show me documents processed with v4.0"
"Find chunks with enhanced processing"
"What processing version was used for HR documents?"
```

---

## 🎯 Context Preservation Testing

### Overlap Testing
```
"Find related chunks about the same topic"
"Show me consecutive chunks from the onboarding document"
"What context is preserved between chunks?"
```

### Sentence Boundaries
```
"Find complete sentences about business continuity"
"Show me properly chunked paragraphs about safety"
"Are sentences split across chunks?"
```

---

## 📊 Qdrant Schema Testing

### Vector Search
```
"Find similar documents to business continuity"
"What documents are semantically related to IT disaster recovery?"
"Show me documents similar to employee onboarding"
```

### Payload Filtering
```
"Find documents of type 'policy_document'"
"Show me 'business_continuity' category documents"
"Filter by document type 'process_document'"
```

### Score Thresholds
```
"Show me only highly relevant results (score > 0.6)"
"Find documents with relevance above 0.5"
"What are the top scoring documents for 'safety'?"
```

---

## 🔧 Advanced Features Testing

### Multi-Concept Queries
```
"Find documents about employee onboarding and probation"
"Show me materials covering both safety and compliance"
"What documents discuss IT security and disaster recovery?"
```

### Scenario-Based Queries
```
"A new employee is starting Monday, what documents do they need?"
"We have an IT incident, what procedures should we follow?"
"How do we handle a business continuity event?"
"What's the process for requesting new equipment?"
```

### Natural Language Queries
```
"I need to know how to request SharePoint access"
"What should I do if I lose my company device?"
"How do I submit an expense report?"
"What's the procedure for taking time off?"
```

### Document Code Queries
```
"Find BMS-BCON-FOR-001"
"Show me BMS-ENGI-FOR-003"
"Locate BMS-PROJ-FOR-033"
"What is BMS-FINA-FOR-006?"
"Find BMS-SERV-PRO-001"
```

---

## 📈 Quality Validation Testing

### RAGAS Metrics
```
"Show me documents with high faithfulness scores"
"Find chunks with good context precision"
"What's the quality score distribution?"
```

### Content Quality
```
"Find documents without fragmented text"
"Show me clean, well-formatted documents"
"What documents have the best readability?"
```

### Preprocessing Validation
```
"Find documents with proper header/footer removal"
"Show me chunks without duplicate content"
"What documents have clean metadata extraction?"
```

---

## 🎨 Specific Document Testing

### Business Continuity
```
"What is our business continuity plan?"
"Show me all business continuity templates"
"Find BMS-BCON documents"
"What scenarios are covered in BC planning?"
```

### HR & Employee Management
```
"What is the employee onboarding process?"
"Show me HR lifecycle documents"
"Find recruitment and selection procedures"
"What's the employee leaving process?"
```

### IT & Technology
```
"What's the IT service management process?"
"Show me IT disaster recovery procedures"
"Find documents about lost or stolen devices"
"What's the IT joiner and leaver process?"
```

### Engineering & Technical
```
"Find engineering commissioning templates"
"Show me PE commissioning reports"
"What engineering forms do we have?"
"Find technical documentation templates"
```

### Finance & Procurement
```
"Show me expense report forms"
"Find credit card expense templates"
"What's the ERP supplier approval process?"
"Show me material management procedures"
```

### Safety & Compliance
```
"What are our safety procedures?"
"Show me risk assessment templates"
"Find compliance requirements"
"What's the incident reporting process?"
```

---

## 🔬 Edge Cases & Stress Testing

### Empty/No Results
```
"Find documents about quantum physics"
"Show me recipes for cooking"
"What documents discuss space travel?"
```

### Ambiguous Queries
```
"Find process"
"Show me documents"
"What is management?"
```

### Very Specific Queries
```
"Find the exact section about probation period duration"
"What's the specific approval threshold for expenses?"
"Show me the contact details for IT support"
```

### Long Queries
```
"I need to understand the complete process for onboarding a new employee including all required documentation, approval workflows, system access requests, equipment provisioning, and training schedules"
```

---

## 📊 Performance Testing

### Batch Queries
```
"Find all documents about: safety, HR, IT, finance, and engineering"
"Show me documents for: onboarding, offboarding, and transfers"
"What do we have on: risk, compliance, and audit?"
```

### Limit Testing
```
"Show me top 3 results for business continuity"
"Find 10 documents about employee management"
"Give me 1 result for IT service management"
```

---

## ✅ Expected Behaviors to Verify

### For Each Query, Check:

1. **Response Time**
   - Semantic search: < 2 seconds
   - Hybrid search: < 3 seconds

2. **Result Quality**
   - Relevance scores > 0.4
   - Correct document names
   - Proper content excerpts

3. **Metadata Presence**
   - Document type shown
   - Quality score displayed
   - Relevance score included
   - Modification date (if available)

4. **Formatting**
   - Clean, readable output
   - Proper document names
   - No truncated content mid-sentence
   - Context preserved

5. **Error Handling**
   - Graceful "no results" messages
   - No crashes on edge cases
   - Helpful suggestions for refinement

---

## 🎯 Success Criteria

### Semantic Search
- ✅ Returns conceptually related documents
- ✅ Handles natural language well
- ✅ Finds documents even with different terminology

### Hybrid Search
- ✅ Finds exact keyword matches
- ✅ Better for document codes
- ✅ Combines semantic + keyword relevance

### Quality
- ✅ All results have quality scores
- ✅ Content is clean and readable
- ✅ No fragmented text or artifacts

### Metadata
- ✅ Document types correctly identified
- ✅ Modification dates present
- ✅ Processing version tracked
- ✅ Chunk indices logical

### Performance
- ✅ 96% accuracy on test queries
- ✅ Fast response times
- ✅ Consistent results

---

## 📝 Testing Checklist

- [ ] Test all semantic search prompts
- [ ] Test all hybrid search prompts
- [ ] Verify multi-format support
- [ ] Check metadata completeness
- [ ] Validate quality scores
- [ ] Test document type filtering
- [ ] Verify context preservation
- [ ] Test edge cases
- [ ] Check error handling
- [ ] Validate performance
- [ ] Test comparison function
- [ ] Verify all 448 documents accessible

---

## 🚀 Quick Test Suite

### 5-Minute Smoke Test
```
1. "What is business continuity?"
2. "Find BMS-ENGI-FOR-003"
3. "Show me employee onboarding process"
4. "What IT service management procedures do we have?"
5. "Compare semantic vs hybrid for 'material management'"
```

### 15-Minute Comprehensive Test
```
1. All 5 smoke tests above
2. "Find all PDF documents about safety"
3. "Show me documents with quality score > 0.7"
4. "What documents were modified in September 2025?"
5. "Find documents of type 'business_continuity'"
6. "Show me Excel templates"
7. "What's the employee leaving process?"
8. "Find risk assessment documents"
9. "Show me IT disaster recovery procedures"
10. "What engineering forms do we have?"
```

---

**Use these prompts to thoroughly test all features of your 96% accuracy BMS Agent!** 🎯✨
