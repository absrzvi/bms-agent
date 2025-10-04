#!/usr/bin/env python3
"""
Direct Form Augmentation - Bypass processor cache issue
Directly augments sparse forms and re-embeds them into Qdrant
"""

import sys
from pathlib import Path
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
import uuid
from datetime import datetime
import json

# Document reading libraries
from docx import Document as DocxDocument
import fitz  # PyMuPDF
import openpyxl
from pptx import Presentation

def read_document(file_path: Path) -> str:
    """Read document content based on file type"""
    ext = file_path.suffix.lower()
    
    try:
        if ext == '.docx':
            doc = DocxDocument(file_path)
            return '\n'.join([para.text for para in doc.paragraphs])
        
        elif ext == '.pdf':
            doc = fitz.open(file_path)
            text = []
            for page in doc:
                text.append(page.get_text())
            doc.close()
            return '\n'.join(text)
        
        elif ext == '.xlsx':
            wb = openpyxl.load_workbook(file_path, data_only=True)
            content = []
            for sheet in wb.worksheets:
                for row in sheet.iter_rows(values_only=True):
                    row_text = ' '.join([str(cell) for cell in row if cell is not None])
                    if row_text.strip():
                        content.append(row_text)
            return '\n'.join(content)
        
        elif ext == '.pptx':
            prs = Presentation(file_path)
            content = []
            for slide in prs.slides:
                for shape in slide.shapes:
                    if hasattr(shape, "text"):
                        content.append(shape.text)
            return '\n'.join(content)
        
        return ""
    
    except Exception as e:
        print(f"  Error reading {file_path.name}: {e}")
        return ""

def augment_form_content(filename: str, content: str) -> str:
    """
    Augment sparse form with semantic-rich description
    """
    if len(content) > 1000:  # Only augment sparse forms
        return content
    
    parts = filename.split('-')
    
    department = ""
    doc_type = ""
    doc_name = filename
    
    if len(parts) >= 3 and parts[0].upper() == 'BMS':
        department = parts[1].upper()
        doc_type = parts[2].upper()
        doc_name = ' '.join(parts[3:]).replace('.docx', '').replace('.xlsx', '').replace('.pptx', '').replace('.pdf', '')
    
    dept_names = {
        'HUMR': 'Human Resources',
        'ISEC': 'Information Security',
        'QHSE': 'Quality, Health, Safety and Environment',
        'PROJ': 'Project Management',
        'ENGI': 'Engineering',
        'BDEV': 'Business Development',
        'FINA': 'Finance',
        'PROC': 'Procurement',
        'SERV': 'Service Management',
        'PROD': 'Product Development',
        'RENG': 'Railway Engineering',
        'SYSA': 'System Administration',
        'TDEV': 'Training and Development'
    }
    
    dept_full = dept_names.get(department, department)
    
    augmentation_parts = []
    
    if doc_type == 'FOR':
        augmentation_parts.append(f"This is a form template used in {dept_full} department.")
    
    purpose_keywords = {
        'approval': 'to obtain approval and authorization',
        'checklist': 'to ensure all required items are completed',
        'declaration': 'to formally declare or certify information',
        'report': 'to report and document information',
        'request': 'to submit a formal request',
        'sign-off': 'to obtain sign-off and approval',
        'register': 'to register and track items',
        'questionnaire': 'to collect information through questions',
        'assessment': 'to assess and evaluate',
        'plan': 'to plan and document activities',
        'traceability': 'to track and trace items',
        'audit': 'to conduct and document audits',
        'expense': 'to submit and track expenses',
        'competency': 'to assess competency and skills',
        'handover': 'to document handover procedures',
        'exit': 'for employee exit procedures',
        'maternity': 'for maternity-related documentation',
        'visitor': 'for visitor management and information',
        'poc': 'for proof of concept requests',
        'learner': 'for training and learning agreements',
        'analysis': 'to analyze and document findings'
    }
    
    doc_name_lower = doc_name.lower()
    for keyword, purpose in purpose_keywords.items():
        if keyword in doc_name_lower:
            augmentation_parts.append(f"Use this form {purpose}.")
            break
    
    if 'employee' in doc_name_lower or 'driver' in doc_name_lower:
        augmentation_parts.append("Required for employee-related processes.")
    elif 'incident' in doc_name_lower:
        augmentation_parts.append("Required when reporting incidents.")
    elif 'project' in doc_name_lower:
        augmentation_parts.append("Required for project documentation.")
    elif 'supplier' in doc_name_lower or 'vendor' in doc_name_lower:
        augmentation_parts.append("Required for supplier and vendor management.")
    elif 'bid' in doc_name_lower or 'tender' in doc_name_lower:
        augmentation_parts.append("Required for bidding and tendering processes.")
    elif 'audit' in doc_name_lower:
        augmentation_parts.append("Required for audit documentation and compliance.")
    elif 'expense' in doc_name_lower or 'payment' in doc_name_lower:
        augmentation_parts.append("Required for financial documentation.")
    elif 'training' in doc_name_lower or 'competency' in doc_name_lower:
        augmentation_parts.append("Required for training and development activities.")
    
    if augmentation_parts:
        augmentation = "FORM DESCRIPTION: " + " ".join(augmentation_parts) + "\n\n"
        return augmentation + content
    
    return content

def main():
    print("=" * 80)
    print("DIRECT FORM AUGMENTATION - BYPASSING PROCESSOR")
    print("=" * 80)
    
    # Initialize
    print("\n1. Initializing...")
    qdrant_client = QdrantClient(host="localhost", port=6333)
    model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
    collection_name = "nomad_bms_documents"
    
    # Sparse forms to augment
    sparse_forms = [
        ("docx", "BMS-ISEC-FOR-008 Internal System Audit Report.docx"),
        ("xlsx", "BMS-FINA-FOR-006 Company Credit Card Expense Form.xlsx"),
        ("pdf", "BMS-TDEV-FOR-004 FSE Competency Assessment Programme.pdf"),
        ("docx", "BMS-PROD-FOR-002 Internal FAI Inspection Report.docx"),
        ("docx", "BMS-HUMR-FOR-009 Maternity Risk Assessment.docx"),
        ("pptx", "BMS-BDEV-FOR-026 Tax Compliance Template.pptx"),
        ("docx", "BMS-QHSE-FOR-009 Risk Assessment Template.docx"),
        ("pptx", "BMS-BDEV-FOR-014 Win-Loss Analysis Template.pptx"),
        ("pdf", "BMS-QHSE-VIS-003 Belgium Visitor Information.pdf"),
        ("docx", "BMS-HUMR-FOR-038 Handover Schedule Template.docx"),
        ("pdf", "BMS-HUMR-FOR-015 Last Day Checklist.pdf"),
        ("pdf", "BMS-HUMR-FOR-035 Exit Interview Template.pdf"),
        ("xlsx", "BMS-PROJ-FOR-028 Project Traceability Matrix.xlsx"),
        ("docx", "BMS-QHSE-FOR-035 Site Contractor Audit.docx"),
        ("docx", "BMS-QHSE-FOR-057 Management of Change - Office Move Checklist.docx"),
        ("docx", "BMS-SYSA-FOR-004 POC Request Form.docx"),
        ("pdf", "BMS-TDEV-FOR-001 Learner Agreement Template.pdf")
    ]
    
    processed_dir = Path('/workspace/bms_data/processed')
    
    print(f"\n2. Processing {len(sparse_forms)} forms...")
    success_count = 0
    total_chunks = 0
    
    for ext_dir, filename in sparse_forms:
        file_path = processed_dir / ext_dir / filename
        
        if not file_path.exists():
            print(f"  ⚠️  {filename}: Not found")
            continue
        
        try:
            # Read original content
            content = read_document(file_path)
            
            if len(content) < 50:
                print(f"  ⚠️  {filename}: Too little content ({len(content)} chars)")
                continue
            
            # Augment content
            augmented_content = augment_form_content(filename, content)
            
            # Check if augmentation was applied
            was_augmented = len(augmented_content) > len(content)
            
            # Create simple chunks (since these are small forms)
            chunks = []
            if len(augmented_content) < 2000:
                chunks = [augmented_content]
            else:
                # Split into 2000-char chunks
                for i in range(0, len(augmented_content), 2000):
                    chunks.append(augmented_content[i:i+2000])
            
            # Embed and store each chunk
            for idx, chunk_content in enumerate(chunks):
                # Generate embedding
                embedding = model.encode(chunk_content).tolist()
                
                # Create point
                point_id = str(uuid.uuid4())
                point = PointStruct(
                    id=point_id,
                    vector={
                        "chunk_embedding": embedding,
                        "parent_embedding": embedding,
                        "child_embedding": embedding,
                        "full_doc_embedding": embedding
                    },
                    payload={
                        "document_id": str(uuid.uuid4()),
                        "document_name": filename,
                        "document_type": file_path.suffix[1:],
                        "chunk_id": f"{filename}_chunk_{idx}",
                        "chunk_index": idx,
                        "content": chunk_content,
                        "is_form": True,
                        "is_template": "template" in filename.lower(),
                        "document_type_category": "form_template",
                        "processing_version": "v4.2_direct_augmented",
                        "processing_timestamp": datetime.now().isoformat(),
                        "augmented": was_augmented
                    }
                )
                
                # Upsert to Qdrant
                qdrant_client.upsert(
                    collection_name=collection_name,
                    points=[point]
                )
            
            aug_marker = "📝" if was_augmented else "  "
            print(f"  {aug_marker} ✅ {filename}: {len(chunks)} chunks (+{len(augmented_content)-len(content)} chars)")
            success_count += 1
            total_chunks += len(chunks)
            
        except Exception as e:
            print(f"  ❌ {filename}: {str(e)[:60]}")
    
    print(f"\n3. Summary:")
    print(f"   Successfully processed: {success_count}/{len(sparse_forms)}")
    print(f"   Total chunks created: {total_chunks}")
    print(f"   Augmentation applied: {success_count} forms")
    
    print("\n" + "=" * 80)
    print("AUGMENTATION COMPLETE!")
    print("=" * 80)
    print("\nNext: Re-run evaluation to see improvement")
    print("   /workspace/bms-api-venv/bin/python3 scripts/evaluate_retrieval_enhanced.py")

if __name__ == "__main__":
    main()
