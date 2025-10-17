# Final SharePoint Office Files Download Solution

## Summary
- **Total Office files**: 282
- **Direct library URLs**: 70 files (can be downloaded programmatically)
- **Office Online URLs**: 212 files (require manual download)

## Solution Created

### Script: `/workspace/001-bms-agent/scripts/sharepoint_rest_download_complete.js`

This script will download **70 Office files** that have direct library URLs using SharePoint's REST API.

## How to Use

### Step 1: Download 70 Files Automatically

1. **Open SharePoint**: https://nomadrail.sharepoint.com
2. **Open Console**: Press `F12`
3. **Copy script**: `/workspace/001-bms-agent/scripts/sharepoint_rest_download_complete.js`
4. **Paste in console** and press Enter
5. **Allow downloads** when prompted
6. **Wait**: ~1 minute for 70 files

### Step 2: Download Remaining 212 Files Manually

The remaining files use Office Online URLs and must be downloaded manually:

**Option A: Bulk Download (FASTEST)**
1. Go to https://nomadrail.sharepoint.com/qms/BMS%20System/06%20Forms
2. Select all Office files (Ctrl+A or Shift+Click)
3. Click "Download" button
4. SharePoint creates a ZIP file
5. Extract and use

**Option B: OneDrive Sync**
1. Go to SharePoint library
2. Click "Sync" button
3. Files sync to your computer automatically
4. Copy from synced folder

**Option C: Individual Downloads**
- Click each file → Click "Download" in toolbar
- Slow but works for specific files

## After Download

Once you have the Office files:

```bash
# Move to incoming directory
mv ~/Downloads/*.docx ~/Downloads/*.xlsx ~/Downloads/*.pptx /workspace/bms_data/incoming/

# Or if downloaded as ZIP
unzip ~/Downloads/sharepoint_files.zip -d /workspace/bms_data/incoming/

# Run batch processor
/workspace/bms-api-venv/bin/python3 scripts/batch_process_incoming.py
```

## Expected Results

After processing all Office files:
- **Total documents**: ~700 (430 PDFs + 270 Office files)
- **Total chunks**: ~2,500-3,000
- **Processing time**: ~30-40 minutes (GPU mode)

## Why Two Methods?

SharePoint has two types of URLs:

1. **Direct Library URLs** (70 files):
   ```
   https://nomadrail.sharepoint.com/qms/BMS System/06 Forms/filename.xlsx
   ```
   ✅ Can download via REST API

2. **Office Online URLs** (212 files):
   ```
   https://nomadrail.sharepoint.com/:x:/r/qms/_layouts/15/Doc.aspx?sourcedoc={GUID}&file=filename.xlsx
   ```
   ❌ No direct path - opens in viewer

## Current Status

✅ **Already Ingested**:
- 430 PDF documents
- 1,416 chunks  
- Zero duplicates

⏳ **Ready to Ingest**:
- 70 Office files (automated script)
- 212 Office files (manual download)

🔧 **System Ready**:
- Enhanced Document Processor: Fixed and working
- Batch processor: GPU-accelerated
- Qdrant: Properly configured

## Recommendation

1. **Run the automated script first** (70 files in 1 minute)
2. **Use SharePoint bulk download** for the rest (5-10 minutes)
3. **Process all files together** (30-40 minutes)

This gives you the complete 700-document corpus with minimal manual effort!
