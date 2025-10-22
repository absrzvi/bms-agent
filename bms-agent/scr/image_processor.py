"""
Image Processor
Handles image resizing, optimization, and thumbnail generation.
"""

import io
import logging
from typing import Tuple, Optional
from PIL import Image, ImageOps
from pathlib import Path

logger = logging.getLogger(__name__)


class ImageProcessor:
    """
    Processes images for visual artifacts: resizing, optimization, thumbnail creation.
    """

    def __init__(
        self,
        max_width: int = 1920,
        max_height: int = 1080,
        thumbnail_size: Tuple[int, int] = (400, 300),
        jpeg_quality: int = 85
    ):
        """
        Initialize the image processor.

        Args:
            max_width: Maximum image width in pixels
            max_height: Maximum image height in pixels
            thumbnail_size: Thumbnail dimensions (width, height)
            jpeg_quality: JPEG compression quality (1-100)
        """
        self.max_width = max_width
        self.max_height = max_height
        self.thumbnail_size = thumbnail_size
        self.jpeg_quality = jpeg_quality

        logger.info(
            f"ImageProcessor initialized: max_size={max_width}x{max_height}, "
            f"thumbnail={thumbnail_size}, jpeg_quality={jpeg_quality}"
        )

    def resize_image(
        self,
        image_data: bytes,
        preserve_aspect_ratio: bool = True
    ) -> Tuple[bytes, Tuple[int, int]]:
        """
        Resize an image to fit within max dimensions while preserving aspect ratio.

        Args:
            image_data: Binary image data
            preserve_aspect_ratio: Whether to maintain aspect ratio (default: True)

        Returns:
            Tuple of (resized_image_bytes, (width, height))
        """
        try:
            # Load image from bytes
            image = Image.open(io.BytesIO(image_data))
            original_size = image.size

            logger.debug(f"Original image size: {original_size}")

            # Check if resize is needed
            if original_size[0] <= self.max_width and original_size[1] <= self.max_height:
                logger.debug("Image within size limits, no resize needed")
                return image_data, original_size

            # Calculate new size
            if preserve_aspect_ratio:
                image.thumbnail((self.max_width, self.max_height), Image.Resampling.LANCZOS)
                new_size = image.size
            else:
                new_size = (self.max_width, self.max_height)
                image = image.resize(new_size, Image.Resampling.LANCZOS)

            # Convert back to bytes
            output = io.BytesIO()
            image_format = image.format or "PNG"
            image.save(output, format=image_format)
            resized_data = output.getvalue()

            logger.info(
                f"Resized image: {original_size} → {new_size} "
                f"({len(image_data)} → {len(resized_data)} bytes)"
            )

            return resized_data, new_size

        except Exception as e:
            logger.error(f"Failed to resize image: {e}")
            raise

    def create_thumbnail(self, image_data: bytes) -> bytes:
        """
        Create a compressed thumbnail for preview.

        Args:
            image_data: Binary image data

        Returns:
            Thumbnail image bytes (JPEG format)
        """
        try:
            # Load image
            image = Image.open(io.BytesIO(image_data))

            # Convert to RGB if necessary (for JPEG)
            if image.mode in ('RGBA', 'LA', 'P'):
                # Create white background
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                image = background
            elif image.mode != 'RGB':
                image = image.convert('RGB')

            # Create thumbnail
            image.thumbnail(self.thumbnail_size, Image.Resampling.LANCZOS)

            # Save as JPEG
            output = io.BytesIO()
            image.save(output, format="JPEG", quality=80, optimize=True)
            thumbnail_data = output.getvalue()

            logger.debug(
                f"Created thumbnail: {self.thumbnail_size} ({len(thumbnail_data)} bytes)"
            )

            return thumbnail_data

        except Exception as e:
            logger.error(f"Failed to create thumbnail: {e}")
            raise

    def optimize_image(self, image_data: bytes, target_format: Optional[str] = None) -> bytes:
        """
        Optimize image for storage: format conversion and compression.

        Args:
            image_data: Binary image data
            target_format: Target format (PNG, JPEG, etc.). If None, keep original.

        Returns:
            Optimized image bytes
        """
        try:
            # Load image
            image = Image.open(io.BytesIO(image_data))
            original_format = image.format

            # Determine target format
            if target_format is None:
                target_format = original_format or "PNG"

            # Handle format conversion
            if target_format.upper() == "JPEG":
                # Convert to RGB for JPEG
                if image.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', image.size, (255, 255, 255))
                    if image.mode == 'P':
                        image = image.convert('RGBA')
                    background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                    image = background
                elif image.mode != 'RGB':
                    image = image.convert('RGB')

            # Save with optimization
            output = io.BytesIO()
            if target_format.upper() == "PNG":
                image.save(output, format="PNG", optimize=True)
            elif target_format.upper() == "JPEG":
                image.save(output, format="JPEG", quality=self.jpeg_quality, optimize=True)
            else:
                image.save(output, format=target_format)

            optimized_data = output.getvalue()

            logger.debug(
                f"Optimized image: {original_format} → {target_format} "
                f"({len(image_data)} → {len(optimized_data)} bytes)"
            )

            return optimized_data

        except Exception as e:
            logger.error(f"Failed to optimize image: {e}")
            raise

    def get_image_dimensions(self, image_data: bytes) -> Tuple[int, int]:
        """
        Get image dimensions without loading the full image.

        Args:
            image_data: Binary image data

        Returns:
            Tuple of (width, height)
        """
        try:
            image = Image.open(io.BytesIO(image_data))
            dimensions = image.size
            logger.debug(f"Image dimensions: {dimensions}")
            return dimensions
        except Exception as e:
            logger.error(f"Failed to get image dimensions: {e}")
            raise

    def verify_image_integrity(self, image_data: bytes) -> bool:
        """
        Verify that image data is valid and can be loaded.

        Args:
            image_data: Binary image data

        Returns:
            True if image is valid, False otherwise
        """
        try:
            image = Image.open(io.BytesIO(image_data))
            image.verify()
            logger.debug("Image integrity verified")
            return True
        except Exception as e:
            logger.warning(f"Image integrity check failed: {e}")
            return False

    def detect_image_format(self, image_data: bytes) -> str:
        """
        Detect the image format from binary data.

        Args:
            image_data: Binary image data

        Returns:
            Image format string (e.g., 'PNG', 'JPEG')
        """
        try:
            image = Image.open(io.BytesIO(image_data))
            image_format = image.format or "UNKNOWN"
            logger.debug(f"Detected image format: {image_format}")
            return image_format
        except Exception as e:
            logger.error(f"Failed to detect image format: {e}")
            return "UNKNOWN"

    def auto_orient_image(self, image_data: bytes) -> bytes:
        """
        Automatically orient image based on EXIF data.

        Args:
            image_data: Binary image data

        Returns:
            Re-oriented image bytes
        """
        try:
            image = Image.open(io.BytesIO(image_data))

            # Apply EXIF orientation
            image = ImageOps.exif_transpose(image)

            # Convert back to bytes
            output = io.BytesIO()
            image_format = image.format or "PNG"
            image.save(output, format=image_format)
            oriented_data = output.getvalue()

            logger.debug("Applied auto-orientation")
            return oriented_data

        except Exception as e:
            logger.warning(f"Auto-orientation failed, returning original: {e}")
            return image_data


if __name__ == "__main__":
    # Test the ImageProcessor
    logging.basicConfig(level=logging.DEBUG)

    processor = ImageProcessor()

    # Test with a simple image
    test_image = Image.new('RGB', (2000, 1500), color='red')
    output = io.BytesIO()
    test_image.save(output, format='PNG')
    test_data = output.getvalue()

    print(f"Original size: {len(test_data)} bytes")

    # Test resize
    resized_data, new_size = processor.resize_image(test_data)
    print(f"Resized to: {new_size}, {len(resized_data)} bytes")

    # Test thumbnail
    thumbnail_data = processor.create_thumbnail(test_data)
    print(f"Thumbnail size: {len(thumbnail_data)} bytes")

    # Test optimize
    optimized_data = processor.optimize_image(test_data, "JPEG")
    print(f"Optimized size: {len(optimized_data)} bytes")

    # Test integrity
    is_valid = processor.verify_image_integrity(test_data)
    print(f"Image valid: {is_valid}")
