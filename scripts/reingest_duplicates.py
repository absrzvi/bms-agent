#!/usr/bin/env python3
"""
Re-ingest duplicate documents into Qdrant.
- Reads reports/duplicate_documents.json
- Deletes any existing points for each document_name
- Reprocesses document from processed/incoming directories using EnhancedDocumentProcessor
"""

import json
import sys
import time
from pathlib import Path
from typing import Optional

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "bms-agent" / "scr"))

from enhanced_document_processor import EnhancedDocumentProcessor, ProcessingConfig, ProcessingProfile
from qdrant_client import QdrantClient
from qdrant_client.http import models

API_HOST = "localhost"
API_PORT = 6333
COLLECTION = "nomad_bms_documents"

LOG_PATH = Path('/workspace/logs/reingest_duplicates.log')
DUP_REPORT = Path('reports/duplicate_documents.json')
SEARCH_DIRS = [
    Path('/workspace/bms_data/processed'),
    Path('/workspace/bms_data/incoming'),
    Path('/workspace/bms_data/uploads')
]

config = ProcessingConfig(
    chunk_size=2000,
    chunk_overlap=400,
    quality_threshold=0.70,
    enable_quality_validation=True,
    enable_contextual_retrieval=True,
    enable_late_chunking=True,
    processing_profile=ProcessingProfile.RAILWAY,
    use_gpu=True,
)
processor = EnhancedDocumentProcessor(config)
client = QdrantClient(host=API_HOST, port=API_PORT)


def find_source(name: str) -> Optional[Path]:
    for base in SEARCH_DIRS:
        if not base.exists():
            continue
        # exact match first
        for candidate in base.rglob(name):
            if candidate.is_file():
                return candidate
    return None


def delete_existing(doc_id: str):
    flt = models.Filter(
        must=[models.FieldCondition(key="document_id", match=models.MatchValue(value=doc_id))]
    )
    client.delete(
        collection_name=COLLECTION,
        points_selector=models.FilterSelector(filter=flt)
    )


def ingest(path: Path):
    result = processor.process_document(str(path))
    if not result.get('processing_success', False):
        raise RuntimeError(f"Processing failed for {path}: {result.get('errors')}")
    return result


def main():
    if not DUP_REPORT.exists():
        print(f"Missing {DUP_REPORT}")
        sys.exit(1)

    data = json.loads(DUP_REPORT.read_text())
    duplicates = data.get('duplicates', {})
    records = []
    for name, entries in duplicates.items():
        if not entries:
            continue
        doc_id = entries[-1].get('document_id') or name
        records.append((name, doc_id))

    total = len(records)
    processed = 0
    missing = []

    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open('w') as log_file:
        log_file.write(f"Re-ingest started for {total} documents\n")

    for name, doc_id in sorted(records):
        source = find_source(name)
        if not source:
            print(f"\n⚠️  Source missing: {name}")
            missing.append(name)
            with LOG_PATH.open('a') as log_file:
                log_file.write(f"MISSING: {name}\n")
            continue
        print(f"\n=== {name}")
        delete_existing(doc_id)
        try:
            ingest(source)
            processed += 1
            print(f"✅ Re-ingested {name}")
            with LOG_PATH.open('a') as log_file:
                log_file.write(f"SUCCESS: {name}\n")
            time.sleep(0.1)
        except Exception as exc:
            print(f"❌ Failed to ingest {name}: {exc}")
            with LOG_PATH.open('a') as log_file:
                log_file.write(f"FAILED: {name} :: {exc}\n")

    print("\nSummary:")
    print(f"  Total duplicates: {total}")
    print(f"  Re-ingested: {processed}")
    print(f"  Missing sources: {len(missing)}")
    if missing:
        Path('reports/missing_duplicate_sources.txt').write_text('\n'.join(missing))
        print("  Missing list saved to reports/missing_duplicate_sources.txt")
    print(f"  Log: {LOG_PATH}")


if __name__ == '__main__':
    main()
