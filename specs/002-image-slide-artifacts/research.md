# Research: Image and Slide Visual Artifacts for RAG Search

**Feature Branch**: `002-image-slide-artifacts`
**Date**: 2025-10-22
**Status**: Complete

## Executive Summary

This document consolidates research and technical decisions for extending the BMS Agent RAG system to extract, store, and display visual artifacts (images and rendered PowerPoint slides) alongside text search results in OpenWebUI.

**Key Decisions**:
1. **PDF Image Extraction**: PyMuPDF (fitz) for embedded image extraction with pdf2image fallback
2. **PPTX Slide Rendering**: python-pptx + Pillow for slide-to-image conversion (LibreOffice headless as alternative)
3. **OCR Engine**: Tesseract OCR via pytesseract for text extraction from images
4. **Image Storage**: File system storage in `/workspace/visual-artifacts/` with URL references in metadata
5. **Image-Chunk Association**: Proximity-based algorithm using page/position coordinates
6. **OpenWebUI Integration**: Base64 encoding for artifact display with metadata wrapper

---

## 1. PDF Image Extraction

### Decision: PyMuPDF (fitz) Primary, pdf2image Fallback

**Rationale**:
- **PyMuPDF**: Already installed in BMS Agent, fast native C++ library, extracts images directly from PDF structure
- **Performance**: ~50-100ms per page for image extraction (10x faster than pdf2image)
- **Format Support**: Handles PNG, JPEG, TIFF, BMP embedded in PDFs
- **Metadata Preservation**: Retains image dimensions, format, position coordinates
- **Fallback Strategy**: Use pdf2image for scanned PDFs or when PyMuPDF fails (renders page to image, then extracts)

**Alternatives Considered**:
- **pdf2image (Poppler)**: Slower (renders entire page), requires external Poppler dependency, good for scanned docs
- **PDFMiner**: Text-focused, poor image extraction capabilities
- **pdfplumber**: Good for tables/layout, limited image support
- **Apache PDFBox (Java)**: Requires JVM, adds deployment complexity

**Implementation Pattern**:
```python
import fitz  # PyMuPDF

def extract_images_from_pdf(pdf_path):
    images = []
    doc = fitz.open(pdf_path)

    for page_num, page in enumerate(doc):
        image_list = page.get_images(full=True)

        for img_index, img in enumerate(image_list):
            xref = img[0]
            base_image = doc.extract_image(xref)

            images.append({
                'image_bytes': base_image['image'],
                'format': base_image['ext'],  # png, jpeg, etc.
                'page_number': page_num + 1,
                'position': img_index,
                'bbox': page.get_image_bbox(img)  # Bounding box for proximity
            })

    return images
```

---

## 2. DOCX Image Extraction

### Decision: python-docx with _rels Inspection

**Rationale**:
- **python-docx**: Already installed, provides direct access to inline and floating images
- **Relationship Tracking**: Can extract images via document relationships (`_rels`)
- **Caption Extraction**: Access to paragraph text surrounding images for captions
- **Compatibility**: Handles both modern DOCX (Office 2007+) and legacy DOC (via conversion)

**Implementation Pattern**:
```python
from docx import Document
from docx.oxml.ns import qn

def extract_images_from_docx(docx_path):
    doc = Document(docx_path)
    images = []

    # Extract inline images
    for paragraph in doc.paragraphs:
        for run in paragraph.runs:
            inline_shapes = run._element.xpath('.//a:blip')

            for shape in inline_shapes:
                rId = shape.get(qn('r:embed'))
                image_part = doc.part.related_parts[rId]

                images.append({
                    'image_bytes': image_part.blob,
                    'format': image_part.content_type.split('/')[-1],
                    'paragraph_index': doc.paragraphs.index(paragraph),
                    'caption': extract_caption(paragraph)
                })

    return images
```

**Alternatives Considered**:
- **mammoth**: Good for HTML conversion, limited image extraction API
- **python-docx2txt**: Text-only, loses image metadata
- **unoconv (LibreOffice)**: Overkill, slow, designed for format conversion

---

## 3. PowerPoint Slide Rendering

### Decision: python-pptx + Pillow (Primary), LibreOffice Headless (Fallback)

**Rationale**:
- **python-pptx + Pillow**: Pure Python solution, can extract slide layouts and render text/shapes
- **Challenge**: python-pptx doesn't render slides directly (only programmatic access)
- **Solution**: Use LibreOffice headless for high-fidelity slide rendering
- **Deployment**: LibreOffice already available in most Linux environments, RunPod likely has it

**Primary Approach: LibreOffice Headless**
```bash
# Convert PPTX to PDF first (preserves all formatting)
soffice --headless --convert-to pdf presentation.pptx --outdir /tmp/

# Then use pdf2image to extract each page as PNG
from pdf2image import convert_from_path

images = convert_from_path('/tmp/presentation.pdf', dpi=150)
for i, image in enumerate(images):
    image.save(f'/workspace/visual-artifacts/slide_{i+1}.png', 'PNG')
```

**Advantages**:
- **High Fidelity**: Preserves all PowerPoint formatting, colors, fonts, embedded images
- **Production-Ready**: LibreOffice is stable, widely used for document conversion
- **Format Support**: Handles PPTX, PPT (legacy), ODP

**Fallback Approach: python-pptx + PIL (Manual Rendering)**
- Use for simple slides (text-only, basic shapes)
- Complex slides (images, charts, transitions) fallback to LibreOffice
- Lower dependency footprint for development/testing

**Alternatives Considered**:
- **Aspose.Slides (Commercial)**: Expensive licensing, not open-source
- **unoconv**: Wrapper around LibreOffice, adds abstraction layer
- **PowerPoint COM Automation**: Windows-only, not viable for Linux/RunPod
- **Presentations API (Google Slides)**: Requires OAuth, external dependency

**Performance Considerations**:
- LibreOffice conversion: ~500ms-1s per presentation (20-50 slides)
- pdf2image rendering: ~100-200ms per slide at 150 DPI
- Total: < 5 minutes for 50-slide presentation (meets SC-002)

---

## 4. OCR Text Extraction

### Decision: Tesseract OCR via pytesseract

**Rationale**:
- **Tesseract**: Industry standard, open-source OCR engine from Google
- **pytesseract**: Lightweight Python wrapper, easy integration
- **Accuracy**: 70-95% on technical diagrams with annotations (meets assumptions)
- **Language Support**: Default English, extensible to other languages
- **Cost**: Free, no API limits unlike cloud OCR services

**Implementation Pattern**:
```python
import pytesseract
from PIL import Image

def extract_text_from_image(image_path):
    image = Image.open(image_path)
    ocr_text = pytesseract.image_to_string(image, lang='eng')

    # Also extract confidence scores
    data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)

    return {
        'text': ocr_text,
        'confidence': sum(data['conf']) / len(data['conf']),
        'word_count': len([w for w in data['text'] if w.strip()])
    }
```

**Alternatives Considered**:
- **EasyOCR**: More accurate on handwriting, slower, requires PyTorch (large dependency)
- **Google Cloud Vision API**: Cloud-based, costs money, latency, requires internet
- **AWS Textract**: Same issues as Google Vision
- **PaddleOCR**: Chinese origin, less documentation, similar accuracy to Tesseract

**Optimization Strategies**:
- **Preprocessing**: Binarization, noise removal, deskewing for better accuracy
- **Selective OCR**: Only run on images with low text density or captions
- **Caching**: Store OCR results in metadata to avoid re-processing

---

## 5. Image Storage Strategy

### Decision: File System Storage with Metadata References

**Storage Location**: `/workspace/visual-artifacts/`

**Rationale**:
- **Persistent Storage**: `/workspace/` survives RunPod pod restarts
- **Scalability**: File system handles 1000s of images efficiently
- **Cost**: No cloud storage costs (S3/Azure Blob)
- **Access Pattern**: Images loaded on-demand via OpenWebUI artifact requests
- **Backup**: Can be backed up with standard file system tools

**Directory Structure**:
```
/workspace/visual-artifacts/
├── images/                          # Extracted images from PDF/DOCX
│   ├── doc_{doc_id}/
│   │   ├── page_001_img_001.png
│   │   ├── page_001_img_002.jpg
│   │   └── page_002_img_001.png
├── slides/                          # Rendered PowerPoint slides
│   ├── pres_{pres_id}/
│   │   ├── slide_001.png
│   │   ├── slide_002.png
│   │   └── slide_003.png
└── thumbnails/                      # Compressed thumbnails for quick preview
    ├── thumb_{artifact_id}.jpg
```

**Metadata Storage**: Qdrant payload extension

**Image Metadata in Chunk Payload**:
```json
{
  "has_visual_artifacts": true,
  "visual_artifacts": [
    {
      "artifact_id": "img_abc123",
      "artifact_type": "image",
      "file_path": "/workspace/visual-artifacts/images/doc_xyz/page_001_img_001.png",
      "format": "png",
      "dimensions": {"width": 1920, "height": 1080},
      "file_size_bytes": 245678,
      "page_number": 1,
      "ocr_text": "Figure 3: Hydraulic Pressure Valve",
      "caption": "Hydraulic Pressure Valve Assembly",
      "extraction_timestamp": "2025-10-22T10:30:00Z"
    }
  ]
}
```

**Alternatives Considered**:
- **Base64 in Qdrant**: Bloats vector database, inefficient for large images
- **Cloud Storage (S3)**: Additional costs, latency, dependency on external service
- **Database BLOB storage**: Poor performance for large binary data
- **Separate image server**: Over-engineering for MVP, adds deployment complexity

---

## 6. Image-Chunk Association Algorithm

### Decision: Proximity-Based with Caption Matching

**Algorithm**:
1. **Spatial Proximity**: Associate image with nearest text chunk based on document position
2. **Caption Matching**: If image has caption (e.g., "Figure 3"), link to chunk referencing that caption
3. **Fallback**: If no clear association, link to chunk on same page/slide

**Proximity Calculation** (PDF):
```python
def associate_image_with_chunks(image_bbox, text_chunks, page_number):
    # Find chunks on same page
    same_page_chunks = [c for c in text_chunks if c['page'] == page_number]

    if not same_page_chunks:
        return None

    # Calculate distance from image to each chunk
    min_distance = float('inf')
    nearest_chunk = None

    for chunk in same_page_chunks:
        distance = calculate_bbox_distance(image_bbox, chunk['bbox'])
        if distance < min_distance:
            min_distance = distance
            nearest_chunk = chunk

    return nearest_chunk['chunk_id']

def calculate_bbox_distance(bbox1, bbox2):
    # Euclidean distance between bounding box centers
    center1 = ((bbox1[0] + bbox1[2]) / 2, (bbox1[1] + bbox1[3]) / 2)
    center2 = ((bbox2[0] + bbox2[2]) / 2, (bbox2[1] + bbox2[3]) / 2)

    return ((center1[0] - center2[0])**2 + (center1[1] - center2[1])**2)**0.5
```

**Caption-Based Association**:
```python
import re

def extract_figure_references(text):
    # Match patterns like "Figure 3", "Fig. 2", "Image 1", etc.
    pattern = r'(?:Figure|Fig\.|Image|Diagram)\s*(\d+(?:\.\d+)?)'
    return re.findall(pattern, text, re.IGNORECASE)

def associate_via_caption(image_caption, text_chunks):
    figure_num = extract_figure_number(image_caption)  # "Figure 3" → "3"

    for chunk in text_chunks:
        if figure_num in extract_figure_references(chunk['text']):
            return chunk['chunk_id']

    return None  # No caption reference found, fall back to proximity
```

**Multi-Image Handling** (P2):
- Group images within same page section (configurable proximity threshold)
- Preserve sequential order (e.g., step 1, step 2, step 3)
- Limit: Maximum 5 images per chunk (configurable via `MAX_IMAGES_PER_CHUNK`)

---

## 7. OpenWebUI Artifact Integration

### Decision: Base64 Encoding with Metadata Wrapper

**Rationale**:
- **OpenWebUI Artifact System**: Supports structured JSON artifacts with embedded media
- **Base64**: Universal browser support, no additional HTTP requests, works in chat interface
- **Metadata**: Include image caption, source document, page number for context

**Artifact Format**:
```json
{
  "type": "visual_artifact",
  "artifact_id": "img_abc123",
  "content": {
    "text_chunk": "The brake system hydraulic valve controls pressure...",
    "images": [
      {
        "caption": "Figure 3: Hydraulic Pressure Valve",
        "source_document": "BMS-ENGI-FOR-004 Maintenance Manual.pdf",
        "page_number": 15,
        "format": "png",
        "dimensions": "1920x1080",
        "data": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgA..."
      }
    ],
    "chunk_metadata": {
      "quality_score": 0.87,
      "chapter": "3.2 Hydraulic Systems"
    }
  }
}
```

**OpenWebUI Tool Update** (`bms_search.py`):
```python
def format_search_result_with_artifacts(chunk, visual_artifacts):
    """Format search result with visual artifacts for OpenWebUI display"""

    result = {
        "text": chunk['content'],
        "source": chunk['metadata']['document_name'],
        "quality_score": chunk['metadata']['quality_score']
    }

    # Add visual artifacts if present
    if visual_artifacts:
        result["artifacts"] = []

        for artifact in visual_artifacts:
            # Load image from file path and encode to base64
            with open(artifact['file_path'], 'rb') as f:
                image_bytes = f.read()

            base64_image = base64.b64encode(image_bytes).decode('utf-8')

            result["artifacts"].append({
                "type": "image",
                "caption": artifact.get('caption', 'Image'),
                "data": f"data:image/{artifact['format']};base64,{base64_image}"
            })

    return result
```

**Performance Optimization**:
- **Thumbnail First**: Send thumbnail (compressed) initially, load full-res on click
- **Lazy Loading**: Only encode/send images for top-k search results (default: first 10)
- **Caching**: Cache base64-encoded images in memory (LRU cache, 100MB limit)

**Alternatives Considered**:
- **URL References**: Requires separate HTTP server to serve images, adds complexity
- **File Paths**: Only works if OpenWebUI has file system access, brittle
- **Separate Image Service**: Over-engineering, adds deployment/network overhead

---

## 8. Image Processing and Optimization

### Decision: Pillow (PIL) for Resizing and Format Conversion

**Maximum Dimensions**: 1920x1080 (configurable via `MAX_IMAGE_WIDTH`, `MAX_IMAGE_HEIGHT`)

**Rationale**:
- **Storage Efficiency**: Large diagrams (5000x3000px) waste storage, reduce to HD resolution
- **Display Optimization**: Most monitors are 1920x1080 or 2560x1440, larger images overkill
- **Bandwidth**: Smaller images load faster in OpenWebUI (< 1 second per SC-004)
- **Aspect Ratio Preservation**: Pillow handles proportional resizing (FR-012)

**Image Processing Pipeline**:
```python
from PIL import Image

def process_image(image_bytes, format, artifact_id):
    """Resize, compress, and save image artifact"""

    image = Image.open(io.BytesIO(image_bytes))

    # Resize if exceeds max dimensions
    max_width = 1920
    max_height = 1080

    if image.width > max_width or image.height > max_height:
        image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

    # Convert to RGB if RGBA or other modes (for JPEG compatibility)
    if image.mode not in ('RGB', 'L'):
        if image.mode == 'RGBA':
            # Create white background for transparency
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[3])  # Alpha channel
            image = background
        else:
            image = image.convert('RGB')

    # Save optimized image
    output_path = f"/workspace/visual-artifacts/images/{artifact_id}.png"
    image.save(output_path, 'PNG', optimize=True)

    # Also create thumbnail
    thumb = image.copy()
    thumb.thumbnail((400, 300), Image.Resampling.LANCZOS)
    thumb_path = f"/workspace/visual-artifacts/thumbnails/thumb_{artifact_id}.jpg"
    thumb.save(thumb_path, 'JPEG', quality=80)

    return {
        'file_path': output_path,
        'thumbnail_path': thumb_path,
        'dimensions': image.size,
        'file_size': os.path.getsize(output_path)
    }
```

**Format Standardization**:
- **Storage Format**: PNG for diagrams/screenshots (lossless), JPEG for photos (lossy)
- **Detection**: Use image characteristics (transparency, color depth) to choose format
- **Quality**: JPEG quality=85 for good balance (80% reduction, minimal quality loss)

---

## 9. Enhanced Document Processor Integration

### Integration Points

**1. Image Extraction Module** (New):
```python
# bms-agent/scr/image_extractor.py

class ImageExtractor:
    def extract_from_pdf(self, pdf_path):
        # Use PyMuPDF
        pass

    def extract_from_docx(self, docx_path):
        # Use python-docx
        pass

    def render_pptx_slides(self, pptx_path):
        # Use LibreOffice + pdf2image
        pass
```

**2. Update `EnhancedDocumentProcessor`**:
```python
# bms-agent/scr/enhanced_document_processor.py

def process_document(self, file_path, metadata):
    # Existing text extraction
    text = self._read_document(file_path)

    # NEW: Extract visual artifacts
    visual_artifacts = self._extract_visual_artifacts(file_path, metadata)

    # Existing chunking
    chunks = self._create_hierarchical_chunks(text, metadata)

    # NEW: Associate images with chunks
    chunks = self._associate_artifacts_with_chunks(chunks, visual_artifacts)

    # Existing quality validation, embedding generation, indexing
    ...
```

**3. Qdrant Payload Extension**:
```python
# Update chunk metadata to include visual artifact references
chunk_payload = {
    # Existing fields
    'document_name': doc_name,
    'content': chunk_text,
    'quality_score': 0.87,

    # NEW: Visual artifact fields
    'has_visual_artifacts': True,
    'visual_artifact_ids': ['img_abc123', 'img_def456'],
    'visual_artifact_count': 2
}
```

**4. OpenWebUI Tool Update**:
```python
# bms_search.py

def search_with_artifacts(query, top_k=10):
    # Existing search
    results = qdrant_client.search(...)

    # NEW: Load and include visual artifacts
    for result in results:
        if result.payload.get('has_visual_artifacts'):
            artifact_ids = result.payload['visual_artifact_ids']
            artifacts = load_visual_artifacts(artifact_ids)
            result['artifacts'] = format_artifacts_for_display(artifacts)

    return results
```

---

## 10. Performance and Scalability

### Performance Targets (from Success Criteria)

- **SC-002**: < 5 minutes for 20-50 slide PPTX processing
- **SC-003**: 95%+ image extraction success rate
- **SC-004**: < 1 second image load time for 90% of artifacts
- **SC-007**: < 2x storage overhead
- **SC-008**: Handle 50+ images per document without degradation

### Optimization Strategies

**1. Async Processing**:
```python
import asyncio

async def process_document_with_images_async(file_path):
    # Run image extraction in parallel with text processing
    text_task = asyncio.create_task(extract_text(file_path))
    images_task = asyncio.create_task(extract_images(file_path))

    text, images = await asyncio.gather(text_task, images_task)
    return text, images
```

**2. Batch Image Processing**:
```python
# Process multiple images in batch to amortize I/O costs
def batch_process_images(images, batch_size=10):
    for i in range(0, len(images), batch_size):
        batch = images[i:i+batch_size]
        # Process batch concurrently
        with ThreadPoolExecutor(max_workers=4) as executor:
            executor.map(process_image, batch)
```

**3. Lazy Artifact Loading**:
- Don't load all images immediately
- Load thumbnails first, full-res on user click/expand
- Cache frequently accessed images in memory

**4. Storage Compression**:
- PNG optimization (pngquant, optipng)
- JPEG quality tuning (85% quality = 80% size reduction)
- WebP format consideration (better compression, not all browsers support)

### Scalability Estimates

**Typical Railway Document**:
- 100 pages
- 20 images (diagrams, photos)
- Average image size after compression: 500KB
- Total storage per document: ~10MB images + ~2MB text/metadata = 12MB

**300 Document Corpus**:
- Total storage: 300 docs × 12MB = 3.6GB
- < 2x overhead compared to text-only (1.8GB for text) ✅ Meets SC-007

**50-Image Document** (Edge Case):
- Storage: 50 × 500KB = 25MB
- Processing time: 50 images × 100ms = 5 seconds (still < 5 min target) ✅ Meets SC-008

---

## 11. Error Handling and Resilience

### Failure Modes and Mitigations

**1. Corrupted Image** (Edge Case):
```python
try:
    image = Image.open(image_path)
    image.verify()  # Check integrity
except Exception as e:
    logger.warning(f"Corrupted image: {image_path}, skipping. Error: {e}")
    continue  # Skip image, continue processing document
```

**2. LibreOffice Unavailable**:
```python
def render_slide(pptx_path):
    try:
        # Try LibreOffice first
        subprocess.run(['soffice', '--version'], check=True)
        return render_with_libreoffice(pptx_path)
    except FileNotFoundError:
        logger.warning("LibreOffice not found, falling back to text extraction")
        return extract_text_only(pptx_path)  # Fallback
```

**3. OCR Failure**:
```python
try:
    ocr_text = pytesseract.image_to_string(image)
except Exception as e:
    logger.error(f"OCR failed for {image_path}: {e}")
    ocr_text = ""  # Store empty OCR text, still index the image
```

**4. Storage Full**:
```python
def save_artifact(image, artifact_path):
    # Check available disk space before saving
    stat = os.statvfs('/workspace/')
    free_space_gb = (stat.f_bavail * stat.f_frsize) / (1024**3)

    if free_space_gb < 10:  # Less than 10GB free
        logger.error("Low disk space, cannot save artifact")
        raise DiskSpaceError("Insufficient storage for visual artifacts")

    image.save(artifact_path)
```

---

## 12. Testing Strategy

### Unit Tests

**1. Image Extraction Tests**:
```python
def test_pdf_image_extraction():
    pdf_path = 'tests/fixtures/sample_with_images.pdf'
    extractor = ImageExtractor()
    images = extractor.extract_from_pdf(pdf_path)

    assert len(images) > 0
    assert images[0]['format'] in ['png', 'jpeg', 'jpg']
    assert images[0]['page_number'] > 0
```

**2. Slide Rendering Tests**:
```python
def test_pptx_slide_rendering():
    pptx_path = 'tests/fixtures/sample_presentation.pptx'
    extractor = ImageExtractor()
    slides = extractor.render_pptx_slides(pptx_path)

    assert len(slides) == 20  # Expected slide count
    assert slides[0]['format'] == 'png'
    assert os.path.exists(slides[0]['file_path'])
```

**3. OCR Tests**:
```python
def test_ocr_text_extraction():
    image_path = 'tests/fixtures/diagram_with_text.png'
    ocr_result = extract_text_from_image(image_path)

    assert 'valve' in ocr_result['text'].lower()
    assert ocr_result['confidence'] > 0.7
```

### Integration Tests

**1. End-to-End Document Processing**:
```python
def test_document_with_images_processing():
    pdf_path = 'tests/fixtures/maintenance_manual.pdf'
    processor = EnhancedDocumentProcessor()

    result = processor.process_document(pdf_path, {'department': 'Engineering'})

    assert result['chunks_created'] > 0
    assert result['visual_artifacts_extracted'] > 0

    # Verify artifacts are associated with chunks
    chunks_with_artifacts = [c for c in result['chunks'] if c['has_visual_artifacts']]
    assert len(chunks_with_artifacts) > 0
```

**2. OpenWebUI Artifact Display Test**:
```python
def test_search_returns_artifacts():
    query = "brake system diagram"
    results = search_with_artifacts(query, top_k=5)

    # Check if results contain visual artifacts
    artifacts_found = sum(1 for r in results if 'artifacts' in r)
    assert artifacts_found > 0  # At least one result has artifact

    # Verify base64 encoding
    first_artifact = results[0]['artifacts'][0]
    assert first_artifact['data'].startswith('data:image/')
```

### Performance Tests

**1. Processing Time Test**:
```python
import time

def test_pptx_processing_time():
    pptx_path = 'tests/fixtures/50_slide_presentation.pptx'

    start = time.time()
    slides = render_pptx_slides(pptx_path)
    end = time.time()

    processing_time = end - start
    assert processing_time < 300  # 5 minutes (SC-002)
```

**2. Image Load Time Test**:
```python
def test_image_artifact_load_time():
    artifact_id = 'img_test123'

    start = time.time()
    artifact = load_and_encode_artifact(artifact_id)
    end = time.time()

    load_time = end - start
    assert load_time < 1.0  # 1 second (SC-004)
```

---

## 13. Deployment Considerations

### Dependencies to Add

**Python Packages** (requirements.txt):
```
pytesseract>=0.3.10
pdf2image>=1.16.3
Pillow>=10.0.0
```

**System Dependencies**:
```bash
# Tesseract OCR
apt-get install -y tesseract-ocr tesseract-ocr-eng

# Poppler (for pdf2image)
apt-get install -y poppler-utils

# LibreOffice (for PPTX rendering)
apt-get install -y libreoffice-core libreoffice-writer libreoffice-impress

# Image optimization tools (optional)
apt-get install -y optipng pngquant
```

### Environment Variables

**New Configuration**:
```bash
# Visual Artifacts
VISUAL_ARTIFACTS_DIR=/workspace/visual-artifacts
MAX_IMAGE_WIDTH=1920
MAX_IMAGE_HEIGHT=1080
MAX_IMAGES_PER_CHUNK=5
ENABLE_OCR=true
OCR_LANGUAGE=eng

# Slide Rendering
PPTX_RENDER_DPI=150
PPTX_RENDER_ENGINE=libreoffice  # or 'manual' for python-pptx

# Performance
IMAGE_PROCESSING_WORKERS=4
ARTIFACT_CACHE_SIZE_MB=100
```

### Storage Initialization

**RunPod `/pre_start.sh` Addition**:
```bash
# Create visual artifacts directory
mkdir -p /workspace/visual-artifacts/images
mkdir -p /workspace/visual-artifacts/slides
mkdir -p /workspace/visual-artifacts/thumbnails

# Set permissions
chmod -R 755 /workspace/visual-artifacts

# Verify LibreOffice installation
if ! command -v soffice &> /dev/null; then
    echo "WARNING: LibreOffice not found. PPTX slide rendering will fail."
fi

# Verify Tesseract installation
if ! command -v tesseract &> /dev/null; then
    echo "WARNING: Tesseract not found. OCR will be disabled."
fi
```

---

## 14. Open Questions Resolved

All technical decisions have been made with reasonable defaults:

✅ **Image Extraction Library**: PyMuPDF (fitz) + pdf2image fallback
✅ **Slide Rendering**: LibreOffice headless + pdf2image
✅ **OCR Engine**: Tesseract OCR
✅ **Storage Location**: `/workspace/visual-artifacts/`
✅ **Image-Chunk Association**: Proximity + caption matching algorithm
✅ **OpenWebUI Integration**: Base64 encoding with metadata wrapper
✅ **Image Optimization**: Pillow with 1920x1080 max dimensions
✅ **Performance**: Async processing, batch operations, lazy loading

---

## 15. References

**Existing Documentation**:
- BMS Agent CLAUDE.md - Project overview
- Feature 001 research.md - RAG system architecture
- enhanced_document_processor.py - Current document processing implementation

**External Resources**:
- PyMuPDF documentation: https://pymupdf.readthedocs.io/
- python-pptx documentation: https://python-pptx.readthedocs.io/
- Tesseract OCR: https://github.com/tesseract-ocr/tesseract
- Pillow (PIL): https://pillow.readthedocs.io/
- LibreOffice headless: https://wiki.documentfoundation.org/Development/CommandLine

---

## Conclusion

All technical unknowns have been resolved with production-ready solutions. The implementation leverages existing BMS Agent infrastructure (PyMuPDF, python-docx, Pillow) while adding targeted libraries for OCR (Tesseract) and slide rendering (LibreOffice).

**Next Steps**:
1. Generate data model documentation (`data-model.md`)
2. Define API contract extensions (`contracts/`)
3. Create developer quickstart guide (`quickstart.md`)
4. Run `/speckit.tasks` to generate implementation tasks
