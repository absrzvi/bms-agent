#!/usr/bin/env python3
"""
Update Document URLs in Qdrant Database

This script updates the document_url metadata field for documents in Qdrant.
Useful for fixing documents that have null or incorrect URLs.

Usage:
    # Update single document
    python update_document_urls.py --document "BMS-PROJ-FOR-028 Project Traceability Matrix.xlsx" \
                                    --url "https://nomadrail.sharepoint.com/qms/..."

    # Batch update from JSON file
    python update_document_urls.py --mapping url_mapping.json

    # Interactive mode (prompts for each document from missing_urls.txt)
    python update_document_urls.py --interactive --source /workspace/002-n8n/documents_missing_urls.txt

    # Dry run (preview changes without applying)
    python update_document_urls.py --mapping url_mapping.json --dry-run
"""

import argparse
import json
import logging
import sys
from typing import Dict, List, Tuple, Optional
from urllib.parse import urlparse

import requests

# Configuration
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
QDRANT_URL = f"http://{QDRANT_HOST}:{QDRANT_PORT}"
COLLECTION_NAME = "nomad_bms_documents"

# Valid SharePoint domains
VALID_DOMAINS = [
    "nomadrail.sharepoint.com"
]

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def validate_url(url: str) -> Tuple[bool, str]:
    """
    Validate SharePoint URL format.

    Args:
        url: URL to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not url or url.strip() == "":
        return False, "URL is empty"

    if url.lower() in ["null", "none", "n/a", ""]:
        return False, "URL is placeholder value"

    try:
        parsed = urlparse(url)

        # Check protocol
        if parsed.scheme not in ["http", "https"]:
            return False, f"Invalid protocol: {parsed.scheme} (must be http or https)"

        # Check domain
        if parsed.netloc not in VALID_DOMAINS:
            return False, f"Invalid domain: {parsed.netloc} (must be one of {VALID_DOMAINS})"

        # Check path exists
        if not parsed.path or parsed.path == "/":
            return False, "URL has no path (must point to specific document)"

        return True, ""

    except Exception as e:
        return False, f"URL parsing error: {str(e)}"


def get_points_for_document(document_name: str, fuzzy: bool = True) -> List[Dict]:
    """
    Get all Qdrant points (chunks) for a specific document.

    Args:
        document_name: Name of the document (e.g., "BMS-PROJ-FOR-028 Project Traceability Matrix.xlsx")
        fuzzy: If True, use partial matching (handles timestamps, extensions). Default: True

    Returns:
        List of points matching the document
    """
    try:
        # Remove file extension for fuzzy matching
        search_name = document_name
        if fuzzy:
            # Remove common file extensions
            for ext in ['.pdf', '.docx', '.xlsx', '.pptx', '.doc', '.xls', '.ppt']:
                if search_name.lower().endswith(ext):
                    search_name = search_name[:-len(ext)]
                    break

        # Get all points and filter in-memory for fuzzy matching
        # (Qdrant doesn't support "contains" filters directly in all versions)
        response = requests.post(
            f"{QDRANT_URL}/collections/{COLLECTION_NAME}/points/scroll",
            json={
                "limit": 10000,  # High limit to get all chunks
                "with_payload": True,
                "with_vector": False
            },
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            all_points = data.get("result", {}).get("points", [])

            # Filter points by document_id
            if fuzzy:
                # Partial match: document_id contains search_name
                matching_points = [
                    p for p in all_points
                    if search_name in p.get("payload", {}).get("document_id", "")
                ]
            else:
                # Exact match
                matching_points = [
                    p for p in all_points
                    if p.get("payload", {}).get("document_id", "") == document_name
                ]

            logger.info(f"Found {len(matching_points)} chunks for document: {document_name}")

            # Show matching document IDs for confirmation
            unique_doc_ids = set(p.get("payload", {}).get("document_id", "") for p in matching_points)
            if unique_doc_ids:
                logger.info(f"Matching document IDs: {', '.join(sorted(unique_doc_ids))}")

            return matching_points
        else:
            logger.error(f"Failed to get points: HTTP {response.status_code} - {response.text}")
            return []

    except Exception as e:
        logger.error(f"Error getting points for {document_name}: {str(e)}")
        return []


def update_point_url(point_id: str, new_url: str, dry_run: bool = False) -> bool:
    """
    Update the document_url for a specific point.

    Args:
        point_id: Qdrant point ID
        new_url: New URL to set
        dry_run: If True, only simulate the update

    Returns:
        True if successful, False otherwise
    """
    if dry_run:
        logger.info(f"[DRY RUN] Would update point {point_id} with URL: {new_url}")
        return True

    try:
        response = requests.post(
            f"{QDRANT_URL}/collections/{COLLECTION_NAME}/points/payload",
            json={
                "points": [point_id],
                "payload": {
                    "document_url": new_url,
                    "metadata": {
                        "document_url": new_url  # Update both locations
                    }
                }
            },
            timeout=30
        )

        if response.status_code == 200:
            return True
        else:
            logger.error(f"Failed to update point {point_id}: HTTP {response.status_code} - {response.text}")
            return False

    except Exception as e:
        logger.error(f"Error updating point {point_id}: {str(e)}")
        return False


def update_document_url(document_name: str, new_url: str, dry_run: bool = False) -> Tuple[int, int]:
    """
    Update URL for all chunks of a document.

    Args:
        document_name: Name of the document
        new_url: New URL to set
        dry_run: If True, only simulate the update

    Returns:
        Tuple of (success_count, failure_count)
    """
    logger.info(f"\n{'='*80}")
    logger.info(f"Processing: {document_name}")
    logger.info(f"New URL: {new_url}")
    logger.info(f"{'='*80}")

    # Validate URL
    is_valid, error_msg = validate_url(new_url)
    if not is_valid:
        logger.error(f"❌ Invalid URL: {error_msg}")
        return 0, 0

    logger.info(f"✅ URL validation passed")

    # Get all points for this document
    points = get_points_for_document(document_name)

    if not points:
        logger.warning(f"⚠️  No chunks found for document: {document_name}")
        return 0, 0

    # Update each point
    success_count = 0
    failure_count = 0

    for point in points:
        point_id = point.get("id")
        if update_point_url(point_id, new_url, dry_run):
            success_count += 1
        else:
            failure_count += 1

    logger.info(f"✅ Updated {success_count}/{len(points)} chunks successfully")
    if failure_count > 0:
        logger.warning(f"⚠️  Failed to update {failure_count} chunks")

    return success_count, failure_count


def load_url_mapping(filepath: str) -> Dict[str, str]:
    """
    Load URL mapping from JSON file.

    Expected format:
    {
        "BMS-PROJ-FOR-028 Project Traceability Matrix.xlsx": "https://nomadrail.sharepoint.com/...",
        "BMS-ENGI-FOR-007 PE Solution Design Template.docx": "https://nomadrail.sharepoint.com/..."
    }

    Args:
        filepath: Path to JSON file

    Returns:
        Dictionary mapping document names to URLs
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            mapping = json.load(f)

        logger.info(f"Loaded {len(mapping)} document URL mappings from {filepath}")
        return mapping

    except FileNotFoundError:
        logger.error(f"File not found: {filepath}")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {filepath}: {str(e)}")
        return {}
    except Exception as e:
        logger.error(f"Error loading mapping file: {str(e)}")
        return {}


def load_missing_urls_list(filepath: str) -> List[str]:
    """
    Load list of documents with missing URLs.

    Args:
        filepath: Path to text file with document names (one per line)

    Returns:
        List of document names
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Clean up lines (remove line numbers, arrows, etc.)
        documents = []
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Remove line numbers like "     1→"
            if '→' in line:
                line = line.split('→', 1)[1].strip()

            # Skip empty lines after cleanup
            if line:
                documents.append(line)

        logger.info(f"Loaded {len(documents)} documents from {filepath}")
        return documents

    except FileNotFoundError:
        logger.error(f"File not found: {filepath}")
        return []
    except Exception as e:
        logger.error(f"Error loading missing URLs list: {str(e)}")
        return []


def interactive_mode(source_file: str, dry_run: bool = False):
    """
    Interactive mode - prompts user for URL for each document.

    Args:
        source_file: Path to file with list of documents
        dry_run: If True, only simulate updates
    """
    documents = load_missing_urls_list(source_file)

    if not documents:
        logger.error("No documents to process")
        return

    logger.info(f"\n{'='*80}")
    logger.info(f"INTERACTIVE MODE - {len(documents)} documents to process")
    logger.info(f"{'='*80}\n")

    total_success = 0
    total_failure = 0
    skipped = 0

    for i, document_name in enumerate(documents, 1):
        print(f"\n[{i}/{len(documents)}] Document: {document_name}")

        # Check current URL status
        points = get_points_for_document(document_name)
        if points:
            current_url = points[0].get("payload", {}).get("document_url", "null")
            print(f"Current URL: {current_url}")

        # Prompt for new URL
        new_url = input("Enter new SharePoint URL (or 'skip' to skip, 'quit' to exit): ").strip()

        if new_url.lower() == 'quit':
            logger.info("User requested quit")
            break

        if new_url.lower() == 'skip' or new_url == '':
            logger.info(f"Skipped: {document_name}")
            skipped += 1
            continue

        # Update document
        success, failure = update_document_url(document_name, new_url, dry_run)
        total_success += success
        total_failure += failure

    # Final summary
    logger.info(f"\n{'='*80}")
    logger.info(f"FINAL SUMMARY")
    logger.info(f"{'='*80}")
    logger.info(f"Total chunks updated: {total_success}")
    logger.info(f"Total failures: {total_failure}")
    logger.info(f"Documents skipped: {skipped}")
    logger.info(f"{'='*80}\n")


def batch_mode(mapping: Dict[str, str], dry_run: bool = False):
    """
    Batch mode - update multiple documents from mapping.

    Args:
        mapping: Dictionary mapping document names to URLs
        dry_run: If True, only simulate updates
    """
    logger.info(f"\n{'='*80}")
    logger.info(f"BATCH MODE - {len(mapping)} documents to update")
    logger.info(f"{'='*80}\n")

    total_success = 0
    total_failure = 0
    documents_updated = 0

    for document_name, new_url in mapping.items():
        success, failure = update_document_url(document_name, new_url, dry_run)

        if success > 0:
            documents_updated += 1

        total_success += success
        total_failure += failure

    # Final summary
    logger.info(f"\n{'='*80}")
    logger.info(f"FINAL SUMMARY")
    logger.info(f"{'='*80}")
    logger.info(f"Documents processed: {len(mapping)}")
    logger.info(f"Documents updated: {documents_updated}")
    logger.info(f"Total chunks updated: {total_success}")
    logger.info(f"Total failures: {total_failure}")
    logger.info(f"{'='*80}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Update document URLs in Qdrant database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Update single document
  python update_document_urls.py \\
    --document "BMS-PROJ-FOR-028 Project Traceability Matrix.xlsx" \\
    --url "https://nomadrail.sharepoint.com/qms/..."

  # Batch update from JSON file
  python update_document_urls.py --mapping url_mapping.json

  # Interactive mode
  python update_document_urls.py --interactive --source documents_missing_urls.txt

  # Dry run (preview changes)
  python update_document_urls.py --mapping url_mapping.json --dry-run
        """
    )

    parser.add_argument(
        "--document",
        help="Single document name to update"
    )
    parser.add_argument(
        "--url",
        help="New URL for single document"
    )
    parser.add_argument(
        "--mapping",
        help="Path to JSON file with document name -> URL mapping"
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Interactive mode - prompts for each document"
    )
    parser.add_argument(
        "--source",
        default="/workspace/002-n8n/documents_missing_urls.txt",
        help="Source file for interactive mode (default: documents_missing_urls.txt)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without applying them"
    )

    args = parser.parse_args()

    # Dry run warning
    if args.dry_run:
        logger.warning("🔍 DRY RUN MODE - No changes will be made to the database")

    # Single document update
    if args.document and args.url:
        update_document_url(args.document, args.url, args.dry_run)
        return

    # Batch update from mapping file
    if args.mapping:
        mapping = load_url_mapping(args.mapping)
        if mapping:
            batch_mode(mapping, args.dry_run)
        return

    # Interactive mode
    if args.interactive:
        interactive_mode(args.source, args.dry_run)
        return

    # No valid mode specified
    parser.print_help()
    logger.error("\nError: Must specify either --document + --url, --mapping, or --interactive")
    sys.exit(1)


if __name__ == "__main__":
    main()
