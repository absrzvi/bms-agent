"""
BMS Document Generator Pipeline
Generates Word, Excel, and PowerPoint documents from BMS Agent data

Based on research in docs/openwebui-doc-gen.md
Uses Pipelines approach (recommended) to avoid dependency conflicts

title: BMS Document Generator
author: BMS Agent Team
version: 1.0.0
license: MIT
requirements: python-docx>=0.8.11,openpyxl>=3.1.0,python-pptx>=0.6.21
"""

from typing import List, Dict, Any, Optional, Callable, Awaitable
from pydantic import BaseModel, Field
import os
import json
from datetime import datetime

# Import will happen after pip install via Pipelines
try:
    from docx import Document
    from docx.shared import Pt, RGBColor, Inches
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment
    XLSX_AVAILABLE = True
except ImportError:
    XLSX_AVAILABLE = False

try:
    from pptx import Presentation
    from pptx.util import Inches as PptxInches, Pt as PptxPt
    PPTX_AVAILABLE = True
except ImportError:
    PPTX_AVAILABLE = False


class Pipeline:
    """
    BMS Document Generator Pipeline
    Function calling blueprint for document generation
    """

    class Valves(BaseModel):
        """Admin-configurable settings"""
        OUTPUT_DIR: str = Field(
            default="/workspace/001-bms-agent/pipelines/output",
            description="Directory for generated documents"
        )
        MAX_FILE_SIZE_MB: int = Field(
            default=10,
            description="Maximum file size in MB"
        )
        ENABLE_DOCX: bool = Field(
            default=True,
            description="Enable Word document generation"
        )
        ENABLE_XLSX: bool = Field(
            default=True,
            description="Enable Excel spreadsheet generation"
        )
        ENABLE_PPTX: bool = Field(
            default=True,
            description="Enable PowerPoint presentation generation"
        )

    class UserValves(BaseModel):
        """User-configurable settings"""
        include_timestamp: bool = Field(
            default=True,
            description="Include timestamp in filenames"
        )
        default_author: str = Field(
            default="BMS Agent",
            description="Default document author"
        )

    def __init__(self):
        self.type = "pipe"
        self.id = "bms_document_generator"
        self.name = "BMS Document Generator"
        self.valves = self.Valves()
        
        # Ensure output directory exists
        os.makedirs(self.valves.OUTPUT_DIR, exist_ok=True)

    async def on_startup(self):
        """Initialize pipeline on startup"""
        print("=" * 60)
        print("BMS Document Generator Pipeline starting...")
        print(f"Output directory: {self.valves.OUTPUT_DIR}")

        # Validate dependencies
        issues = []
        if not DOCX_AVAILABLE:
            issues.append("python-docx not available")
        if not XLSX_AVAILABLE:
            issues.append("openpyxl not available")
        if not PPTX_AVAILABLE:
            issues.append("python-pptx not available")

        if issues:
            print(f"❌ Dependency issues: {', '.join(issues)}")
        else:
            print(f"✅ DOCX available: {DOCX_AVAILABLE}")
            print(f"✅ XLSX available: {XLSX_AVAILABLE}")
            print(f"✅ PPTX available: {PPTX_AVAILABLE}")

        # Validate output directory
        try:
            os.makedirs(self.valves.OUTPUT_DIR, exist_ok=True)
            print(f"✅ Output directory ready: {self.valves.OUTPUT_DIR}")
        except Exception as e:
            print(f"❌ Cannot create output directory: {e}")

        print("=" * 60)

    async def on_shutdown(self):
        """Cleanup on shutdown"""
        print("BMS Document Generator Pipeline shutting down...")

    async def inlet(self, body: dict, user: Optional[dict] = None) -> dict:
        """Process incoming requests"""
        return body

    async def outlet(self, body: dict, user: Optional[dict] = None) -> dict:
        """Process outgoing responses"""
        return body

    def pipe(
        self,
        user_message: str,
        model_id: str,
        messages: List[dict],
        body: dict,
    ) -> str:
        """Main pipeline execution"""
        return f"BMS Document Generator ready. Available tools: create_word_doc, create_excel_sheet, create_presentation"

    def get_tools(self) -> List[Dict[str, Any]]:
        """
        Define available tools for function calling
        Returns JSON schema for LLM to understand available functions
        """
        tools = []

        if self.valves.ENABLE_DOCX and DOCX_AVAILABLE:
            tools.append({
                "type": "function",
                "function": {
                    "name": "create_word_document",
                    "description": "Create a Word document (DOCX) with structured content including title, sections, and paragraphs",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {
                                "type": "string",
                                "description": "Document title"
                            },
                            "sections": {
                                "type": "array",
                                "description": "List of sections with headings and content",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "heading": {"type": "string"},
                                        "content": {"type": "string"}
                                    },
                                    "required": ["heading", "content"]
                                }
                            },
                            "filename": {
                                "type": "string",
                                "description": "Output filename (without extension)"
                            }
                        },
                        "required": ["title", "sections", "filename"]
                    }
                }
            })

        if self.valves.ENABLE_XLSX and XLSX_AVAILABLE:
            tools.append({
                "type": "function",
                "function": {
                    "name": "create_excel_spreadsheet",
                    "description": "Create an Excel spreadsheet (XLSX) with data in table format",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {
                                "type": "string",
                                "description": "Spreadsheet title"
                            },
                            "headers": {
                                "type": "array",
                                "description": "Column headers",
                                "items": {"type": "string"}
                            },
                            "data": {
                                "type": "array",
                                "description": "Table data rows",
                                "items": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                }
                            },
                            "filename": {
                                "type": "string",
                                "description": "Output filename (without extension)"
                            }
                        },
                        "required": ["headers", "data", "filename"]
                    }
                }
            })

        if self.valves.ENABLE_PPTX and PPTX_AVAILABLE:
            tools.append({
                "type": "function",
                "function": {
                    "name": "create_presentation",
                    "description": "Create a PowerPoint presentation (PPTX) with title and content slides",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {
                                "type": "string",
                                "description": "Presentation title"
                            },
                            "slides": {
                                "type": "array",
                                "description": "List of slides with titles and content",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "title": {"type": "string"},
                                        "content": {"type": "string"}
                                    },
                                    "required": ["title", "content"]
                                }
                            },
                            "filename": {
                                "type": "string",
                                "description": "Output filename (without extension)"
                            }
                        },
                        "required": ["title", "slides", "filename"]
                    }
                }
            })

        return tools

    async def call_tool(
        self,
        tool_name: str,
        tool_parameters: dict,
        user: Optional[dict] = None,
        event_emitter: Optional[Callable[[dict], Awaitable[None]]] = None
    ) -> str:
        """
        Execute tool based on function call from LLM
        """
        try:
            if event_emitter:
                await event_emitter({
                    "type": "status",
                    "data": {
                        "description": f"Creating {tool_name.replace('create_', '').replace('_', ' ')}...",
                        "done": False
                    }
                })

            if tool_name == "create_word_document":
                result = self._create_word_doc(tool_parameters, user)
            elif tool_name == "create_excel_spreadsheet":
                result = self._create_excel_sheet(tool_parameters, user)
            elif tool_name == "create_presentation":
                result = self._create_pptx(tool_parameters, user)
            else:
                result = f"Unknown tool: {tool_name}"

            if event_emitter:
                await event_emitter({
                    "type": "status",
                    "data": {
                        "description": "Document created successfully",
                        "done": True
                    }
                })

            return result

        except Exception as e:
            error_msg = f"Error creating document: {str(e)}"
            if event_emitter:
                await event_emitter({
                    "type": "status",
                    "data": {
                        "description": error_msg,
                        "done": True
                    }
                })
            return error_msg

    def _get_filename(self, base_filename: str, extension: str, user: Optional[dict] = None) -> str:
        """Generate filename with optional timestamp"""
        user_valves = user.get("valves", {}) if user else {}
        include_timestamp = user_valves.get("include_timestamp", True)
        
        if include_timestamp:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{base_filename}_{timestamp}.{extension}"
        else:
            filename = f"{base_filename}.{extension}"
        
        return os.path.join(self.valves.OUTPUT_DIR, filename)

    def _create_word_doc(self, params: dict, user: Optional[dict] = None) -> str:
        """Create Word document"""
        if not DOCX_AVAILABLE:
            return "Error: python-docx library not available"

        doc = Document()
        
        # Add title
        title = doc.add_heading(params["title"], 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Add metadata
        doc.add_paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        doc.add_paragraph(f"Author: BMS Agent")
        doc.add_paragraph("")  # Blank line
        
        # Add sections
        for section in params["sections"]:
            doc.add_heading(section["heading"], 1)
            doc.add_paragraph(section["content"])
            doc.add_paragraph("")  # Blank line between sections
        
        # Save
        filepath = self._get_filename(params["filename"], "docx", user)
        doc.save(filepath)
        
        return f"✅ Word document created: {os.path.basename(filepath)}\nLocation: {filepath}"

    def _create_excel_sheet(self, params: dict, user: Optional[dict] = None) -> str:
        """Create Excel spreadsheet"""
        if not XLSX_AVAILABLE:
            return "Error: openpyxl library not available"

        wb = Workbook()
        ws = wb.active
        ws.title = params.get("title", "Sheet1")[:31]  # Excel sheet name limit
        
        # Add title if provided
        if "title" in params:
            ws['A1'] = params["title"]
            ws['A1'].font = Font(size=14, bold=True)
            ws.append([])  # Blank row
        
        # Add headers with styling
        ws.append(params["headers"])
        header_row = ws[ws.max_row]
        for cell in header_row:
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill(start_color="0066CC", end_color="0066CC", fill_type="solid")
            cell.alignment = Alignment(horizontal="center")
        
        # Add data
        for row_data in params["data"]:
            ws.append(row_data)
        
        # Auto-adjust column widths
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                if cell.value:
                    max_length = max(max_length, len(str(cell.value)))
            ws.column_dimensions[column_letter].width = min(max_length + 2, 50)
        
        # Save
        filepath = self._get_filename(params["filename"], "xlsx", user)
        wb.save(filepath)
        
        return f"✅ Excel spreadsheet created: {os.path.basename(filepath)}\nLocation: {filepath}\nRows: {len(params['data']) + 1} (+ header)"

    def _create_pptx(self, params: dict, user: Optional[dict] = None) -> str:
        """Create PowerPoint presentation"""
        if not PPTX_AVAILABLE:
            return "Error: python-pptx library not available"

        prs = Presentation()
        
        # Title slide
        title_slide_layout = prs.slide_layouts[0]
        slide = prs.slides.add_slide(title_slide_layout)
        title = slide.shapes.title
        subtitle = slide.placeholders[1]
        
        title.text = params["title"]
        subtitle.text = f"Generated by BMS Agent\n{datetime.now().strftime('%Y-%m-%d')}"
        
        # Content slides
        for slide_data in params["slides"]:
            content_slide_layout = prs.slide_layouts[1]  # Title and Content
            slide = prs.slides.add_slide(content_slide_layout)
            
            title = slide.shapes.title
            content = slide.placeholders[1]
            
            title.text = slide_data["title"]
            content.text = slide_data["content"]
        
        # Save
        filepath = self._get_filename(params["filename"], "pptx", user)
        prs.save(filepath)
        
        return f"✅ PowerPoint presentation created: {os.path.basename(filepath)}\nLocation: {filepath}\nSlides: {len(params['slides']) + 1} (title + content)"
