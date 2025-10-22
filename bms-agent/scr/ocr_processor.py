"""
OCR Processor
Handles OCR text extraction from images using Tesseract.
"""

import io
import logging
from typing import Tuple, Dict, Any, Optional
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract

logger = logging.getLogger(__name__)


class OCRProcessor:
    """
    Processes images with Tesseract OCR to extract text content.
    """

    def __init__(self, language: str = "eng", tesseract_cmd: Optional[str] = None):
        """
        Initialize the OCR processor.

        Args:
            language: Tesseract language code (default: 'eng')
            tesseract_cmd: Path to tesseract binary (optional, uses system default)
        """
        self.language = language

        # Set tesseract command path if provided
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

        # Verify Tesseract is available
        try:
            version = pytesseract.get_tesseract_version()
            logger.info(f"OCRProcessor initialized: Tesseract version {version}, language={language}")
        except Exception as e:
            logger.warning(f"Tesseract not available: {e}")

    def extract_text_from_image(
        self,
        image_data: bytes,
        preprocess: bool = True
    ) -> Tuple[str, float]:
        """
        Extract text from an image using OCR.

        Args:
            image_data: Binary image data
            preprocess: Whether to preprocess image for better OCR results

        Returns:
            Tuple of (extracted_text, confidence_score)
        """
        try:
            # Load image
            image = Image.open(io.BytesIO(image_data))

            # Preprocess if requested
            if preprocess:
                image = self.preprocess_for_ocr(image)

            # Run OCR
            text = pytesseract.image_to_string(image, lang=self.language)

            # Get confidence data
            data = pytesseract.image_to_data(image, lang=self.language, output_type=pytesseract.Output.DICT)
            confidences = [c for c in data['conf'] if c != -1]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

            # Normalize confidence to 0-1 range
            confidence_score = avg_confidence / 100.0

            logger.info(
                f"OCR extracted {len(text)} chars with {confidence_score:.2f} confidence"
            )

            return text.strip(), confidence_score

        except pytesseract.TesseractNotFoundError:
            logger.error("Tesseract not installed or not found in PATH")
            return "", 0.0
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            return "", 0.0

    def preprocess_for_ocr(self, image: Image.Image) -> Image.Image:
        """
        Preprocess image to improve OCR accuracy.

        Applies:
        - Grayscale conversion
        - Contrast enhancement
        - Binarization (thresholding)

        Args:
            image: PIL Image object

        Returns:
            Preprocessed PIL Image object
        """
        try:
            # Convert to grayscale
            image = image.convert('L')

            # Enhance contrast
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(2.0)

            # Apply median filter to reduce noise
            image = image.filter(ImageFilter.MedianFilter(size=3))

            # Apply thresholding (binarization)
            # Convert to binary (black and white)
            image = image.point(lambda p: p > 128 and 255)

            logger.debug("Image preprocessed for OCR")
            return image

        except Exception as e:
            logger.warning(f"Preprocessing failed, using original image: {e}")
            return image

    def detect_text_in_image(self, image_data: bytes) -> bool:
        """
        Detect whether an image likely contains text.

        Uses heuristics to determine if OCR is worth running.

        Args:
            image_data: Binary image data

        Returns:
            True if text is likely present, False otherwise
        """
        try:
            image = Image.open(io.BytesIO(image_data))

            # Quick OCR test to detect text
            data = pytesseract.image_to_data(
                image,
                lang=self.language,
                output_type=pytesseract.Output.DICT
            )

            # Count detected words with reasonable confidence
            word_count = sum(1 for conf, text in zip(data['conf'], data['text'])
                           if conf > 30 and text.strip())

            has_text = word_count > 2  # At least 3 words detected

            logger.debug(f"Text detection: {word_count} words found, has_text={has_text}")
            return has_text

        except Exception as e:
            logger.warning(f"Text detection failed: {e}")
            return False

    def get_text_regions(self, image_data: bytes) -> list:
        """
        Get bounding boxes of text regions in the image.

        Args:
            image_data: Binary image data

        Returns:
            List of dict with text regions: [{'text': str, 'bbox': (x, y, w, h), 'conf': float}]
        """
        try:
            image = Image.open(io.BytesIO(image_data))

            # Run OCR with detailed output
            data = pytesseract.image_to_data(
                image,
                lang=self.language,
                output_type=pytesseract.Output.DICT
            )

            regions = []
            n_boxes = len(data['text'])

            for i in range(n_boxes):
                if int(data['conf'][i]) > 30:  # Only include confident detections
                    text = data['text'][i].strip()
                    if text:  # Ignore empty strings
                        region = {
                            'text': text,
                            'bbox': (
                                data['left'][i],
                                data['top'][i],
                                data['width'][i],
                                data['height'][i]
                            ),
                            'conf': data['conf'][i] / 100.0  # Normalize to 0-1
                        }
                        regions.append(region)

            logger.debug(f"Found {len(regions)} text regions")
            return regions

        except Exception as e:
            logger.error(f"Failed to get text regions: {e}")
            return []

    def extract_with_layout(self, image_data: bytes) -> Dict[str, Any]:
        """
        Extract text preserving layout information.

        Args:
            image_data: Binary image data

        Returns:
            Dict with text and layout info
        """
        try:
            image = Image.open(io.BytesIO(image_data))

            # Get detailed OCR output
            hocr = pytesseract.image_to_pdf_or_hocr(image, lang=self.language, extension='hocr')
            text = pytesseract.image_to_string(image, lang=self.language)
            data = pytesseract.image_to_data(image, lang=self.language, output_type=pytesseract.Output.DICT)

            # Calculate word count
            word_count = sum(1 for t in data['text'] if t.strip())

            # Calculate average confidence
            confidences = [c for c in data['conf'] if c != -1]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

            result = {
                'text': text.strip(),
                'word_count': word_count,
                'confidence': avg_confidence / 100.0,
                'hocr': hocr.decode('utf-8') if isinstance(hocr, bytes) else hocr,
                'regions': self.get_text_regions(image_data)
            }

            logger.info(f"Extracted text with layout: {word_count} words")
            return result

        except Exception as e:
            logger.error(f"Layout extraction failed: {e}")
            return {
                'text': '',
                'word_count': 0,
                'confidence': 0.0,
                'hocr': '',
                'regions': []
            }

    def is_tesseract_available(self) -> bool:
        """
        Check if Tesseract is available and functional.

        Returns:
            True if Tesseract is available, False otherwise
        """
        try:
            pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False


if __name__ == "__main__":
    # Test the OCRProcessor
    logging.basicConfig(level=logging.DEBUG)

    ocr = OCRProcessor()

    # Check if Tesseract is available
    if ocr.is_tesseract_available():
        print("Tesseract is available")

        # Create a test image with text
        from PIL import ImageDraw, ImageFont

        test_image = Image.new('RGB', (400, 100), color='white')
        draw = ImageDraw.Draw(test_image)

        # Draw text
        text = "Test OCR Image"
        try:
            # Try to use a larger font if available
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
        except:
            font = ImageFont.load_default()

        draw.text((20, 30), text, fill='black', font=font)

        # Convert to bytes
        output = io.BytesIO()
        test_image.save(output, format='PNG')
        test_data = output.getvalue()

        # Test OCR
        extracted_text, confidence = ocr.extract_text_from_image(test_data)
        print(f"Extracted text: '{extracted_text}'")
        print(f"Confidence: {confidence:.2f}")

        # Test text detection
        has_text = ocr.detect_text_in_image(test_data)
        print(f"Has text: {has_text}")

        # Test text regions
        regions = ocr.get_text_regions(test_data)
        print(f"Text regions: {len(regions)}")

    else:
        print("Tesseract is not available")
