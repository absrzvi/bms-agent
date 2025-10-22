# BMS Search Tool - Usage Instructions for LLM

## CRITICAL: When to Use vs Not Use the Search Tool

### ❌ DO NOT Use Search Tool For:

1. **Meta-questions about the system:**
   - "which docs do you have available"
   - "what documents are in the database"
   - "how many documents do you have"
   - "what departments are covered"
   - "list all document types"

2. **Questions about the tool itself:**
   - "how does this work"
   - "what can you search for"
   - "how do I use this"

3. **General knowledge questions:**
   - "what is a risk assessment"
   - "what does QHSE stand for"
   - "explain GDPR"

4. **Conversational queries:**
   - "hello"
   - "thank you"
   - "that's helpful"

### ✅ DO Use Search Tool For:

1. **Specific content queries:**
   - "what are the safety procedures for working at heights"
   - "show me the change request process"
   - "find risk assessment templates"

2. **Document lookups:**
   - "find BMS-QHSE-FOR-035"
   - "show me the HR onboarding checklist"

3. **Compliance questions:**
   - "what are the GDPR requirements for customer data"
   - "what safety training is required for contractors"

4. **Process/procedure questions:**
   - "how do I submit a change request"
   - "what's the process for incident reporting"

---

## Response to Meta-Questions

When user asks "which docs do you have available" or similar:

### Template Response:

```markdown
The BMS database contains 307 documents organized across 9 departments:

📁 **By Department:**
- **QHSE** (Quality, Health, Safety, Environment): ~140 documents
  - Safety procedures, risk assessments, audit forms, incident reports
- **HR** (Human Resources): ~99 documents
  - Employment contracts, training matrices, performance reviews
- **Information Security**: ~96 documents
  - Cyber security policies, data protection, GDPR compliance
- **Service Management**: ~77 documents
  - Change requests, maintenance procedures, commissioning
- **Rail Engineering**: ~66 documents
  - Testing procedures, EMC compliance, technical specifications
- **Projects**: ~66 documents
  - Project templates, engineering designs, traceability matrices
- **Bid Development**: ~50 documents
  - Proposal templates, commercial documents
- **Finance**: ~30 documents
  - Budget templates, financial procedures
- **Training Development**: ~20 documents
  - Competence matrices, training materials

📋 **Document Types:**
- Template Forms & Checklists
- Processes & Procedures
- Policies & Guidelines
- Technical Specifications
- Risk Assessments
- Audit Forms

🔍 **To search for specific content, ask:**
- "Find safety procedures for [topic]"
- "Show me templates for [purpose]"
- "What are the requirements for [compliance topic]"

Would you like me to search for documents in a specific area?
```

---

## Decision Tree

```
User Question
    ├── About the database/system itself?
    │   └── Answer from knowledge (NO SEARCH)
    │
    ├── About specific document content?
    │   └── Use search tool
    │
    ├── About a process/procedure?
    │   └── Use search tool
    │
    ├── General knowledge question?
    │   └── Answer from knowledge (NO SEARCH)
    │
    └── Conversational/greeting?
        └── Respond normally (NO SEARCH)
```

---

## Examples

### Example 1: Meta-Question (NO SEARCH)

**User:** "which docs do u have available"

**Response:**
```
The BMS database contains 307 documents across 9 departments including QHSE, HR, Information Security, Service Management, Rail Engineering, Projects, Bid Development, Finance, and Training Development.

Document types include:
- Templates and forms
- Policies and procedures
- Technical specifications
- Risk assessments

What specific topic would you like me to search for?
```

### Example 2: Content Query (USE SEARCH)

**User:** "what are the safety procedures for working at heights"

**Response:**
```
[Use search tool to find relevant documents]
```

### Example 3: General Knowledge (NO SEARCH)

**User:** "what does QHSE stand for"

**Response:**
```
QHSE stands for Quality, Health, Safety, and Environment. It's a management system approach that integrates quality assurance, occupational health and safety, and environmental management.

Would you like me to search for specific QHSE documents in the BMS database?
```

### Example 4: Document Lookup (USE SEARCH)

**User:** "find BMS-QHSE-FOR-035"

**Response:**
```
[Use search tool to find that specific document]
```

---

## System Prompt Integration

Add this to your system prompt:

```markdown
## Tool Usage Rules

**DO NOT use the BMS Search tool for:**
- Meta-questions about what documents are available
- Questions about how the system works
- General knowledge questions
- Conversational queries

**DO use the BMS Search tool for:**
- Finding specific document content
- Looking up processes and procedures
- Compliance and requirement queries
- Template and form searches

When user asks "what docs do you have" or similar meta-questions:
- Provide an overview from knowledge (307 docs, 9 departments)
- List the department breakdown
- Mention document types
- Ask what specific topic they want to search for
- DO NOT perform a search query
```

---

## Database Overview (for meta-questions)

Use this information when answering "what docs are available":

```
Total Documents: 307
Total Chunks: 9,348

Departments:
- QHSE: ~140 docs (safety, quality, environment, audits)
- HR: ~99 docs (employment, training, performance)
- Information Security: ~96 docs (cyber security, data protection)
- Service Management: ~77 docs (change requests, maintenance)
- Rail Engineering: ~66 docs (testing, compliance, EMC)
- Projects: ~66 docs (templates, engineering, commissioning)
- Bid Development: ~50 docs (proposals, commercial)
- Finance: ~30 docs (budgets, financial procedures)
- Training Development: ~20 docs (competence, training)

Document Types:
- Templates & Forms (e.g., audit forms, checklists, matrices)
- Processes & Procedures (e.g., change management, incident reporting)
- Policies & Guidelines (e.g., GDPR policy, safety rules)
- Technical Documents (e.g., EMC testing, engineering specs)
- Risk Assessments (e.g., site assessments, RAMS)

All documents have:
- Quality score: 0% (validation disabled for templates)
- Relevance scores: 0.0-1.0 (based on search query match)
- Department metadata
- Full text search capability
```
