"""
Artifact Storage Manager
Handles file system storage and retrieval of visual artifacts (images/slides).
"""

import os
import uuid
import shutil
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class ArtifactStorageManager:
    """
    Manages persistent storage of visual artifacts in the file system.
    Handles artifact saving, loading, path generation, and cleanup.
    """

    def __init__(self, base_dir: str = "/workspace/visual-artifacts"):
        """
        Initialize the storage manager.

        Args:
            base_dir: Base directory for artifact storage (default: /workspace/visual-artifacts)
        """
        self.base_dir = Path(base_dir)
        self.images_dir = self.base_dir / "images"
        self.slides_dir = self.base_dir / "slides"
        self.thumbnails_dir = self.base_dir / "thumbnails"

        # Ensure directories exist
        self.ensure_directories_exist()

        logger.info(f"ArtifactStorageManager initialized with base_dir: {self.base_dir}")

    def ensure_directories_exist(self) -> None:
        """Create storage directories if they don't exist."""
        for directory in [self.images_dir, self.slides_dir, self.thumbnails_dir]:
            directory.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Ensured directory exists: {directory}")

    def generate_artifact_id(self, artifact_type: str = "img") -> str:
        """
        Generate a unique artifact ID.

        Args:
            artifact_type: Type prefix ('img' for images, 'slide' for slides)

        Returns:
            Unique artifact ID (e.g., 'img_abc123def')
        """
        unique_id = uuid.uuid4().hex[:12]
        artifact_id = f"{artifact_type}_{unique_id}"
        logger.debug(f"Generated artifact ID: {artifact_id}")
        return artifact_id

    def get_artifact_path(
        self,
        artifact_id: str,
        artifact_type: str,
        document_id: str,
        file_format: str = "png"
    ) -> Path:
        """
        Get the file path for an artifact.

        Args:
            artifact_id: Unique artifact identifier
            artifact_type: 'image' or 'slide'
            document_id: Source document identifier
            file_format: Image format (png, jpeg, etc.)

        Returns:
            Path object for the artifact file
        """
        if artifact_type == "image":
            doc_dir = self.images_dir / f"doc_{document_id}"
        elif artifact_type == "slide":
            doc_dir = self.slides_dir / f"pres_{document_id}"
        else:
            raise ValueError(f"Invalid artifact_type: {artifact_type}")

        doc_dir.mkdir(parents=True, exist_ok=True)
        return doc_dir / f"{artifact_id}.{file_format}"

    def get_thumbnail_path(self, artifact_id: str, file_format: str = "jpg") -> Path:
        """
        Get the file path for an artifact thumbnail.

        Args:
            artifact_id: Unique artifact identifier
            file_format: Thumbnail format (default: jpg)

        Returns:
            Path object for the thumbnail file
        """
        return self.thumbnails_dir / f"thumb_{artifact_id}.{file_format}"

    def save_artifact(
        self,
        image_data: bytes,
        artifact_id: str,
        artifact_type: str,
        document_id: str,
        file_format: str = "png",
        save_thumbnail: bool = False,
        thumbnail_data: Optional[bytes] = None
    ) -> Dict[str, Any]:
        """
        Save an artifact to the file system.

        Args:
            image_data: Binary image data
            artifact_id: Unique artifact identifier
            artifact_type: 'image' or 'slide'
            document_id: Source document identifier
            file_format: Image format
            save_thumbnail: Whether to save a thumbnail
            thumbnail_data: Binary thumbnail data (optional)

        Returns:
            Dict with artifact metadata (file_path, file_size_bytes, etc.)
        """
        # Get artifact path
        artifact_path = self.get_artifact_path(
            artifact_id, artifact_type, document_id, file_format
        )

        # Write artifact file
        artifact_path.write_bytes(image_data)
        file_size = artifact_path.stat().st_size

        logger.info(f"Saved artifact: {artifact_path} ({file_size} bytes)")

        result = {
            "artifact_id": artifact_id,
            "file_path": str(artifact_path),
            "file_size_bytes": file_size,
            "file_format": file_format,
            "extraction_timestamp": datetime.utcnow().isoformat() + "Z"
        }

        # Save thumbnail if requested
        if save_thumbnail and thumbnail_data:
            thumbnail_path = self.get_thumbnail_path(artifact_id, "jpg")
            thumbnail_path.write_bytes(thumbnail_data)
            result["thumbnail_path"] = str(thumbnail_path)
            logger.debug(f"Saved thumbnail: {thumbnail_path}")

        return result

    def load_artifact(self, artifact_path: str) -> bytes:
        """
        Load an artifact from the file system.

        Args:
            artifact_path: Absolute path to the artifact file

        Returns:
            Binary image data

        Raises:
            FileNotFoundError: If artifact file doesn't exist
        """
        path = Path(artifact_path)
        if not path.exists():
            raise FileNotFoundError(f"Artifact not found: {artifact_path}")

        image_data = path.read_bytes()
        logger.debug(f"Loaded artifact: {artifact_path} ({len(image_data)} bytes)")
        return image_data

    def artifact_exists(self, artifact_path: str) -> bool:
        """
        Check if an artifact file exists.

        Args:
            artifact_path: Absolute path to the artifact file

        Returns:
            True if file exists, False otherwise
        """
        return Path(artifact_path).exists()

    def check_disk_space(self, min_free_gb: float = 10.0) -> Dict[str, Any]:
        """
        Check available disk space in the artifacts directory.

        Args:
            min_free_gb: Minimum free space in GB (default: 10GB)

        Returns:
            Dict with disk space info and status
        """
        stat = os.statvfs(self.base_dir)
        free_bytes = stat.f_bavail * stat.f_frsize
        free_gb = free_bytes / (1024 ** 3)
        total_bytes = stat.f_blocks * stat.f_frsize
        total_gb = total_bytes / (1024 ** 3)

        has_space = free_gb >= min_free_gb

        result = {
            "free_gb": round(free_gb, 2),
            "total_gb": round(total_gb, 2),
            "has_sufficient_space": has_space,
            "min_required_gb": min_free_gb
        }

        if not has_space:
            logger.warning(
                f"Low disk space: {free_gb:.2f}GB free (minimum: {min_free_gb}GB)"
            )

        return result

    def cleanup_orphaned_artifacts(self, valid_artifact_ids: set) -> Dict[str, int]:
        """
        Remove artifact files that are not referenced in the database.

        Args:
            valid_artifact_ids: Set of artifact IDs that should exist

        Returns:
            Dict with cleanup statistics
        """
        removed_count = 0
        removed_bytes = 0

        # Check all artifact directories
        for artifact_dir in [self.images_dir, self.slides_dir]:
            if not artifact_dir.exists():
                continue

            # Iterate through document subdirectories
            for doc_dir in artifact_dir.iterdir():
                if not doc_dir.is_dir():
                    continue

                # Check each artifact file
                for artifact_file in doc_dir.iterdir():
                    if not artifact_file.is_file():
                        continue

                    # Extract artifact ID from filename
                    artifact_id = artifact_file.stem

                    # Remove if not in valid set
                    if artifact_id not in valid_artifact_ids:
                        file_size = artifact_file.stat().st_size
                        artifact_file.unlink()
                        removed_count += 1
                        removed_bytes += file_size
                        logger.info(f"Removed orphaned artifact: {artifact_file}")

        result = {
            "removed_count": removed_count,
            "removed_bytes": removed_bytes,
            "removed_mb": round(removed_bytes / (1024 ** 2), 2)
        }

        logger.info(
            f"Cleanup complete: {removed_count} orphaned artifacts removed "
            f"({result['removed_mb']}MB freed)"
        )

        return result

    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get storage statistics for visual artifacts.

        Returns:
            Dict with counts and sizes for images and slides
        """
        stats = {
            "images": {"count": 0, "total_bytes": 0},
            "slides": {"count": 0, "total_bytes": 0},
            "thumbnails": {"count": 0, "total_bytes": 0}
        }

        # Count images
        if self.images_dir.exists():
            for doc_dir in self.images_dir.iterdir():
                if doc_dir.is_dir():
                    for file in doc_dir.iterdir():
                        if file.is_file():
                            stats["images"]["count"] += 1
                            stats["images"]["total_bytes"] += file.stat().st_size

        # Count slides
        if self.slides_dir.exists():
            for pres_dir in self.slides_dir.iterdir():
                if pres_dir.is_dir():
                    for file in pres_dir.iterdir():
                        if file.is_file():
                            stats["slides"]["count"] += 1
                            stats["slides"]["total_bytes"] += file.stat().st_size

        # Count thumbnails
        if self.thumbnails_dir.exists():
            for file in self.thumbnails_dir.iterdir():
                if file.is_file():
                    stats["thumbnails"]["count"] += 1
                    stats["thumbnails"]["total_bytes"] += file.stat().st_size

        # Add human-readable sizes
        for category in stats.values():
            category["total_mb"] = round(category["total_bytes"] / (1024 ** 2), 2)

        return stats


if __name__ == "__main__":
    # Test the ArtifactStorageManager
    logging.basicConfig(level=logging.DEBUG)

    storage = ArtifactStorageManager()

    # Test artifact ID generation
    artifact_id = storage.generate_artifact_id("img")
    print(f"Generated artifact ID: {artifact_id}")

    # Test path generation
    path = storage.get_artifact_path(artifact_id, "image", "test_doc", "png")
    print(f"Artifact path: {path}")

    # Test disk space check
    disk_info = storage.check_disk_space()
    print(f"Disk space: {disk_info}")

    # Test storage stats
    stats = storage.get_storage_stats()
    print(f"Storage stats: {stats}")
