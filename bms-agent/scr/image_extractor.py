"""
Image Extractor
Extracts images from PDF, DOCX documents and renders PPTX slides as images.
"""

import io
import os
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from PIL import Image
import fitz  # PyMuPDF
from docx import Document
from pptx import Presentation
from pdf2image import convert_from_path, convert_from_bytes

logger = logging.getLogger(__name__)


class ImageExtractor:
    """
    Extracts visual artifacts from documents:
    - PDF: Embedded images via PyMuPDF
    - DOCX: Inline and floating images via python-docx
    - PPTX: Rendered slides via LibreOffice + pdf2image
    """

    def __init__(self, pptx_render_dpi: int = 150):
        """
        Initialize the image extractor.

        Args:
            pptx_render_dpi: DPI for PPTX slide rendering (default: 150)
        """
        self.pptx_render_dpi = pptx_render_dpi
        logger.info(f"ImageExtractor initialized: pptx_dpi={pptx_render_dpi}")

    def extract_images_from_pdf(
        self,
        pdf_path: str,
        use_fallback: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Extract embedded images from a PDF document.

        Args:
            pdf_path: Path to PDF file
            use_fallback: Use pdf2image fallback if PyMuPDF fails (for scanned PDFs)

        Returns:
            List of dicts with image data and metadata
        """
        images = []

        try:
            # Open PDF with PyMuPDF
            doc = fitz.open(pdf_path)

            for page_num, page in enumerate(doc, start=1):
                try:
                    # Get list of images on this page
                    image_list = page.get_images(full=True)

                    for img_index, img in enumerate(image_list):
                        try:
                            # Extract image
                            xref = img[0]
                            base_image = doc.extract_image(xref)

                            image_bytes = base_image['image']
                            image_ext = base_image['ext']

                            # Get bounding box if available
                            try:
                                bbox = page.get_image_bbox(img)
                                bbox_dict = {
                                    'x': bbox.x0,
                                    'y': bbox.y0,
                                    'width': bbox.width,
                                    'height': bbox.height
                                }
                            except:
                                bbox_dict = None

                            # Get image dimensions
                            try:
                                pil_image = Image.open(io.BytesIO(image_bytes))
                                dimensions = {
                                    'width': pil_image.width,
                                    'height': pil_image.height
                                }
                            except:
                                dimensions = {'width': 0, 'height': 0}

                            images.append({
                                'image_bytes': image_bytes,
                                'format': image_ext,
                                'page_number': page_num,
                                'position': img_index,
                                'bbox': bbox_dict,
                                'dimensions': dimensions
                            })

                            logger.debug(
                                f"Extracted image from page {page_num}, "
                                f"position {img_index}: {image_ext}, "
                                f"{dimensions['width']}x{dimensions['height']}"
                            )

                        except Exception as e:
                            logger.warning(
                                f"Failed to extract image on page {page_num}, "
                                f"position {img_index}: {e}"
                            )
                            continue

                except Exception as e:
                    logger.warning(f"Failed to process page {page_num}: {e}")
                    continue

            doc.close()

            logger.info(f"Extracted {len(images)} images from PDF using PyMuPDF")

            # Fallback to pdf2image for scanned PDFs if no images found
            if len(images) == 0 and use_fallback:
                logger.info("No embedded images found, trying pdf2image fallback")
                images = self._extract_pdf_fallback(pdf_path)

            return images

        except Exception as e:
            logger.error(f"PDF image extraction failed: {e}")
            if use_fallback:
                logger.info("Attempting pdf2image fallback due to error")
                return self._extract_pdf_fallback(pdf_path)
            return []

    def _extract_pdf_fallback(self, pdf_path: str) -> List[Dict[str, Any]]:
        """
        Fallback method using pdf2image to render PDF pages as images.

        Args:
            pdf_path: Path to PDF file

        Returns:
            List of dicts with rendered page images
        """
        images = []

        try:
            # Convert PDF pages to images
            pil_images = convert_from_path(pdf_path, dpi=self.pptx_render_dpi)

            for page_num, pil_image in enumerate(pil_images, start=1):
                # Convert PIL image to bytes
                output = io.BytesIO()
                pil_image.save(output, format='PNG')
                image_bytes = output.getvalue()

                images.append({
                    'image_bytes': image_bytes,
                    'format': 'png',
                    'page_number': page_num,
                    'position': 0,
                    'bbox': None,
                    'dimensions': {
                        'width': pil_image.width,
                        'height': pil_image.height
                    },
                    'is_rendered_page': True  # Flag to indicate this is a full page render
                })

            logger.info(f"Rendered {len(images)} PDF pages as images (fallback)")
            return images

        except Exception as e:
            logger.error(f"PDF fallback extraction failed: {e}")
            return []

    def extract_images_from_docx(self, docx_path: str) -> List[Dict[str, Any]]:
        """
        Extract images from a DOCX document.

        Args:
            docx_path: Path to DOCX file

        Returns:
            List of dicts with image data and metadata
        """
        images = []

        try:
            doc = Document(docx_path)

            # Extract inline images from runs
            for para_idx, para in enumerate(doc.paragraphs):
                for run_idx, run in enumerate(para.runs):
                    # Check for inline images
                    if run._element.xpath('.//a:blip'):
                        for blip in run._element.xpath('.//a:blip'):
                            try:
                                # Get image relationship ID
                                rId = blip.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')

                                # Get image part
                                image_part = doc.part.related_parts[rId]
                                image_bytes = image_part.blob

                                # Determine format
                                content_type = image_part.content_type
                                if 'png' in content_type:
                                    image_ext = 'png'
                                elif 'jpeg' in content_type or 'jpg' in content_type:
                                    image_ext = 'jpeg'
                                elif 'gif' in content_type:
                                    image_ext = 'gif'
                                else:
                                    image_ext = 'unknown'

                                # Get dimensions
                                try:
                                    pil_image = Image.open(io.BytesIO(image_bytes))
                                    dimensions = {
                                        'width': pil_image.width,
                                        'height': pil_image.height
                                    }
                                except:
                                    dimensions = {'width': 0, 'height': 0}

                                # Get caption from paragraph text
                                caption = para.text.strip() if para.text else None

                                images.append({
                                    'image_bytes': image_bytes,
                                    'format': image_ext,
                                    'paragraph_index': para_idx,
                                    'position': run_idx,
                                    'caption': caption,
                                    'dimensions': dimensions
                                })

                                logger.debug(
                                    f"Extracted image from paragraph {para_idx}: "
                                    f"{image_ext}, {dimensions['width']}x{dimensions['height']}"
                                )

                            except Exception as e:
                                logger.warning(f"Failed to extract inline image: {e}")
                                continue

            logger.info(f"Extracted {len(images)} images from DOCX")
            return images

        except Exception as e:
            logger.error(f"DOCX image extraction failed: {e}")
            return []

    def render_pptx_slides(
        self,
        pptx_path: str,
        use_libreoffice: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Render PowerPoint slides as static PNG images.

        Args:
            pptx_path: Path to PPTX file
            use_libreoffice: Use LibreOffice headless for rendering (default: True)

        Returns:
            List of dicts with slide image data and metadata
        """
        slides = []

        if use_libreoffice and self._is_libreoffice_available():
            slides = self._render_pptx_libreoffice(pptx_path)
        else:
            logger.warning(
                "LibreOffice not available or disabled, "
                "slide rendering not possible"
            )
            slides = []

        return slides

    def _is_libreoffice_available(self) -> bool:
        """
        Check if LibreOffice soffice command is available.

        Returns:
            True if soffice is available, False otherwise
        """
        try:
            result = subprocess.run(
                ['soffice', '--headless', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            available = result.returncode == 0
            if available:
                logger.debug(f"LibreOffice available: {result.stdout.strip()}")
            return available
        except Exception as e:
            logger.debug(f"LibreOffice not available: {e}")
            return False

    def _render_pptx_libreoffice(self, pptx_path: str) -> List[Dict[str, Any]]:
        """
        Render PPTX slides using LibreOffice headless + pdf2image.

        Args:
            pptx_path: Path to PPTX file

        Returns:
            List of dicts with rendered slide images
        """
        slides = []

        try:
            # Get slide count first
            try:
                prs = Presentation(pptx_path)
                slide_count = len(prs.slides)
                logger.info(f"PPTX contains {slide_count} slides")
            except:
                slide_count = 0

            # Create temporary directory for conversion
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)

                # Convert PPTX to PDF using LibreOffice
                logger.info(f"Converting PPTX to PDF using LibreOffice")
                result = subprocess.run(
                    [
                        'soffice',
                        '--headless',
                        '--convert-to', 'pdf',
                        '--outdir', str(temp_path),
                        pptx_path
                    ],
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minutes timeout
                )

                if result.returncode != 0:
                    logger.error(f"LibreOffice conversion failed: {result.stderr}")
                    return []

                # Find generated PDF
                pdf_files = list(temp_path.glob('*.pdf'))
                if not pdf_files:
                    logger.error("No PDF generated by LibreOffice")
                    return []

                pdf_path = pdf_files[0]
                logger.info(f"Generated PDF: {pdf_path}")

                # Convert PDF pages to images using pdf2image
                pil_images = convert_from_path(
                    str(pdf_path),
                    dpi=self.pptx_render_dpi
                )

                for slide_num, pil_image in enumerate(pil_images, start=1):
                    # Convert PIL image to bytes
                    output = io.BytesIO()
                    pil_image.save(output, format='PNG')
                    image_bytes = output.getvalue()

                    slides.append({
                        'image_bytes': image_bytes,
                        'format': 'png',
                        'slide_number': slide_num,
                        'total_slides': len(pil_images),
                        'dimensions': {
                            'width': pil_image.width,
                            'height': pil_image.height
                        }
                    })

                    logger.debug(
                        f"Rendered slide {slide_num}/{len(pil_images)}: "
                        f"{pil_image.width}x{pil_image.height}"
                    )

            logger.info(f"Rendered {len(slides)} slides from PPTX")
            return slides

        except subprocess.TimeoutExpired:
            logger.error("LibreOffice conversion timeout (exceeded 5 minutes)")
            return []
        except Exception as e:
            logger.error(f"PPTX slide rendering failed: {e}")
            return []


if __name__ == "__main__":
    # Test the ImageExtractor
    logging.basicConfig(level=logging.DEBUG)

    extractor = ImageExtractor()

    # Test LibreOffice availability
    if extractor._is_libreoffice_available():
        print("✓ LibreOffice is available")
    else:
        print("✗ LibreOffice is not available")

    # Test with sample files (if they exist)
    test_pdf = "/workspace/bms-agent/upload-files/Engineering/BMS-ENGI-FOR-004 Maintenance Manual.pdf"
    if os.path.exists(test_pdf):
        print(f"\nTesting PDF extraction: {test_pdf}")
        images = extractor.extract_images_from_pdf(test_pdf)
        print(f"Extracted {len(images)} images from PDF")
        if images:
            print(f"First image: page {images[0]['page_number']}, "
                  f"format {images[0]['format']}, "
                  f"dimensions {images[0]['dimensions']}")
