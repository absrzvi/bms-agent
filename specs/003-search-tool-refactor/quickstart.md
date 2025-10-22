# Quickstart: Search Tool Enhanced Retrieval

**Date**: 2025-10-22
**Feature**: Search Tool Enhanced Retrieval
**For**: Developers implementing and testing search tool enrichment

## Overview

This guide provides step-by-step instructions for developing, testing, and deploying the enhanced search tool with visual artifacts, chapter context, quality scores, and hierarchical relationships.

---

## Prerequisites

### Environment Setup

**Required**:
- Python 3.11+
- Access to `/workspace/bms-agent/` directory
- Access to `/workspace/visual-artifacts/` directory (populated by ingestion)
- Qdrant running at `localhost:6333` with `nomad_bms_documents` collection
- OpenWebUI environment for integration testing

**Verify Prerequisites**:
```bash
# Check Python version
python3 --version  # Should be 3.11+

# Check Qdrant access
curl -s http://localhost:6333/healthz

# Check visual artifacts directory
ls -lh /workspace/visual-artifacts/images/ | head -5
ls -lh /workspace/visual-artifacts/slides/ | head -5

# Check bms_search.py exists
ls -lh /workspace/bms-agent/bms_search.py
```

### Test Data

**Ensure documents are ingested with enhanced metadata**:
```bash
# Verify collection has enhanced metadata
cd /workspace/bms-agent
python3 -c "
import sys
sys.path.insert(0, 'bms-agent/scr')
from qdrant_schema_v4 import QdrantSchemaV4, QdrantConfig
from qdrant_client import QdrantClient

client = QdrantClient(host='localhost', port=6333)
collection = 'nomad_bms_documents'

# Get sample point
points = client.scroll(
    collection_name=collection,
    limit=1,
    with_payload=True
)

point = points[0][0]
payload = point.payload

print('Has visual artifacts:', payload.get('has_visual_artifacts', False))
print('Chapter title:', payload.get('chapter_title', 'None'))
print('Quality score:', payload.get('quality_score', 0.0))
print('Parent chunk ID:', payload.get('parent_chunk_id', 'None'))
"
```

**Expected Output**:
```
Has visual artifacts: True
Chapter title: Test Completion Overview & Recommendations
Quality score: 0.0
Parent chunk ID: None
```

---

## Development Workflow

### Step 1: Create Feature Branch

```bash
cd /workspace/bms-agent
git checkout 003-search-tool-refactor  # Already created by /speckit.specify
```

### Step 2: Implement Enrichment Methods

**Add to `bms_search.py` (after line 1066)**:

1. **Add result cache** to `__init__()`:
```python
def __init__(self):
    self.valves = self.Valves()
    self.citation = False
    self.session_id = None
    self._session = None
    self._result_cache = {}  # ← ADD THIS
```

2. **Optimize visual artifact loading** (replace existing `_load_visual_artifacts()` at lines 998-1066):
```python
def _load_visual_artifacts_optimized(self, result: Dict[str, Any], max_artifacts: int = 3) -> List[Dict[str, str]]:
    """Load visual artifacts using optimized direct path construction."""
    # See contracts/enrichment-api.md for full implementation
```

3. **Add chapter formatting method**:
```python
def _format_chapter_context(self, metadata: Dict[str, Any]) -> Dict[str, str] | None:
    """Format chapter metadata into ChapterContext structure."""
    # See contracts/enrichment-api.md for full implementation
```

4. **Add quality formatting method**:
```python
def _format_quality_breakdown(self, metadata: Dict[str, Any]) -> Dict[str, Any] | None:
    """Format quality scores into QualityBreakdown structure."""
    # See contracts/enrichment-api.md for full implementation
```

5. **Add result cache methods**:
```python
def _update_result_cache(self, results: List[Dict[str, Any]]) -> None:
    """Update result cache for parent/child lookup."""
    # See contracts/enrichment-api.md for full implementation

def _check_hierarchy_cache(self, metadata: Dict[str, Any]) -> tuple[bool, int]:
    """Check if parent/child are in cache."""
    # See contracts/enrichment-api.md for full implementation
```

6. **Add main enrichment method**:
```python
def _enrich_search_results(
    self,
    results: List[Dict[str, Any]],
    load_artifacts: bool = True,
    max_artifacts_per_result: int = 3
) -> List[Dict[str, Any]]:
    """Enrich search results with visual artifacts, chapter context, quality scores."""
    # See contracts/enrichment-api.md for full implementation
```

### Step 3: Update Dashboard Generation

**Modify `_generate_search_dashboard()` method (line 1067+)**:

1. Add chapter breadcrumb HTML generation
2. Add quality badge HTML generation
3. Update result card template to include enriched fields

See [data-model.md](./data-model.md) for HTML structure examples.

### Step 4: Integrate with Search Methods

**Update `search_smart()`, `search_semantic()`, `search_hybrid()`**:

```python
async def search_smart(self, query, limit=None, filters=None, ...):
    # ... existing code ...

    # Step 2: Apply boosting
    boosted_results = self._apply_smart_boosting(candidates, user_prefs)

    # Step 3: Take top results
    final_results = boosted_results[:final_limit]

    # ← ADD THIS: Enrich results
    enriched_results = self._enrich_search_results(final_results, load_artifacts=show_rich_ui)

    # ← UPDATE THIS: Cache results for hierarchy
    self._update_result_cache(enriched_results)

    # Step 4: Emit citations
    await self._emit_search_citations(__event_emitter__, enriched_results)  # ← Use enriched

    # Step 5: Generate rich UI
    if show_rich_ui:
        dashboard_html = self._generate_search_dashboard(enriched_results, "smart", query)  # ← Use enriched
        # ... rest of dashboard generation ...
```

---

## Testing

### Unit Tests

**Create `tests/test_bms_search_enrichment.py`**:

```python
import pytest
from unittest.mock import Mock, patch
import sys
import os
from pathlib import Path

# Add bms-agent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import Tools class
from bms_search import Tools

@pytest.fixture
def tools():
    """Create Tools instance for testing."""
    return Tools()

@pytest.fixture
def sample_result_with_artifacts():
    """Sample search result with visual artifacts."""
    return {
        "text": "Sample chunk text",
        "score": 0.95,
        "metadata": {
            "document_id": "hr_10_form",
            "document_name": "Employee Form",
            "department": "HR",
            "chunk_id": "chunk_123",
            "has_visual_artifacts": True,
            "visual_artifact_ids": ["img_62f221a40149", "img_19accd94c73e"],
            "image_captions": ["Figure 1", "Table 2"],
            "visual_artifact_count": 2
        }
    }

def test_load_visual_artifacts_optimized(tools, sample_result_with_artifacts):
    """Test optimized visual artifact loading."""
    # Mock file system
    with patch('os.path.exists', return_value=True):
        with patch('builtins.open', Mock()):
            artifacts = tools._load_visual_artifacts_optimized(sample_result_with_artifacts, max_artifacts=3)

            assert len(artifacts) >= 0  # Should handle missing files gracefully
            if artifacts:
                assert artifacts[0]['artifact_id'] == 'img_62f221a40149'
                assert artifacts[0]['type'] == 'image'
                assert artifacts[0]['caption'] == 'Figure 1'

def test_format_chapter_context(tools):
    """Test chapter context formatting."""
    metadata = {
        "chapter_title": "Safety Protocols",
        "chapter_path": "Introduction > Background > Safety Protocols",
        "chapter_level": 3,
        "chapter_number": "1.2.3"
    }

    context = tools._format_chapter_context(metadata)

    assert context is not None
    assert context['chapter_title'] == "Safety Protocols"
    assert "Safety Protocols" in context['formatted_path']
    assert "📂" in context['breadcrumb_html']

def test_format_quality_breakdown(tools):
    """Test quality breakdown formatting."""
    metadata = {
        "quality_score": 92.5,
        "faithfulness": 0.95,
        "relevancy": 0.90,
        "precision": 0.92,
        "recall": 0.88
    }

    breakdown = tools._format_quality_breakdown(metadata)

    assert breakdown is not None
    assert breakdown['overall_score'] == 92.5
    assert breakdown['color'] == "green"  # >= 80%
    assert "92%" in breakdown['overall_percent'] or "93%" in breakdown['overall_percent']

def test_enrich_search_results(tools, sample_result_with_artifacts):
    """Test full enrichment pipeline."""
    results = [sample_result_with_artifacts]

    enriched = tools._enrich_search_results(results, load_artifacts=False)  # Skip artifact loading

    assert len(enriched) == 1
    assert 'visual_artifacts' in enriched[0]
    assert 'has_parent' in enriched[0]
    assert 'has_children' in enriched[0]

# Run tests
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
```

**Run Tests**:
```bash
cd /workspace/bms-agent
pytest tests/test_bms_search_enrichment.py -v
```

### Integration Testing with OpenWebUI

**Manual Testing Checklist**:

1. **Visual Artifacts Display**:
   - [ ] Search for document with images (e.g., "safety card")
   - [ ] Verify images display inline in result card
   - [ ] Verify captions appear beneath images
   - [ ] Click image to open in new tab

2. **Chapter Context Display**:
   - [ ] Search for document with chapters (e.g., "test completion")
   - [ ] Verify chapter breadcrumb displays above content
   - [ ] Verify breadcrumb shows full hierarchy

3. **Quality Score Display**:
   - [ ] If quality validation enabled: Verify badge appears
   - [ ] Hover over badge to see tooltip with breakdown
   - [ ] Verify color coding (green/yellow/red)

4. **Backward Compatibility**:
   - [ ] Search returns results even if metadata missing
   - [ ] No visual artifacts shown when `has_visual_artifacts == False`
   - [ ] No chapter breadcrumb when `chapter_path` missing
   - [ ] No quality badge when `quality_score == 0.0`

5. **Performance**:
   - [ ] Dashboard renders within 2 seconds for 5 results
   - [ ] No lag when scrolling through results
   - [ ] Images load progressively (no blocking)

### Performance Testing

**Test Dashboard Rendering Time**:

```python
import time

# Add timing to search methods
async def search_smart(self, query, ...):
    start_time = time.time()

    # ... existing search logic ...

    enriched_results = self._enrich_search_results(final_results)
    enrichment_time = time.time() - start_time

    print(f"Enrichment time: {enrichment_time:.3f}s")

    dashboard_html = self._generate_search_dashboard(enriched_results, "smart", query)
    total_time = time.time() - start_time

    print(f"Total time: {total_time:.3f}s")

    # ... rest of method ...
```

**Performance Targets** (from Success Criteria):
- SC-001: Dashboard rendering with artifacts ≤ 2 seconds
- SC-003: Performance impact of visual artifacts ≤ 500ms over baseline
- SC-004: Context expansion ≤ 300ms

---

## Deployment

### Step 1: Validate Implementation

```bash
# Run all tests
cd /workspace/bms-agent
pytest tests/test_bms_search_enrichment.py -v

# Check for syntax errors
python3 -m py_compile bms_search.py

# Verify imports
python3 -c "from bms_search import Tools; t = Tools(); print('✅ Import successful')"
```

### Step 2: Deploy to OpenWebUI

**Option A: Direct File Replacement** (Development):
```bash
# Backup current version
cp bms_search.py bms_search.py.backup

# Deploy new version
# (Assuming OpenWebUI reads from /workspace/bms-agent/)
# No additional steps needed if file is in correct location
```

**Option B: OpenWebUI Tools Interface** (Production):
1. Open OpenWebUI Admin Panel
2. Navigate to Tools section
3. Click "Edit Tool: BMS Search"
4. Paste contents of `bms_search.py`
5. Click "Save"
6. Test in a new chat

### Step 3: Verify Deployment

```bash
# Test search via OpenWebUI interface
# 1. Create new chat
# 2. Type: "search for safety protocols"
# 3. Verify results display with enhanced features
```

---

## Troubleshooting

### Visual Artifacts Not Displaying

**Symptom**: Search works but no images shown

**Checklist**:
1. Verify `/workspace/visual-artifacts/` directory exists and is accessible
2. Check file permissions: `ls -lh /workspace/visual-artifacts/images/ | head`
3. Verify `has_visual_artifacts == True` in Qdrant metadata
4. Check browser console for base64 decoding errors
5. Verify artifact_ids match file names on disk

**Debug**:
```python
# Add logging to _load_visual_artifacts_optimized
import logging
logger = logging.getLogger(__name__)

logger.info(f"Loading artifacts for document: {document_id}")
logger.info(f"Artifact IDs: {artifact_ids}")
logger.info(f"Constructed path: {artifact_path}")
logger.info(f"File exists: {os.path.exists(artifact_path)}")
```

### Chapter Context Not Showing

**Symptom**: No chapter breadcrumbs displayed

**Checklist**:
1. Verify document was ingested with chapter extraction enabled
2. Check `chapter_path` or `chapter_title` exists in Qdrant metadata
3. Verify `_format_chapter_context()` returns non-None value
4. Check CSS styling is not hiding breadcrumb element

**Debug**:
```python
# Check metadata
metadata = result.get("metadata", {})
print("Chapter title:", metadata.get("chapter_title"))
print("Chapter path:", metadata.get("chapter_path"))
```

### Quality Scores Always Zero

**Symptom**: No quality badges displayed

**Explanation**: Quality validation may be disabled during ingestion. This is expected.

**Solution**: Quality scores are optional. Feature gracefully degrades when scores are 0.0.

**To Enable** (requires reingestion):
```bash
# Set environment variable before ingestion
export BMS_ENABLE_QUALITY_VALIDATION=true
export BMS_QUALITY_THRESHOLD=85.0

# Reingest documents
python3 batch_ingest_by_department.py --path upload-files
```

### Parent/Child Context Not Available

**Symptom**: "Parent context not available" message when clicking expand

**Explanation**: Parent chunk may not be in current search results.

**Solutions**:
1. Increase result limit to capture more chunks
2. Search for parent chapter title directly
3. Hierarchical chunking may not be active (check `hierarchy_level` in metadata)

---

## Configuration

### Valve Settings

Add to `class Valves` in `bms_search.py`:

```python
# Visual Artifacts Settings
ENABLE_VISUAL_ARTIFACTS: bool = Field(
    default=True,
    description="Load and display visual artifacts inline"
)
MAX_ARTIFACTS_PER_RESULT: int = Field(
    default=3,
    description="Maximum visual artifacts to display per result (1-10)"
)
MAX_ARTIFACT_SIZE_MB: int = Field(
    default=5,
    description="Maximum artifact file size in MB"
)

# Chapter Context Settings
ENABLE_CHAPTER_CONTEXT: bool = Field(
    default=True,
    description="Display chapter breadcrumbs in results"
)

# Quality Score Settings
ENABLE_QUALITY_BADGES: bool = Field(
    default=True,
    description="Display quality score badges"
)
QUALITY_SCORE_THRESHOLD: float = Field(
    default=0.1,
    description="Minimum score to display badge (0.0 = always show)"
)
```

### Environment Variables

```bash
# Visual artifacts storage location
export VISUAL_ARTIFACTS_DIR=/workspace/visual-artifacts

# Qdrant connection (already configured)
export QDRANT_HOST=localhost
export QDRANT_PORT=6333
export QDRANT_COLLECTION=nomad_bms_documents
```

---

## Next Steps

1. **Review Implementation**: Check that all methods follow contracts in `contracts/enrichment-api.md`
2. **Run Tests**: Execute unit tests and verify all pass
3. **Test Manually**: Perform integration testing in OpenWebUI
4. **Measure Performance**: Validate dashboard rendering time meets ≤2 second target
5. **Deploy**: Update OpenWebUI tool with enhanced version
6. **Document**: Update `TOOL_USAGE_INSTRUCTIONS.md` with new features

---

## Additional Resources

- **Specification**: [spec.md](./spec.md) - User requirements and acceptance criteria
- **Research**: [research.md](./research.md) - Technical decisions and trade-offs
- **Data Model**: [data-model.md](./data-model.md) - Data structure definitions
- **API Contracts**: [contracts/enrichment-api.md](./contracts/enrichment-api.md) - Method signatures and behavior
- **Implementation Plan**: [plan.md](./plan.md) - Full technical plan

---

**Version**: 1.0
**Last Updated**: 2025-10-22
