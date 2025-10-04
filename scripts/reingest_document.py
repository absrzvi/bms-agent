#!/usr/bin/env python3
import sys, subprocess
from pathlib import Path

if len(sys.argv) != 2:
    print("Usage: reingest_document.py <document_name>")
    sys.exit(1)

document_name = sys.argv[1]

control = Path("scripts") / "batch_process_incoming.py"
if not control.exists():
    print("Missing scripts/batch_process_incoming.py")
    sys.exit(1)

incoming_dir = Path("/workspace/bms_data/incoming")
source = next((p for p in incoming_dir.glob("**/*") if p.name == document_name), None)
if not source:
    print(f"Document {document_name} not found in incoming dir")
    sys.exit(1)

subprocess.check_call(["python3", "scripts/batch_process_incoming.py", "--single", str(source)])
