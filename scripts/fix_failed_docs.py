#!/usr/bin/env python3
"""
Fix Failed Documents Script
Reprocess documents that failed in the initial batch with enhanced error handling
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "bms-agent" / "scr"))

from enhanced_document_processor import (
    EnhancedDocumentProcessor, 
    ProcessingConfig,
    ProcessingProfile
)

# Failed documents from the batch processing
FAILED_DOCS = [
    "pdf/Supplier Management.pdf",
    "pdf/Product Management High Level Map.pdf",
    "pdf/PM - Customer Feedback Questionnaire - French.pdf",
    "pdf/Patching Process.pdf",
    "pdf/Non-Disclosure Agreement Process.pdf",
    "pdf/NMID Free to Bid - Free to Order Process.pdf",
    "pdf/Expression of Wish Form Group Life Assurance (Restricted).pdf",
    "pdf/Asset Registration Process.pdf",
    "xls/Supplier Approval Checklist.xlsx",
    "xls/New Supplier Form for ERP Upload.xlsx",
    "xls/ENG - Cable Schedule Example.xlsx",
    "xls/Bid Risk Register.xlsx",
    "xls/Bid Action Log Check List.xlsx",
    "doc/BMS-HI-PROD-FOR-006 Assembly Instruction.docx",
    "doc/Blank - No Address Template.docx",
    "doc/Bid Sign Off Record.docx"
]

def fix_xlsx_file(file_path):
    """Try to read XLSX with different engines"""
    import pandas as pd
    
    engines = ['openpyxl', 'xlrd', None]
    for engine in engines:
        try:
            if engine:
                df = pd.read_excel(file_path, engine=engine)
            else:
                df = pd.read_excel(file_path)
            print(f"  ✅ Successfully read with engine: {engine or 'auto'}")
            return df
        except Exception as e:
            print(f"  ❌ Engine {engine or 'auto'} failed: {e}")
    return None

def fix_pdf_file(file_path):
    """Try to read PDF with enhanced error handling"""
    import fitz
    try:
        doc = fitz.open(file_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        print(f"  ✅ Successfully extracted {len(text)} chars")
        return text
    except Exception as e:
        print(f"  ❌ PyMuPDF failed: {e}")
        
        # Try pdfplumber as fallback
        try:
            import pdfplumber
            with pdfplumber.open(file_path) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() or ""
            print(f"  ✅ pdfplumber extracted {len(text)} chars")
            return text
        except Exception as e2:
            print(f"  ❌ pdfplumber also failed: {e2}")
    return None

def fix_docx_file(file_path):
    """Try to read DOCX with enhanced error handling"""
    from docx import Document
    import zipfile
    
    # First check if it's a valid ZIP
    try:
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            print(f"  ✅ Valid ZIP archive")
    except zipfile.BadZipFile:
        print(f"  ❌ Not a valid ZIP file - file may be corrupted")
        return None
    
    try:
        doc = Document(file_path)
        text = "\n".join([para.text for para in doc.paragraphs])
        print(f"  ✅ Successfully extracted {len(text)} chars")
        return text
    except Exception as e:
        print(f"  ❌ python-docx failed: {e}")
    return None

def main():
    """Fix failed documents"""
    
    base_dir = Path("/workspace/bms_data/uploads")
    
    print("🔧 Fixing Failed Documents")
    print("=" * 70)
    print()
    
    # Configuration
    config = ProcessingConfig(
        chunk_size=2000,
        chunk_overlap=400,
        quality_threshold=70.0,
        enable_quality_validation=True,
        enable_contextual_retrieval=True,
        enable_late_chunking=True,
        processing_profile=ProcessingProfile.TECHNICAL
    )
    
    processor = EnhancedDocumentProcessor(config)
    
    fixed = 0
    still_failed = 0
    
    for doc_path in FAILED_DOCS:
        full_path = base_dir / doc_path
        
        if not full_path.exists():
            print(f"❌ File not found: {doc_path}")
            still_failed += 1
            continue
        
        print(f"\n📄 Processing: {doc_path}")
        
        # Try format-specific fixes first
        if doc_path.endswith('.xlsx'):
            result = fix_xlsx_file(full_path)
            if result is not None:
                # Now try processing with the processor
                try:
                    proc_result = processor.process_document(str(full_path))
                    if proc_result.get('processing_success'):
                        print(f"  ✅ Successfully processed!")
                        fixed += 1
                    else:
                        print(f"  ❌ Processing failed: {proc_result.get('errors')}")
                        still_failed += 1
                except Exception as e:
                    print(f"  ❌ Processing error: {e}")
                    still_failed += 1
            else:
                still_failed += 1
                
        elif doc_path.endswith('.pdf'):
            result = fix_pdf_file(full_path)
            if result is not None:
                try:
                    proc_result = processor.process_document(str(full_path))
                    if proc_result.get('processing_success'):
                        print(f"  ✅ Successfully processed!")
                        fixed += 1
                    else:
                        print(f"  ❌ Processing failed: {proc_result.get('errors')}")
                        still_failed += 1
                except Exception as e:
                    print(f"  ❌ Processing error: {e}")
                    still_failed += 1
            else:
                still_failed += 1
                
        elif doc_path.endswith('.docx'):
            result = fix_docx_file(full_path)
            if result is not None:
                try:
                    proc_result = processor.process_document(str(full_path))
                    if proc_result.get('processing_success'):
                        print(f"  ✅ Successfully processed!")
                        fixed += 1
                    else:
                        print(f"  ❌ Processing failed: {proc_result.get('errors')}")
                        still_failed += 1
                except Exception as e:
                    print(f"  ❌ Processing error: {e}")
                    still_failed += 1
            else:
                still_failed += 1
    
    print()
    print("=" * 70)
    print("📊 Fix Summary:")
    print(f"   ✅ Fixed: {fixed}")
    print(f"   ❌ Still Failed: {still_failed}")
    print(f"   📝 Total Attempted: {len(FAILED_DOCS)}")
    print()
    
    if fixed > 0:
        print("🎉 Some documents were successfully fixed!")
    if still_failed > 0:
        print("⚠️  Some documents are likely corrupted and cannot be recovered")

if __name__ == "__main__":
    main()
