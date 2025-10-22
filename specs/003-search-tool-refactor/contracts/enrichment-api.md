# Internal API Contract: Search Result Enrichment

**Date**: 2025-10-22
**Feature**: Search Tool Enhanced Retrieval
**Scope**: Internal methods within `bms_search.py`

## Overview

This document defines the internal API contracts for methods that enrich search results with visual artifacts, chapter context, quality scores, and hierarchical relationships. These are private methods within the `Tools` class and are not exposed externally.

---

## Method: `_enrich_search_results()`

Enriches a list of search results with visual artifacts, chapter context, and quality scores.

### Signature

```python
def _enrich_search_results(
    self,
    results: List[Dict[str, Any]],
    load_artifacts: bool = True,
    max_artifacts_per_result: int = 3
) -> List[Dict[str, Any]]:
    """
    Enrich search results with visual artifacts, chapter context, and quality scores.

    Args:
        results: List of search results from Qdrant API
        load_artifacts: Whether to load visual artifacts from disk (default: True)
        max_artifacts_per_result: Maximum artifacts to load per result (default: 3)

    Returns:
        List of enriched search results with additional fields:
        - visual_artifacts: List[VisualArtifact]
        - chapter_context: ChapterContext | None
        - quality_breakdown: QualityBreakdown | None
        - has_parent: bool
        - has_children: bool
        - parent_in_cache: bool
        - children_in_cache: int
    """
```

### Behavior

**Input Processing**:
1. Accepts list of base search results from Qdrant API
2. Each result must have `metadata` dict with standard Qdrant fields

**Enrichment Steps** (per result):
1. **Visual Artifacts**: If `metadata.has_visual_artifacts == True`:
   - Load artifacts using `_load_visual_artifacts_optimized()`
   - Add `visual_artifacts` field (list of VisualArtifact dicts)
2. **Chapter Context**: If `metadata.chapter_path` exists:
   - Format chapter context using `_format_chapter_context()`
   - Add `chapter_context` field (ChapterContext dict or None)
3. **Quality Breakdown**: If `metadata.quality_score > 0.0`:
   - Format quality breakdown using `_format_quality_breakdown()`
   - Add `quality_breakdown` field (QualityBreakdown dict or None)
4. **Hierarchy Flags**:
   - Set `has_parent = (metadata.parent_chunk_id != None)`
   - Set `has_children = (metadata.child_count > 0)`
   - Check result cache for parent/child availability

**Output**:
- Returns enriched results list (original list is not modified)
- Added fields are optional (None if data unavailable)
- Original Qdrant fields are preserved unchanged

### Error Handling

- **Missing metadata**: Skips enrichment, returns original result
- **Artifact loading failure**: Returns empty `visual_artifacts` list
- **Chapter formatting failure**: Returns `None` for `chapter_context`
- **Quality formatting failure**: Returns `None` for `quality_breakdown`
- **No exceptions thrown**: All errors handled gracefully

### Performance

- **Complexity**: O(n * m) where n = results, m = max_artifacts_per_result
- **Typical**: 5 results × 3 artifacts = 15 file loads
- **Expected time**: 200-500ms for 5 results with artifacts

---

## Method: `_load_visual_artifacts_optimized()`

Loads visual artifacts from persistent storage using direct path construction.

### Signature

```python
def _load_visual_artifacts_optimized(
    self,
    result: Dict[str, Any],
    max_artifacts: int = 3
) -> List[Dict[str, str]]:
    """
    Load visual artifacts using optimized direct path construction.

    Args:
        result: Single search result from Qdrant API
        max_artifacts: Maximum number of artifacts to load (default: 3)

    Returns:
        List of VisualArtifact dicts with fields:
        - artifact_id: str
        - type: "image" | "slide"
        - caption: str
        - data: str (base64 data URL)
        - file_path: str
        - file_size: int
        - ocr_text: str (optional)
    """
```

### Behavior

**Pre-Conditions**:
- `result["metadata"]["has_visual_artifacts"] == True`
- `result["metadata"]["visual_artifact_ids"]` is non-empty list

**Path Construction Algorithm**:
1. Extract `document_id` from metadata
2. Extract `artifact_ids` list from metadata
3. For each artifact_id (up to `max_artifacts`):
   - Determine type: `img_*` → "image", `slide_*` → "slide"
   - Determine subdirectory: image → `images/doc_{document_id}`, slide → `slides/pres_{document_id}`
   - Construct path: `/workspace/visual-artifacts/{subdir}/{artifact_id}.png`
   - Check file exists
   - Load file bytes
   - Base64 encode
   - Build VisualArtifact dict

**Caption Selection**:
- Primary: Use `metadata.image_captions[idx]` if available
- Fallback: Generate `f"Visual Artifact {idx + 1}"`

**Output**:
- Returns list of successfully loaded artifacts
- Silently skips artifacts that fail to load
- Returns empty list if no artifacts loaded successfully

### Error Handling

- **File not found**: Skip artifact, continue with next
- **Base64 encoding error**: Skip artifact, log warning
- **Invalid artifact_id format**: Skip artifact
- **No exceptions thrown**: All errors handled gracefully

### Performance

- **Complexity**: O(m) where m = max_artifacts
- **File I/O**: Direct path, no directory scanning
- **Typical time**: ~50-100ms for 3 artifacts

---

## Method: `_format_chapter_context()`

Formats chapter metadata into human-readable breadcrumb display.

### Signature

```python
def _format_chapter_context(
    self,
    metadata: Dict[str, Any]
) -> Dict[str, str] | None:
    """
    Format chapter metadata into ChapterContext structure.

    Args:
        metadata: Search result metadata from Qdrant

    Returns:
        ChapterContext dict with fields:
        - chapter_number: str
        - chapter_title: str
        - chapter_path: str
        - chapter_level: int
        - sub_chapter: str
        - formatted_path: str
        - breadcrumb_html: str

        Or None if chapter metadata unavailable.
    """
```

### Behavior

**Pre-Conditions**:
- `metadata.get("chapter_title")` or `metadata.get("chapter_path")` must exist

**Formatting Rules**:
1. **Formatted Path**:
   - If `chapter_number` exists: Prepend "Chapter {number} > "
   - Otherwise: Use `chapter_path` as-is
2. **Breadcrumb HTML**:
   - Icon: `📂`
   - Separator: ` > `
   - Indentation: Based on `chapter_level` (indent by 20px per level)

**Output**:
- Returns ChapterContext dict if chapter data available
- Returns None if no chapter metadata present

### Error Handling

- **Missing chapter_title and chapter_path**: Return None
- **Invalid chapter_level**: Default to 1
- **No exceptions thrown**

### Performance

- **Complexity**: O(1) string operations
- **Typical time**: <1ms

---

## Method: `_format_quality_breakdown()`

Formats quality validation scores into display-ready structure.

### Signature

```python
def _format_quality_breakdown(
    self,
    metadata: Dict[str, Any]
) -> Dict[str, Any] | None:
    """
    Format quality scores into QualityBreakdown structure.

    Args:
        metadata: Search result metadata from Qdrant

    Returns:
        QualityBreakdown dict with fields:
        - overall_score: float (0.0-100.0)
        - overall_percent: str (e.g., "92%")
        - color: "green" | "yellow" | "red"
        - components: dict with faithfulness, relevancy, precision, recall
        - badge_html: str
        - tooltip_html: str

        Or None if quality_score <= 0.0.
    """
```

### Behavior

**Pre-Conditions**:
- `metadata.get("quality_score", 0.0) > 0.0`

**Color Mapping**:
```python
if quality_score >= 80.0:
    color = "green"
elif quality_score >= 60.0:
    color = "yellow"
else:
    color = "red"
```

**Component Extraction**:
- Faithfulness: `metadata.get("faithfulness", 0.0)`
- Relevancy: `metadata.get("relevancy", 0.0)`
- Precision: `metadata.get("precision", 0.0)`
- Recall: `metadata.get("recall", 0.0)`

**HTML Generation**:
- Badge: Inline `<span>` with color styling
- Tooltip: Hover `<div>` with component breakdown

**Output**:
- Returns QualityBreakdown dict if quality_score > 0.0
- Returns None if quality validation disabled (score = 0.0)

### Error Handling

- **Missing component scores**: Default to 0.0
- **Invalid score range**: Clamp to 0.0-100.0
- **No exceptions thrown**

### Performance

- **Complexity**: O(1) string operations
- **Typical time**: <1ms

---

## Method: `_update_result_cache()`

Updates the in-memory cache of search results for parent/child lookup.

### Signature

```python
def _update_result_cache(
    self,
    results: List[Dict[str, Any]]
) -> None:
    """
    Update result cache with new search results for parent/child lookup.

    Args:
        results: List of search results to cache

    Returns:
        None (modifies self._result_cache in-place)
    """
```

### Behavior

**Caching Strategy**:
1. Extract `chunk_id` from each result's metadata
2. Store result in `self._result_cache[chunk_id]`
3. Limit cache size to 100 entries (LRU eviction)

**Cache Structure**:
```python
self._result_cache = {
    "chunk_id_1": {full_result_dict},
    "chunk_id_2": {full_result_dict},
    ...
}
```

**Output**:
- Updates instance variable `self._result_cache`
- No return value

### Error Handling

- **Missing chunk_id**: Skip that result
- **Cache overflow**: Evict oldest entries
- **No exceptions thrown**

### Performance

- **Complexity**: O(n) where n = results
- **Memory**: ~10KB per cached result × 100 = ~1MB max
- **Typical time**: <10ms for 20 results

---

## Method: `_check_hierarchy_cache()`

Checks if parent/child chunks are available in result cache.

### Signature

```python
def _check_hierarchy_cache(
    self,
    metadata: Dict[str, Any]
) -> tuple[bool, int]:
    """
    Check if parent and children are available in result cache.

    Args:
        metadata: Search result metadata with hierarchy fields

    Returns:
        Tuple of (parent_in_cache: bool, children_in_cache_count: int)
    """
```

### Behavior

**Parent Check**:
- If `parent_chunk_id` exists: Check if `self._result_cache[parent_chunk_id]` exists
- Return True if found, False otherwise

**Children Check**:
- Note: Qdrant schema does not store `child_ids` list
- Cannot check child availability without querying Qdrant
- Return 0 (children check not implemented)

**Output**:
- Returns tuple: `(parent_in_cache, children_in_cache_count)`
- Typical: `(True, 0)` or `(False, 0)`

### Error Handling

- **Missing parent_chunk_id**: Return `(False, 0)`
- **No exceptions thrown**

### Performance

- **Complexity**: O(1) dict lookup
- **Typical time**: <1ms

---

## Integration Points

### Called By

- `search_smart()`: Enriches results after boosting, before dashboard generation
- `search_semantic()`: Enriches results after Qdrant query
- `search_hybrid()`: Enriches results after RRF ranking

### Calls

- `_load_visual_artifacts_optimized()`: Load visual artifacts from disk
- `_format_chapter_context()`: Format chapter breadcrumb
- `_format_quality_breakdown()`: Format quality badge and tooltip
- `_update_result_cache()`: Update cache for hierarchy lookups
- `_check_hierarchy_cache()`: Check parent/child availability

### Dependencies

- **File System**: `/workspace/visual-artifacts/` directory
- **Environment Variable**: `VISUAL_ARTIFACTS_DIR` (optional override)
- **Python Standard Library**: `os`, `base64`, `typing`

---

## Testing Strategy

### Unit Tests

1. **Test `_enrich_search_results()`**:
   - Input: List of results with varying metadata
   - Expected: All enrichment fields added correctly
   - Edge case: Results with missing metadata

2. **Test `_load_visual_artifacts_optimized()`**:
   - Input: Result with valid artifact_ids
   - Expected: Artifacts loaded with base64 data
   - Edge case: Missing artifact files, invalid paths

3. **Test `_format_chapter_context()`**:
   - Input: Metadata with chapter fields
   - Expected: Breadcrumb HTML generated
   - Edge case: Missing chapter fields, unnumbered chapters

4. **Test `_format_quality_breakdown()`**:
   - Input: Metadata with quality scores
   - Expected: Badge HTML with correct color
   - Edge case: Zero scores, missing component scores

5. **Test `_update_result_cache()`**:
   - Input: List of 20 results
   - Expected: All results cached by chunk_id
   - Edge case: Cache overflow (>100 entries)

6. **Test `_check_hierarchy_cache()`**:
   - Input: Metadata with parent_chunk_id
   - Expected: Correct parent_in_cache boolean
   - Edge case: Parent not in cache, missing parent_chunk_id

### Integration Tests

1. **Full enrichment pipeline**:
   - Run search → enrich → render dashboard
   - Verify visual artifacts display
   - Verify chapter breadcrumbs display
   - Verify quality badges display

2. **Backward compatibility**:
   - Test with documents lacking visual artifacts
   - Test with documents lacking chapter metadata
   - Test with documents having zero quality scores

---

## Versioning

**Version**: 1.0
**Compatibility**: bms_search.py v4.2+
**Breaking Changes**: None (all additions are backward-compatible)

---

## Future Enhancements

1. **Artifact Caching**: Add LRU cache for frequently accessed artifacts
2. **Batch Artifact Loading**: Load all artifacts in parallel using asyncio
3. **Child Chunk Retrieval**: Implement children lookup via Qdrant query
4. **Quality Threshold Configuration**: Add Valves settings for color thresholds
5. **Chapter Navigation**: Add click handlers for breadcrumb filtering
