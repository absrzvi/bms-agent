"""
Proximity Associator
Associates extracted images with text chunks based on proximity and caption matching.
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ImageArtifact:
    """Represents an extracted image artifact."""
    artifact_id: str
    page_number: int
    bbox: Optional[Dict[str, float]]  # {x, y, width, height}
    caption: Optional[str]
    position: int  # Index on page


@dataclass
class TextChunk:
    """Represents a text chunk to associate with images."""
    chunk_id: str
    page_number: Optional[int]
    text: str
    position: int  # Index in document


class ProximityAssociator:
    """
    Associates images with text chunks using:
    1. Proximity-based matching (same page, bounding box distance)
    2. Caption-based matching (figure references in text)
    """

    def __init__(self, max_images_per_chunk: int = 5):
        """
        Initialize the proximity associator.

        Args:
            max_images_per_chunk: Maximum images to associate per chunk (default: 5)
        """
        self.max_images_per_chunk = max_images_per_chunk
        logger.info(f"ProximityAssociator initialized: max_images={max_images_per_chunk}")

    def associate_images_with_chunks(
        self,
        images: List[ImageArtifact],
        chunks: List[TextChunk]
    ) -> Dict[str, List[str]]:
        """
        Associate images with text chunks.

        Args:
            images: List of ImageArtifact objects
            chunks: List of TextChunk objects

        Returns:
            Dict mapping chunk_id -> list of artifact_ids
        """
        associations = {}

        # First pass: Caption-based matching (highest priority)
        caption_matches = self._match_by_captions(images, chunks)
        associations.update(caption_matches)

        # Second pass: Proximity-based matching for remaining images
        proximity_matches = self._match_by_proximity(images, chunks, caption_matches)

        # Merge proximity matches with caption matches
        for chunk_id, artifact_ids in proximity_matches.items():
            if chunk_id in associations:
                # Combine and deduplicate
                existing = set(associations[chunk_id])
                existing.update(artifact_ids)
                associations[chunk_id] = list(existing)[:self.max_images_per_chunk]
            else:
                associations[chunk_id] = artifact_ids[:self.max_images_per_chunk]

        # Log statistics
        total_associated = sum(len(ids) for ids in associations.values())
        logger.info(
            f"Associated {total_associated} images with {len(associations)} chunks "
            f"(avg {total_associated/len(associations):.1f} per chunk)" if associations else
            "No image associations created"
        )

        return associations

    def _match_by_captions(
        self,
        images: List[ImageArtifact],
        chunks: List[TextChunk]
    ) -> Dict[str, List[str]]:
        """
        Match images to chunks based on caption references in text.

        Args:
            images: List of image artifacts
            chunks: List of text chunks

        Returns:
            Dict mapping chunk_id -> list of artifact_ids
        """
        associations = {}

        # Build caption index
        caption_to_artifact = {}
        for img in images:
            if img.caption:
                # Extract figure numbers from captions
                figure_refs = self.extract_figure_references(img.caption)
                for ref in figure_refs:
                    caption_to_artifact[ref] = img.artifact_id

        # Match chunks that reference these figures
        for chunk in chunks:
            figure_refs = self.extract_figure_references(chunk.text)

            matched_artifacts = []
            for ref in figure_refs:
                if ref in caption_to_artifact:
                    matched_artifacts.append(caption_to_artifact[ref])

            if matched_artifacts:
                associations[chunk.chunk_id] = matched_artifacts[:self.max_images_per_chunk]
                logger.debug(
                    f"Caption match: chunk {chunk.chunk_id} -> "
                    f"{len(matched_artifacts)} images via {figure_refs}"
                )

        return associations

    def _match_by_proximity(
        self,
        images: List[ImageArtifact],
        chunks: List[TextChunk],
        exclude_matches: Dict[str, List[str]]
    ) -> Dict[str, List[str]]:
        """
        Match images to chunks based on page proximity.

        Args:
            images: List of image artifacts
            chunks: List of text chunks
            exclude_matches: Already matched chunk->artifact pairs to exclude

        Returns:
            Dict mapping chunk_id -> list of artifact_ids
        """
        associations = {}

        # Get already matched artifact IDs
        already_matched = set()
        for artifact_ids in exclude_matches.values():
            already_matched.update(artifact_ids)

        # Group chunks by page
        chunks_by_page = {}
        for chunk in chunks:
            if chunk.page_number:
                if chunk.page_number not in chunks_by_page:
                    chunks_by_page[chunk.page_number] = []
                chunks_by_page[chunk.page_number].append(chunk)

        # Group images by page
        images_by_page = {}
        for img in images:
            if img.artifact_id not in already_matched:
                if img.page_number not in images_by_page:
                    images_by_page[img.page_number] = []
                images_by_page[img.page_number].append(img)

        # Match images to chunks on same page
        for page_num in images_by_page:
            if page_num not in chunks_by_page:
                # No chunks on this page, try adjacent pages
                for offset in [-1, 1]:
                    adj_page = page_num + offset
                    if adj_page in chunks_by_page:
                        self._associate_page_images(
                            images_by_page[page_num],
                            chunks_by_page[adj_page],
                            associations
                        )
                        break
            else:
                # Associate images with chunks on same page
                self._associate_page_images(
                    images_by_page[page_num],
                    chunks_by_page[page_num],
                    associations
                )

        return associations

    def _associate_page_images(
        self,
        images: List[ImageArtifact],
        chunks: List[TextChunk],
        associations: Dict[str, List[str]]
    ) -> None:
        """
        Associate images with chunks on the same page.

        Args:
            images: Images on this page
            chunks: Chunks on this page
            associations: Dict to update with associations
        """
        if not images or not chunks:
            return

        # If bounding box info is available, use distance calculation
        if images[0].bbox:
            for img in images:
                best_chunk = None
                min_distance = float('inf')

                for chunk in chunks:
                    distance = self.calculate_bbox_distance(img.bbox, chunk.position)
                    if distance < min_distance:
                        min_distance = distance
                        best_chunk = chunk

                if best_chunk:
                    if best_chunk.chunk_id not in associations:
                        associations[best_chunk.chunk_id] = []
                    associations[best_chunk.chunk_id].append(img.artifact_id)
                    logger.debug(
                        f"Proximity match: chunk {best_chunk.chunk_id} -> "
                        f"image {img.artifact_id} (distance={min_distance:.1f})"
                    )
        else:
            # No bbox info, associate images with chunks by position
            # Distribute images among chunks evenly
            for idx, img in enumerate(images):
                chunk_idx = min(idx, len(chunks) - 1)
                chunk = chunks[chunk_idx]

                if chunk.chunk_id not in associations:
                    associations[chunk.chunk_id] = []
                associations[chunk.chunk_id].append(img.artifact_id)

                logger.debug(
                    f"Position match: chunk {chunk.chunk_id} -> "
                    f"image {img.artifact_id} (position {idx})"
                )

    def calculate_bbox_distance(
        self,
        bbox: Dict[str, float],
        chunk_position: int
    ) -> float:
        """
        Calculate distance between image bounding box and chunk position.

        Args:
            bbox: Image bounding box {x, y, width, height}
            chunk_position: Chunk position index

        Returns:
            Distance score (lower is closer)
        """
        if not bbox:
            return float('inf')

        # Simple heuristic: Use vertical position (y-coordinate)
        # Lower y values are higher on page, closer to beginning of document
        # Weight by chunk position
        image_y = bbox.get('y', 0)

        # Normalize distance based on chunk position
        # Images near the top of page should match early chunks
        distance = abs(image_y - (chunk_position * 100))

        return distance

    def extract_figure_references(self, text: str) -> List[str]:
        """
        Extract figure references from text.

        Matches patterns like:
        - "Figure 1", "Fig. 2", "Figure 3.4"
        - "Image 1", "Img 2"
        - "Diagram 1", "Schema 2"

        Args:
            text: Text to search

        Returns:
            List of normalized figure references (e.g., ['fig_1', 'fig_2'])
        """
        if not text:
            return []

        references = []

        # Patterns to match
        patterns = [
            r'\b(?:Figure|Fig\.?)\s+(\d+(?:\.\d+)?)',
            r'\b(?:Image|Img\.?)\s+(\d+(?:\.\d+)?)',
            r'\b(?:Diagram|Diag\.?)\s+(\d+(?:\.\d+)?)',
            r'\b(?:Schema|Schematic)\s+(\d+(?:\.\d+)?)',
            r'\b(?:Table|Tbl\.?)\s+(\d+(?:\.\d+)?)',
            r'\b(?:Chart)\s+(\d+(?:\.\d+)?)',
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                number = match.group(1).replace('.', '_')
                ref_type = match.group(0).split()[0].lower()
                normalized = f"{ref_type}_{number}"
                references.append(normalized)

        logger.debug(f"Extracted figure references: {references}")
        return list(set(references))  # Remove duplicates

    def extract_caption(
        self,
        text: str,
        window_size: int = 200
    ) -> Optional[str]:
        """
        Extract caption from text near an image.

        Args:
            text: Surrounding text
            window_size: Characters to search for caption

        Returns:
            Extracted caption or None
        """
        # Look for caption patterns at start of text window
        caption_text = text[:window_size]

        # Common caption patterns
        patterns = [
            r'(?:Figure|Fig\.?|Image|Diagram)\s+\d+[:.]\s*(.+?)(?:\.|$)',
            r'Caption:\s*(.+?)(?:\.|$)',
        ]

        for pattern in patterns:
            match = re.search(pattern, caption_text, re.IGNORECASE)
            if match:
                caption = match.group(1).strip()
                if len(caption) > 10:  # Minimum caption length
                    logger.debug(f"Extracted caption: {caption[:50]}...")
                    return caption

        return None


if __name__ == "__main__":
    # Test the ProximityAssociator
    logging.basicConfig(level=logging.DEBUG)

    associator = ProximityAssociator()

    # Test figure reference extraction
    test_text = "As shown in Figure 1, the hydraulic system uses a valve. See Fig. 2 for details."
    refs = associator.extract_figure_references(test_text)
    print(f"Figure references: {refs}")

    # Test caption extraction
    test_caption = "Figure 3: Brake System Diagram. This shows the main components."
    caption = associator.extract_caption(test_caption)
    print(f"Extracted caption: {caption}")

    # Test association
    images = [
        ImageArtifact("img_1", page_number=1, bbox={'x': 100, 'y': 200, 'width': 300, 'height': 200}, caption="Figure 1: Test", position=0),
        ImageArtifact("img_2", page_number=1, bbox={'x': 100, 'y': 600, 'width': 300, 'height': 200}, caption="Figure 2: Test", position=1),
    ]

    chunks = [
        TextChunk("chunk_1", page_number=1, text="Refer to Figure 1 for details", position=0),
        TextChunk("chunk_2", page_number=1, text="As seen in Fig. 2, the system works", position=1),
    ]

    associations = associator.associate_images_with_chunks(images, chunks)
    print(f"Associations: {associations}")
