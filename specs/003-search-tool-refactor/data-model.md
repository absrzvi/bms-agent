# Data Model: Search Tool Enhanced Retrieval

**Date**: 2025-10-22
**Feature**: Search Tool Enhanced Retrieval
**Purpose**: Define data structures for enriched search results

## Overview

This document defines the data structures used to represent enriched search results with visual artifacts, chapter context, quality scores, and hierarchical relationships. These structures are used internally by the `bms_search.py` tool and are not exposed as external APIs.

## Core Data Structures

### 1. EnrichedSearchResult

An enriched search result extends the base Qdrant search result with additional context loaded from metadata and file system.

**Structure**:
```python
{
    # Base Qdrant fields (unchanged)
    "text": str,                    # Chunk text content
    "score": float,                 # Relevance score (0.0-1.0)
    "metadata": {                   # Base metadata from Qdrant
        "document_id": str,
        "document_name": str,
        "department": str,
        "document_type": str,
        "chunk_id": str,
        # ... other base fields
    },

    # Enhanced fields (added by enrichment)
    "visual_artifacts": List[VisualArtifact],  # See VisualArtifact below
    "chapter_context": ChapterContext,          # See ChapterContext below
    "quality_breakdown": QualityBreakdown,      # See QualityBreakdown below
    "has_parent": bool,                         # True if parent_chunk_id exists
    "has_children": bool,                       # True if child_count > 0
    "parent_in_cache": bool,                    # True if parent is in result cache
    "children_in_cache": int                    # Number of children in result cache
}
```

**Field Descriptions**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | string | Yes | Original chunk text content from Qdrant |
| `score` | float | Yes | Relevance score from Qdrant (0.0-1.0) |
| `metadata` | dict | Yes | Original metadata payload from Qdrant |
| `visual_artifacts` | List[VisualArtifact] | No | Loaded visual artifacts (empty list if none) |
| `chapter_context` | ChapterContext | No | Formatted chapter hierarchy (None if not available) |
| `quality_breakdown` | QualityBreakdown | No | Quality validation scores (None if not available) |
| `has_parent` | bool | Yes | True if parent_chunk_id is present in metadata |
| `has_children` | bool | Yes | True if child_count > 0 in metadata |
| `parent_in_cache` | bool | Yes | True if parent chunk is available in result cache |
| `children_in_cache` | int | Yes | Count of child chunks available in result cache |

**Notes**:
- Enriched fields are computed during result processing
- Original Qdrant fields are never modified
- Enhanced fields default to empty/None when data unavailable

---

### 2. VisualArtifact

Represents a loaded visual artifact (image or slide) with display-ready data.

**Structure**:
```python
{
    "artifact_id": str,           # Unique identifier (e.g., "img_62f221a40149", "slide_08cf72e755bc")
    "type": str,                  # Artifact type: "image" or "slide"
    "caption": str,               # Display caption (from metadata or generated)
    "data": str,                  # Base64-encoded image data with data URL prefix
    "file_path": str,             # Original file path on disk
    "file_size": int,             # File size in bytes
    "ocr_text": str               # OCR text from metadata (optional)
}
```

**Field Descriptions**:

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `artifact_id` | string | Yes | Unique artifact identifier from Qdrant metadata | `"img_62f221a40149"` |
| `type` | string | Yes | Artifact type | `"image"` or `"slide"` |
| `caption` | string | Yes | Display caption | `"Figure 1: Network Diagram"` |
| `data` | string | Yes | Base64-encoded data URL | `"data:image/png;base64,iVBORw0KG..."` |
| `file_path` | string | Yes | Original file path | `"/workspace/visual-artifacts/images/doc_hr_10_form/img_62f221a40149.png"` |
| `file_size` | int | Yes | File size in bytes | `156789` |
| `ocr_text` | string | No | OCR text extracted from artifact | `"Safety Protocol Overview"` |

**Data URL Format**:
```
data:image/png;base64,{base64_encoded_bytes}
```

**Type Determination**:
- `artifact_id.startswith('img_')` → `type = "image"`
- `artifact_id.startswith('slide_')` → `type = "slide"`

**Caption Fallback**:
- Primary: Use `image_captions[idx]` from metadata
- Fallback: Generate `f"Visual Artifact {idx + 1}"`

---

### 3. ChapterContext

Represents hierarchical chapter/section information for a chunk.

**Structure**:
```python
{
    "chapter_number": str,        # Chapter number (e.g., "1", "2.3", or "")
    "chapter_title": str,         # Chapter title/heading text
    "chapter_path": str,          # Full breadcrumb path
    "chapter_level": int,         # Nesting level (1, 2, 3, ...)
    "sub_chapter": str,           # Sub-chapter identifier
    "formatted_path": str,        # Human-readable path with separators
    "breadcrumb_html": str        # HTML for breadcrumb display
}
```

**Field Descriptions**:

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `chapter_number` | string | No | Numeric chapter identifier | `"2.3"`, `""` (unnumbered) |
| `chapter_title` | string | Yes | Chapter heading text | `"Safety Protocols"` |
| `chapter_path` | string | Yes | Full hierarchical path | `"Introduction > Background > Scope"` |
| `chapter_level` | int | Yes | Nesting depth (1-indexed) | `1` (top-level), `2` (sub-chapter) |
| `sub_chapter` | string | No | Sub-chapter identifier | `"2.3.1"` |
| `formatted_path` | string | Yes | Display-ready path with separators | `"Chapter 2 > Section 2.3 > Safety Protocols"` |
| `breadcrumb_html` | string | Yes | HTML for breadcrumb UI | `<div class="breadcrumb">...</div>` |

**Formatted Path Examples**:
```
chapter_path: "Introduction > Background > Scope"
formatted_path: "Chapter 1 > Background > Scope"

chapter_path: "Safety Protocols"
formatted_path: "Safety Protocols"

chapter_path: ""
formatted_path: ""  # No chapter context
```

**Breadcrumb HTML Format**:
```html
<div class="chapter-breadcrumb">
    <span class="breadcrumb-icon">📂</span>
    <span class="breadcrumb-path">Chapter 2 > Section 2.3 > Safety Protocols</span>
</div>
```

---

### 4. QualityBreakdown

Represents quality validation scores for a chunk.

**Structure**:
```python
{
    "overall_score": float,       # Overall quality score (0.0-100.0)
    "overall_percent": str,       # Formatted percentage (e.g., "92%")
    "color": str,                 # Badge color: "green", "yellow", "red"
    "components": {               # Individual RAGAS metrics
        "faithfulness": float,    # 0.0-1.0
        "relevancy": float,       # 0.0-1.0 (answer_relevancy)
        "precision": float,       # 0.0-1.0 (context_precision)
        "recall": float           # 0.0-1.0 (context_recall)
    },
    "badge_html": str,            # HTML for quality badge
    "tooltip_html": str           # HTML for tooltip with breakdown
}
```

**Field Descriptions**:

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `overall_score` | float | Yes | Overall quality score | `92.5` (0.0-100.0 range) |
| `overall_percent` | string | Yes | Formatted percentage | `"93%"` |
| `color` | string | Yes | Badge color based on score | `"green"` (≥80%), `"yellow"` (60-80%), `"red"` (<60%) |
| `components` | dict | Yes | RAGAS component scores | See Components table below |
| `badge_html` | string | Yes | Inline badge HTML | `<span class="quality-badge">...</span>` |
| `tooltip_html` | string | Yes | Hover tooltip HTML | `<div class="quality-tooltip">...</div>` |

**Component Scores**:

| Component | Range | Description |
|-----------|-------|-------------|
| `faithfulness` | 0.0-1.0 | Measures factual consistency with source |
| `relevancy` | 0.0-1.0 | Measures answer relevance to query |
| `precision` | 0.0-1.0 | Measures context precision |
| `recall` | 0.0-1.0 | Measures context recall |

**Color Mapping**:
```python
if overall_score >= 80.0:
    color = "green"
elif overall_score >= 60.0:
    color = "yellow"
else:
    color = "red"
```

**Badge HTML Format**:
```html
<span class="quality-badge" style="background-color: green; color: white; padding: 2px 8px; border-radius: 4px;">
    93%
</span>
```

**Tooltip HTML Format**:
```html
<div class="quality-tooltip">
    <div class="tooltip-header">Quality Breakdown</div>
    <div class="tooltip-metrics">
        <div>Faithfulness: 95%</div>
        <div>Relevancy: 90%</div>
        <div>Precision: 92%</div>
        <div>Recall: 88%</div>
    </div>
</div>
```

---

## Data Flow

### Enrichment Pipeline

```
1. Base Qdrant Results
   ↓
2. Extract Metadata
   ├─ has_visual_artifacts? → Load Visual Artifacts
   ├─ chapter_path? → Format Chapter Context
   ├─ quality_score? → Format Quality Breakdown
   └─ parent_chunk_id? → Check Parent/Child Cache
   ↓
3. Enriched Search Result
   ↓
4. Dashboard HTML Generation
```

### Visual Artifact Loading Flow

```
Result Metadata
   ├─ has_visual_artifacts == True?
   ├─ visual_artifact_ids: ["img_abc", "slide_xyz"]
   ├─ image_captions: ["Figure 1", "Slide 3"]
   └─ document_id: "hr_10_form"
   ↓
For each artifact_id:
   1. Determine type (img_ or slide_)
   2. Construct path: /workspace/visual-artifacts/{subdir}/{doc_prefix}{document_id}/{artifact_id}.png
   3. Check file exists
   4. Load bytes
   5. Base64 encode
   6. Build VisualArtifact object
   ↓
List[VisualArtifact]
```

### Chapter Context Formatting Flow

```
Metadata Fields
   ├─ chapter_title: "Safety Protocols"
   ├─ chapter_path: "Introduction > Background > Safety Protocols"
   ├─ chapter_level: 3
   └─ chapter_number: "1.2.3"
   ↓
Format Operations:
   1. Add "Chapter X >" prefix if chapter_number exists
   2. Generate breadcrumb HTML with icon
   3. Add indentation based on chapter_level
   ↓
ChapterContext object
```

### Quality Breakdown Formatting Flow

```
Metadata Fields
   ├─ quality_score: 92.5
   ├─ faithfulness: 0.95
   ├─ relevancy: 0.90
   ├─ precision: 0.92
   └─ recall: 0.88
   ↓
Format Operations:
   1. Convert overall_score to percentage string
   2. Map score to color (green/yellow/red)
   3. Format components as percentages
   4. Generate badge HTML
   5. Generate tooltip HTML
   ↓
QualityBreakdown object
```

---

## Validation Rules

### VisualArtifact Validation

- `artifact_id` MUST match pattern: `(img|slide)_[a-f0-9]{12}`
- `type` MUST be one of: `"image"`, `"slide"`
- `data` MUST start with `"data:image/png;base64,"`
- `file_size` MUST be > 0 and < 10MB (10,485,760 bytes)

### ChapterContext Validation

- `chapter_title` MUST NOT be empty string
- `chapter_level` MUST be integer >= 1
- `chapter_path` MAY be empty (for unnumbered sections)
- `formatted_path` MUST equal `chapter_path` if no chapter_number exists

### QualityBreakdown Validation

- `overall_score` MUST be 0.0-100.0
- All `components` scores MUST be 0.0-1.0
- `color` MUST be one of: `"green"`, `"yellow"`, `"red"`
- Badge only rendered if `overall_score > 0.0`

---

## Error Handling

### Missing Visual Artifacts

**Scenario**: `has_visual_artifacts == True` but artifact files not found on disk

**Handling**:
- Skip missing artifacts silently
- Continue loading other artifacts
- Return partial list of VisualArtifact objects
- No error shown to user (graceful degradation)

### Missing Chapter Metadata

**Scenario**: `chapter_path` is None or empty

**Handling**:
- Return None for ChapterContext
- No chapter breadcrumb rendered in UI
- Document displays without chapter context

### Zero Quality Scores

**Scenario**: `quality_score == 0.0` (quality validation disabled)

**Handling**:
- Return None for QualityBreakdown
- No quality badge rendered in UI
- No tooltip displayed

### Parent/Child Not in Cache

**Scenario**: User clicks "Expand Context" but parent not in result cache

**Handling**:
- Display message: "Parent context not available in current results"
- Suggest search query: "Try searching for: [parent_title]"
- No error thrown

---

## Implementation Notes

### Memory Considerations

- **Result Cache**: Stores up to 20 results in memory (~200KB per result with metadata)
- **Artifact Cache**: No caching (artifacts loaded on-demand)
- **Total Memory**: ~5MB for typical search session (20 results + overhead)

### Performance Considerations

- **Artifact Loading**: O(m) where m = max_artifacts (typically 3)
- **Chapter Formatting**: O(1) string operations
- **Quality Formatting**: O(1) string operations
- **Total Enrichment**: O(m) per result, dominated by artifact loading

### Thread Safety

- Not applicable: OpenWebUI tools run in single-threaded Python context
- Result cache is instance variable, not shared across sessions

---

## Future Enhancements

### Potential Additions

1. **Artifact Caching**: LRU cache for frequently accessed artifacts
2. **Thumbnail Optimization**: Load thumbnails first, full image on click
3. **Lazy Loading**: Only load artifacts for visible results (viewport detection)
4. **Quality Score Thresholds**: Configurable color thresholds via Valves
5. **Chapter Navigation**: Click breadcrumb to filter by chapter

### Backward Compatibility

All enhancements must:
- Gracefully handle missing metadata fields
- Never break existing search functionality
- Default to original behavior when enhanced data unavailable
