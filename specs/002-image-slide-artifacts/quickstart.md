# Quickstart: Image and Slide Visual Artifacts

**Feature Branch**: `002-image-slide-artifacts`
**Date**: 2025-10-22

## Overview

This quickstart guide walks you through setting up and testing the visual artifacts feature for the BMS Agent RAG system. You'll extract images from documents, render PowerPoint slides, and display them in OpenWebUI search results.

---

## Prerequisites

Before starting, ensure you have:

1. **BMS Agent System**: Fully operational BMS Agent RAG system (Feature 001)
2. **Python 3.11+**: With existing dependencies installed
3. **RunPod Environment**: Access to `/workspace/` persistent storage
4. **System Packages**: Tesseract OCR, Poppler, LibreOffice

---

## Installation

### Step 1: Install System Dependencies

```bash
# Update package list
apt-get update

# Install Tesseract OCR with English language data
apt-get install -y tesseract-ocr tesseract-ocr-eng

# Install Poppler utilities (for pdf2image)
apt-get install -y poppler-utils

# Install LibreOffice for PPTX slide rendering
apt-get install -y libreoffice-core libreoffice-impress

# Verify installations
tesseract --version
soffice --version
pdftoppm -v
```

**Expected Output**:
```
tesseract 5.x.x
LibreOffice 7.x.x.x
pdftoppm version 22.x.x
```

### Step 2: Install Python Dependencies

```bash
cd /workspace/bms-agent

# Add new packages to requirements.txt
cat >> requirements.txt <<EOF
pytesseract>=0.3.10
pdf2image>=1.16.3
Pillow>=10.0.0
EOF

# Install dependencies
pip install -r requirements.txt

# Verify installations
python3 -c "import pytesseract; import pdf2image; from PIL import Image; print('All packages imported successfully')"
```

### Step 3: Create Visual Artifacts Storage

```bash
# Create directory structure
mkdir -p /workspace/visual-artifacts/images
mkdir -p /workspace/visual-artifacts/slides
mkdir -p /workspace/visual-artifacts/thumbnails

# Set permissions
chmod -R 755 /workspace/visual-artifacts

# Verify structure
tree /workspace/visual-artifacts -L 1
```

**Expected Output**:
```
/workspace/visual-artifacts
├── images
├── slides
└── thumbnails
```

### Step 4: Configure Environment Variables

```bash
# Add to ~/.bashrc or /workspace/bms-agent/.env
export VISUAL_ARTIFACTS_DIR=/workspace/visual-artifacts
export MAX_IMAGE_WIDTH=1920
export MAX_IMAGE_HEIGHT=1080
export MAX_IMAGES_PER_CHUNK=5
export ENABLE_OCR=true
export OCR_LANGUAGE=eng
export PPTX_RENDER_DPI=150
export PPTX_RENDER_ENGINE=libreoffice

# Apply changes
source ~/.bashrc  # or source .env
```

---

## First Run: Test Image Extraction

### Test 1: Extract Images from PDF

Create a test script to verify PDF image extraction:

```python
# test_pdf_extraction.py
import sys
sys.path.insert(0, '/workspace/bms-agent/bms-agent/scr')

from enhanced_document_processor import EnhancedDocumentProcessor
from processing_config import ProcessingConfig

# Initialize processor
config = ProcessingConfig()
processor = EnhancedDocumentProcessor(config)

# Test PDF with images
pdf_path = '/workspace/bms-agent/upload-files/Engineering/BMS-ENGI-FOR-004 Maintenance Manual.pdf'

# Process document
result = processor.process_document(pdf_path, {
    'department': 'Engineering',
    'category': 'Manual'
})

# Check results
print(f"Document processed: {result['document_name']}")
print(f"Total chunks: {result['chunks_created']}")
print(f"Visual artifacts extracted: {result.get('visual_artifacts_extracted', 0)}")

# List artifacts
if result.get('visual_artifacts'):
    for artifact in result['visual_artifacts'][:5]:  # Show first 5
        print(f"\nArtifact: {artifact['artifact_id']}")
        print(f"  Type: {artifact['artifact_type']}")
        print(f"  Page: {artifact['source_page_or_slide_number']}")
        print(f"  Format: {artifact['file_format']}")
        print(f"  Dimensions: {artifact['dimensions']['width']}x{artifact['dimensions']['height']}")
        print(f"  File: {artifact['file_path']}")
        if artifact.get('caption'):
            print(f"  Caption: {artifact['caption']}")
```

Run the test:
```bash
cd /workspace/bms-agent
python3 test_pdf_extraction.py
```

**Expected Output**:
```
Document processed: BMS-ENGI-FOR-004 Maintenance Manual.pdf
Total chunks: 45
Visual artifacts extracted: 12

Artifact: img_abc123
  Type: image
  Page: 3
  Format: png
  Dimensions: 1920x1080
  File: /workspace/visual-artifacts/images/doc_xyz/page_003_img_001.png
  Caption: Figure 1: System Overview
...
```

### Test 2: Render PowerPoint Slides

Test PPTX slide rendering:

```python
# test_pptx_rendering.py
import sys
sys.path.insert(0, '/workspace/bms-agent/bms-agent/scr')

from enhanced_document_processor import EnhancedDocumentProcessor
from processing_config import ProcessingConfig

config = ProcessingConfig()
processor = EnhancedDocumentProcessor(config)

# Test PPTX file
pptx_path = '/workspace/bms-agent/upload-files/Training/safety_procedures.pptx'

result = processor.process_document(pptx_path, {
    'department': 'Training',
    'category': 'Presentation'
})

print(f"Presentation: {result['document_name']}")
print(f"Total slides rendered: {result.get('visual_artifacts_extracted', 0)}")

# Check first slide
if result.get('visual_artifacts'):
    first_slide = result['visual_artifacts'][0]
    print(f"\nFirst slide: {first_slide['artifact_id']}")
    print(f"  File: {first_slide['file_path']}")
    print(f"  Dimensions: {first_slide['dimensions']}")

    # Verify file exists
    import os
    assert os.path.exists(first_slide['file_path']), "Slide image file not found!"
    print("  ✓ Slide image file exists")
```

Run the test:
```bash
python3 test_pptx_rendering.py
```

### Test 3: OCR Text Extraction

Test OCR on an image with text:

```python
# test_ocr.py
import pytesseract
from PIL import Image

# Create a test image with text (or use existing diagram)
test_image_path = '/workspace/visual-artifacts/images/doc_xyz/page_003_img_001.png'

# Run OCR
image = Image.open(test_image_path)
ocr_text = pytesseract.image_to_string(image, lang='eng')
data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)

# Calculate confidence
confidences = [c for c in data['conf'] if c != -1]
avg_confidence = sum(confidences) / len(confidences) if confidences else 0

print(f"OCR Text:\n{ocr_text}\n")
print(f"Confidence: {avg_confidence:.2f}%")
print(f"Words detected: {len([w for w in data['text'] if w.strip()])}")
```

Run the test:
```bash
python3 test_ocr.py
```

---

## Integration Test: End-to-End Document Processing

Test the complete pipeline with a document containing images:

```bash
# Use existing ingestion script with verbose logging
cd /workspace/bms-agent

python3 ingest_documents_to_qdrant.py \
    --file "upload-files/Engineering/BMS-ENGI-FOR-004 Maintenance Manual.pdf" \
    --department "Engineering" \
    --verbose
```

Check Qdrant for indexed artifacts:

```python
# check_qdrant_artifacts.py
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

client = QdrantClient(host="localhost", port=6333)

# Search for chunks with visual artifacts
results = client.scroll(
    collection_name="nomad_bms_documents",
    scroll_filter=Filter(
        must=[
            FieldCondition(
                key="has_visual_artifacts",
                match=MatchValue(value=True)
            )
        ]
    ),
    limit=10
)

print(f"Found {len(results[0])} chunks with visual artifacts")

for point in results[0]:
    payload = point.payload
    print(f"\nChunk: {payload.get('document_name')}")
    print(f"  Artifact count: {payload.get('visual_artifact_count')}")
    print(f"  Artifact IDs: {payload.get('visual_artifact_ids')}")
    if payload.get('image_captions'):
        print(f"  Captions: {payload.get('image_captions')}")
```

Run the check:
```bash
python3 check_qdrant_artifacts.py
```

---

## OpenWebUI Integration Test

### Step 1: Update OpenWebUI Tool

Ensure `bms_search.py` includes artifact display logic:

```python
# In bms_search.py, add to search functions:

def format_result_with_artifacts(result):
    """Add visual artifacts to search result"""
    import base64

    formatted = {
        "text": result['content'],
        "source": result.get('metadata', {}).get('document_name'),
        "quality_score": result.get('metadata', {}).get('quality_score')
    }

    # Check for visual artifacts
    if result.get('metadata', {}).get('has_visual_artifacts'):
        formatted["artifacts"] = []

        artifact_ids = result['metadata'].get('visual_artifact_ids', [])

        for artifact_id in artifact_ids[:3]:  # Limit to first 3 for performance
            # Load artifact from file system
            artifact_path = f"/workspace/visual-artifacts/images/{artifact_id}.png"

            if os.path.exists(artifact_path):
                with open(artifact_path, 'rb') as f:
                    image_bytes = f.read()

                base64_data = base64.b64encode(image_bytes).decode('utf-8')

                formatted["artifacts"].append({
                    "type": "image",
                    "caption": result['metadata'].get('image_captions', ['Image'])[0],
                    "data": f"data:image/png;base64,{base64_data}"
                })

    return formatted
```

### Step 2: Test in OpenWebUI

1. Open OpenWebUI in browser
2. Ask: "Show me brake system diagrams"
3. Verify search results include image artifacts
4. Check that images display correctly inline with text

**Expected Behavior**:
- Text chunk about brake systems appears
- Below text, image of brake system diagram displays
- Caption "Figure 3: Brake System" appears
- Clicking image opens full-resolution view

---

## Performance Testing

### Test Processing Time

```python
# test_performance.py
import time

def test_pptx_processing_time():
    # Time slide rendering for 50-slide presentation
    start = time.time()

    result = processor.process_document('upload-files/Training/large_presentation.pptx', {
        'department': 'Training'
    })

    elapsed = time.time() - start

    print(f"Slides rendered: {result['visual_artifacts_extracted']}")
    print(f"Processing time: {elapsed:.2f} seconds")
    print(f"Average per slide: {elapsed / result['visual_artifacts_extracted']:.2f}s")

    assert elapsed < 300, "Processing exceeded 5 minutes (SC-002)"

test_pptx_processing_time()
```

### Test Image Load Time

```python
# test_image_load_time.py
import time
import base64

def test_artifact_load_time():
    artifact_path = "/workspace/visual-artifacts/images/doc_xyz/page_003_img_001.png"

    start = time.time()

    with open(artifact_path, 'rb') as f:
        image_bytes = f.read()

    base64_image = base64.b64encode(image_bytes).decode('utf-8')

    elapsed = time.time() - start

    print(f"Image size: {len(image_bytes) / 1024:.2f} KB")
    print(f"Base64 size: {len(base64_image) / 1024:.2f} KB")
    print(f"Load + encode time: {elapsed * 1000:.2f} ms")

    assert elapsed < 1.0, "Exceeded 1 second load time (SC-004)"

test_artifact_load_time()
```

---

## Troubleshooting

### Problem: Tesseract OCR Not Found

**Error**: `TesseractNotFoundError: tesseract is not installed`

**Solution**:
```bash
# Verify installation
which tesseract

# Reinstall if missing
apt-get install -y tesseract-ocr tesseract-ocr-eng

# Set path if needed
export TESSERACT_CMD=/usr/bin/tesseract
```

### Problem: LibreOffice Slide Rendering Fails

**Error**: `FileNotFoundError: [Errno 2] No such file or directory: 'soffice'`

**Solution**:
```bash
# Install LibreOffice
apt-get install -y libreoffice-core libreoffice-impress

# Verify
soffice --headless --version

# Check PATH
export PATH=$PATH:/usr/bin
```

### Problem: Images Not Displaying in OpenWebUI

**Symptoms**: Text results show but no images appear

**Debug Steps**:
```python
# Check if artifacts are indexed
from qdrant_client import QdrantClient

client = QdrantClient(host="localhost", port=6333)
result = client.retrieve("nomad_bms_documents", ids=["chunk_001"])

print(result[0].payload.get('has_visual_artifacts'))
print(result[0].payload.get('visual_artifact_ids'))

# Check if files exist
import os
artifact_id = result[0].payload['visual_artifact_ids'][0]
path = f"/workspace/visual-artifacts/images/{artifact_id}.png"
print(f"File exists: {os.path.exists(path)}")
```

### Problem: OCR Confidence Low (< 70%)

**Issue**: OCR text extraction has poor quality

**Solutions**:
```python
# Preprocess image for better OCR
from PIL import Image, ImageEnhance

image = Image.open('diagram.png').convert('L')  # Grayscale
enhancer = ImageEnhance.Contrast(image)
image = enhancer.enhance(2.0)  # Increase contrast

# Apply thresholding
image = image.point(lambda p: p > 128 and 255)

# Run OCR on preprocessed image
ocr_text = pytesseract.image_to_string(image)
```

---

## Next Steps

After successful quickstart:

1. **Ingest Full Document Corpus**: Run batch ingestion on all 300+ documents
   ```bash
   python3 batch_ingest_by_department.py --department Engineering
   ```

2. **Test OpenWebUI Workflows**: Verify artifacts display in all search functions
3. **Monitor Storage**: Check `/workspace/visual-artifacts/` disk usage
4. **Performance Tuning**: Adjust `MAX_IMAGE_WIDTH`, `PPTX_RENDER_DPI` if needed
5. **Review Logs**: Check for extraction errors in `/workspace/logs/processor.log`

---

## Quick Reference

### Environment Variables
```bash
VISUAL_ARTIFACTS_DIR=/workspace/visual-artifacts
MAX_IMAGE_WIDTH=1920
MAX_IMAGE_HEIGHT=1080
MAX_IMAGES_PER_CHUNK=5
ENABLE_OCR=true
OCR_LANGUAGE=eng
PPTX_RENDER_DPI=150
PPTX_RENDER_ENGINE=libreoffice
```

### Key File Locations
- **Artifacts**: `/workspace/visual-artifacts/`
- **Image Extractor**: `bms-agent/scr/image_extractor.py`
- **Enhanced Processor**: `bms-agent/scr/enhanced_document_processor.py`
- **OpenWebUI Tool**: `bms_search.py`

### Useful Commands
```bash
# Check Tesseract
tesseract --version

# Check LibreOffice
soffice --headless --version

# Test OCR
tesseract test_image.png output -l eng

# Convert PPTX to PDF
soffice --headless --convert-to pdf presentation.pptx

# Count artifacts
find /workspace/visual-artifacts -type f | wc -l

# Check Qdrant artifacts
curl -s localhost:6333/collections/nomad_bms_documents | jq
```

---

**Setup Complete!** You're ready to extract images and slides from railway documentation and display them as visual artifacts in OpenWebUI.
