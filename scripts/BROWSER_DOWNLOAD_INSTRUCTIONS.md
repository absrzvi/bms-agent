# Browser Download Instructions for Office Files

## Overview
This script will download **282 Office documents** (DOCX, XLSX, PPTX) from SharePoint directly in your browser.

## Prerequisites
- You must be logged into SharePoint in your browser
- Browser must allow multiple file downloads

## Step-by-Step Instructions

### 1. Open SharePoint
Navigate to: https://nomadrail.sharepoint.com

### 2. Open Developer Console
- **Windows/Linux**: Press `F12` or `Ctrl + Shift + J`
- **Mac**: Press `Cmd + Option + J`

### 3. Copy the Script
Open the file: `/workspace/001-bms-agent/scripts/download_office_files_browser.js`

Select all content (Ctrl+A / Cmd+A) and copy (Ctrl+C / Cmd+C)

### 4. Paste and Run
- Click in the Console tab of Developer Tools
- Paste the script (Ctrl+V / Cmd+V)
- Press `Enter`

### 5. Allow Downloads
Your browser will likely ask permission to download multiple files. Click "Allow".

### 6. Wait for Completion
The script will:
- Download 282 Office files one by one
- Show progress in the console: `[1/282] filename.xlsx`
- Display ✅ for successful downloads
- Display ❌ for failed downloads
- Take approximately 4-5 minutes to complete

### 7. Check Downloads
Files will be in your browser's Downloads folder (usually `~/Downloads`)

## What the Script Does

1. **Converts URLs**: Transforms Office Online URLs to direct download URLs
2. **Downloads files**: Uses browser's fetch API with your existing session
3. **Handles errors**: Skips files that fail and continues
4. **Shows progress**: Real-time console output

## Expected Results

- **Success rate**: ~80-90% (some files may be restricted or moved)
- **File types**: DOCX, XLSX, PPTX, DOC, XLS, PPT, XLSM, POTX
- **Total size**: Approximately 50-100 MB

## Troubleshooting

### Browser blocks downloads
- Click "Allow" when prompted
- Or go to browser settings and allow multiple downloads from sharepoint.com

### Authentication errors
- Refresh the SharePoint page
- Make sure you're logged in
- Try running the script again

### Script doesn't run
- Make sure you copied the ENTIRE script
- Check for any error messages in red in the console
- Try closing and reopening Developer Tools

## After Download

Once downloads complete:

1. Move all downloaded Office files to: `/workspace/bms_data/incoming/`
2. Run the batch processor:
   ```bash
   /workspace/bms-api-venv/bin/python3 scripts/batch_process_incoming.py
   ```
3. Verify ingestion into Qdrant

## Files Included

The script will attempt to download:
- **DOCX files**: ~150 documents
- **XLSX files**: ~100 spreadsheets  
- **PPTX files**: ~30 presentations
- **Total**: 282 Office documents

## Support

If you encounter issues:
1. Check the console for error messages
2. Note which files failed (script will list them)
3. You can manually download failed files from SharePoint
