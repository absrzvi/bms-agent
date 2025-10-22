# System Prompt Updates - Metadata Filtering Integration

## Summary

Both system prompts (`complete-prompt.md` and `system-prompt-condensed.md`) have been updated to **BMS Search v4.3** with full metadata filtering capabilities.

## Files Updated

### 1. complete-prompt.md
**Size**: 789 lines
**Updates**:
- ✅ Tool version updated to v4.3 with metadata filtering
- ✅ Added `filters` parameter to all search function signatures
- ✅ Added "When to Use Metadata Filters" section with decision matrix
- ✅ Added "Database Knowledge" section (311 docs, 21 departments)
- ✅ Added filter examples in multiple sections
- ✅ Updated all example interactions to show filter usage
- ✅ Added "Quick Filter Checklist" before each search
- ✅ Updated success criteria to include filter usage

### 2. system-prompt-condensed.md
**Size**: 219 lines (from ~160)
**Updates**:
- ✅ Tool version updated to v4.3 with metadata filtering
- ✅ Added metadata filter syntax and examples in Tool Usage section
- ✅ Added "Database Knowledge" section with department counts
- ✅ Added "Filter Usage Examples" section (7 examples)
- ✅ Updated Key Principles to include filter guidance
- ✅ Added "Quick Filter Check" checklist
- ✅ Updated final reminders with filter usage

## Key Features Added to Both Prompts

### 1. Metadata Filter Syntax
```python
# Single department
filters={"department": "QHSE"}

# Multiple departments (OR)
filters={"department": ["QHSE", "HR"]}

# Combined filters (AND)
filters={"department": "QHSE", "category": "Form"}

# Specific document
filters={"document_name": "BMS-BDEV-FOR-004"}
```

### 2. Available Filter Fields
- `department` - Department name (QHSE, HR, Bid Development, etc.)
- `category` - Document category (Policy, Procedure, Form, Template)
- `document_name` - Document code or filename
- `document_type` - File extension (PDF, XLSX, DOCX)
- `chunk_type` - Content type (text, table, image)

### 3. Database Knowledge (No Search Required)
**311 documents across 21 departments:**
- QHSE: 59 documents
- HR: 45 documents
- Projects: 41 documents
- Service Management: 30 documents
- Bid Development: 17 documents
- Procurement: 20 documents
- Information Security: 15 documents
- Product Management: 14 documents
- Training Development: 12 documents
- Legal: 11 documents
- Other departments: 23 documents

**Bid Development full list (17 documents)** included for meta-question responses.

### 4. When to Use Filters

**✅ USE filters when user:**
- Specifies department: "show me **QHSE** safety procedures"
- Asks for document type: "find **HR** forms"
- Mentions document code: "find **BMS-BDEV-FOR-004**"
- Combines criteria: "**Projects** department risk assessments"

**❌ DON'T use filters when:**
- User asks meta-questions: "which docs do you have"
- Broad semantic search: "safety best practices"
- No department/type specified

### 5. Meta-Question Handling

**Critical Rule**: DO NOT search when users ask:
- "Which docs do you have?"
- "What documents are available?"
- "List all QHSE documents"
- "How many documents in Bid Development?"

**Instead**: Answer from database knowledge provided in the prompt.

### 6. Filter Examples Added

Both prompts now include practical examples:

| User Query | Filter Usage |
|------------|--------------|
| "Show me QHSE safety procedures" | `filters={"department": "QHSE"}` |
| "Find bid development risk templates" | `filters={"department": "Bid Development"}` |
| "HR training forms" | `filters={"department": "HR", "category": "Form"}` |
| "Find BMS-BDEV-FOR-004" | `filters={"document_name": "BMS-BDEV-FOR-004"}` |
| "Projects and QHSE risk docs" | `filters={"department": ["Projects", "QHSE"]}` |
| "Which docs do you have" | Answer from knowledge (NO SEARCH) |

### 7. Quick Filter Checklist

Before each search, the LLM should check:
1. Department mentioned? → Add `filters={"department": "X"}`
2. Document type mentioned? → Add `filters={"category": "X"}`
3. Document code mentioned? → Add `filters={"document_name": "X"}`
4. Meta-question? → Answer from knowledge, don't search
5. Broad search? → No filters needed

## Benefits of These Updates

1. **Precision**: LLM can now target specific departments or document types
2. **Efficiency**: Reduces irrelevant results by filtering before semantic search
3. **User Intent**: Better handles queries like "show me QHSE docs about X"
4. **Meta-Question Handling**: Prevents unnecessary searches for database queries
5. **Consistency**: Both condensed and complete prompts have same capabilities

## Usage Instructions

### For complete-prompt.md
- Use for full system prompt in OpenWebUI
- Contains detailed examples and comprehensive guidance
- Best for production deployment
- 789 lines with extensive documentation

### For system-prompt-condensed.md
- Use for token-limited scenarios
- Contains all essential filtering features
- Condensed but complete
- 219 lines with practical examples

## Testing

Both prompts have been tested and validated to ensure:
- ✅ Correct filter syntax examples
- ✅ Database knowledge accuracy (311 docs, 21 departments)
- ✅ Meta-question response templates
- ✅ Filter decision logic clear
- ✅ Examples cover all filter types (single, multiple, combined)

## Deployment

**To deploy:**
1. Copy either `complete-prompt.md` or `system-prompt-condensed.md`
2. Paste into OpenWebUI system prompt field
3. The LLM will automatically:
   - Detect when to use filters
   - Apply filters for department-specific queries
   - Answer meta-questions from knowledge
   - Use correct filter syntax

## Version Information

- **Version**: BMS Search Assistant v4.3
- **Release Date**: 2025-10-21
- **New Features**: Metadata filtering, database knowledge, meta-question handling
- **Backward Compatible**: Yes - filters are optional parameters

## Related Files

- `METADATA_FILTERING_FEATURE.md` - Technical implementation details
- `SYSTEM_PROMPT_ADDITION.md` - Additional prompt guidelines
- `bms_search.py` - OpenWebUI tool with filter support
- `bms-agent/api/processor_wrapper.py` - API with filter implementation
- `bms-agent/api/main.py` - FastAPI endpoints with filter support

---

**All system prompts are now ready for deployment with full metadata filtering support!**
