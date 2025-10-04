# Manual Download Guide for Office Files

## Problem
SharePoint's security policies prevent automated downloads of Office files (DOCX, XLSX, PPTX). The files must be downloaded manually.

## Solution: Use SharePoint's Bulk Download Feature

### Method 1: Bulk Download via SharePoint (RECOMMENDED - Fastest)

1. **Go to SharePoint Document Library**
   - Open: https://nomadrail.sharepoint.com/qms
   - Navigate to: `BMS System` → `06 Forms`

2. **Select Files**
   - Click on the first file
   - Hold `Shift` and click on the last file to select all
   - Or use `Ctrl+Click` to select specific files

3. **Download**
   - Click the "Download" button in the top toolbar
   - SharePoint will create a ZIP file containing all selected files
   - Save the ZIP to your computer
   - Extract the ZIP file

4. **Move to Workspace**
   - Copy all extracted Office files to: `/workspace/bms_data/incoming/`

### Method 2: OneDrive Sync (Best for Large Downloads)

1. **Sync SharePoint Library**
   - Go to the SharePoint library
   - Click "Sync" button in the toolbar
   - This will sync the entire library to your local machine

2. **Copy Files**
   - Navigate to the synced folder on your computer
   - Copy all Office files
   - Transfer to: `/workspace/bms_data/incoming/`

### Method 3: Individual Downloads (Slowest)

If you need specific files only:

1. Open the file URL in SharePoint
2. Click "Download" button in the Office Online toolbar
3. Save to your Downloads folder
4. Move to `/workspace/bms_data/incoming/`

## Office Files to Download

**Total: 282 files**

### By Type:
- **DOCX**: ~150 Word documents
- **XLSX**: ~100 Excel spreadsheets
- **PPTX**: ~30 PowerPoint presentations

### Key Directories in SharePoint:
- `/qms/BMS System/06 Forms/` - Most forms and templates
- `/qms/BMS System/04 Guidance Documents/` - Guidance documents
- `/qms/BMS System/03 Manuals/` - Manuals
- `/qms/BMS System/01 Policies/` - Policy documents

## After Downloading

Once you have the Office files in `/workspace/bms_data/incoming/`:

```bash
# Run the batch processor
/workspace/bms-api-venv/bin/python3 scripts/batch_process_incoming.py

# This will:
# 1. Extract text from DOCX/XLSX/PPTX files
# 2. Generate embeddings
# 3. Store in Qdrant database
# 4. Move processed files to /workspace/bms_data/processed/
```

## Expected Results

After processing all Office files:
- **Total documents in Qdrant**: ~700 (430 PDFs + 270 Office files)
- **Total chunks**: ~2,500-3,000
- **Zero duplicates**: Guaranteed by single-worker processing

## Troubleshooting

### "Download" button is grayed out
- You may not have download permissions for that file
- Contact your SharePoint administrator

### ZIP download fails
- Try selecting fewer files at once (50-100 at a time)
- SharePoint has limits on ZIP file size

### Files won't sync
- Check your OneDrive storage space
- Ensure you have permissions to the SharePoint library

## Alternative: Ask IT/Admin

If you have IT support or SharePoint administrators, they can:
1. Use PowerShell scripts to bulk download
2. Provide direct access to the SharePoint backend
3. Export the entire document library

## Current Status

✅ **Already Ingested:**
- 430 PDF documents
- 1,416 chunks
- Zero duplicates
- Full metadata

⏳ **Pending:**
- 282 Office documents (manual download required)

The system is fully operational with the 430 PDFs. Office files can be added incrementally.
