# Quality Scores Explanation

## Why All Documents Show 0% Quality Score

### Summary
**This is intentional, not a bug.** Quality validation is disabled to allow template and form documents to be indexed.

### Technical Details

#### Configuration (batch_ingest_by_department.py)
```python
enable_quality_validation=False  # Disabled to allow templates with minimal text
min_quality_score=0.0           # Accept all content
```

#### Reason
The BMS document library consists primarily of:
- **Templates** (forms, matrices, checklists)
- **Procedural documents** (minimal text, mostly structure)
- **Excel spreadsheets** (tables, headers, formulas)
- **PDF forms** (form fields, signatures)

These documents naturally have:
- Short text content
- Structural elements (tables, headers)
- Minimal narrative text
- High value despite low "quality" metrics

#### What Quality Validation Does When Enabled

Quality validation calculates:
1. **Faithfulness** - How well chunk represents original document
2. **Answer Relevancy** - Chunk's usefulness for answering questions
3. **Context Precision** - How well contextual information is preserved
4. **Semantic Similarity** - Coherence with surrounding content

**For templates and forms, these metrics would be very low**, causing useful documents to be rejected.

### Examples from the Database

```
Document: BMS-TDEV-FOR-002 CSD Competence Matrix (Belgium).xlsx
Content: 400 chars (mostly table headers)
Quality: 0.0 (validation disabled)
Status: ✅ Indexed and searchable

Document: BMS-HUMR-FOR-037 Employee Reference Form - esig.pdf
Content: 97 chars (form fields)
Quality: 0.0 (validation disabled)
Status: ✅ Indexed and searchable

Document: BMS-PROJ-FOR-024 Risk register Template.xlsx
Content: 400 chars (spreadsheet structure)
Quality: 0.0 (validation disabled)
Status: ✅ Indexed and searchable
```

### What This Means for Search Results

When using the BMS search tool, you will see:
- ✅ **Relevance scores** (0.0 - 1.0) → Measures how well the document matches your query
- ⚠️ **Quality scores** (always 0.0) → Not calculated for this document set

**Use relevance scores to judge result quality, not quality scores.**

### Alternative: Enable Quality Validation

If you want quality scores calculated:

1. Update `batch_ingest_by_department.py`:
```python
enable_quality_validation=True
min_quality_score=30.0  # Low threshold for templates
```

2. Re-ingest all documents (will take longer)
3. Expect some template documents to be rejected

**Trade-offs:**
- ✅ Get quality metrics
- ❌ Slower ingestion
- ❌ Some useful templates may be rejected
- ❌ Not recommended for template-heavy document sets

### For LLM Responses

When reporting search results:
- Always show quality_score as 0% (don't hallucinate higher values)
- Focus on relevance_score for result quality
- Mention that quality validation is disabled for this document set
- Use exact document names from search results

### Verification

Check database quality scores:
```python
from qdrant_client import QdrantClient

client = QdrantClient(url="http://localhost:6333")
records, _ = client.scroll(
    collection_name="nomad_bms_documents",
    limit=10,
    with_payload=True
)

for r in records:
    print(f"Quality: {r.payload.get('quality_score', 'N/A')}")
```

Expected output: All scores = 0.0

---

## Summary

- **Quality scores are 0% by design**
- Template documents don't need quality validation
- **Relevance scores indicate search result quality**
- LLM should report actual 0% scores, not hallucinate higher values
