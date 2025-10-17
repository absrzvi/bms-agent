# SharePoint Document Download Instructions

## Overview

This guide explains how to download all BMS documents from SharePoint that were modified after December 31, 2023.

**Total Documents**: 1,004 documents from the BMS Quality Management System

---

## 📋 Prerequisites

1. **SharePoint Access**: You must have access to `nomadrail.sharepoint.com`
2. **Browser**: Chrome, Firefox, or Edge (with Developer Tools)
3. **Authentication**: Be logged into SharePoint before running the script

---

## 🚀 Step-by-Step Instructions

### Step 1: Open the Download Script

The complete browser console script has been generated at:
```
/workspace/001-bms-agent/scripts/download_sharepoint_docs_complete.js
```

### Step 2: Log into SharePoint

1. Open your browser
2. Navigate to: `https://nomadrail.sharepoint.com`
3. Log in with your credentials
4. **Important**: Stay on the SharePoint site (any page is fine)

### Step 3: Open Developer Tools

**Windows/Linux**: Press `F12` or `Ctrl + Shift + I`  
**Mac**: Press `Cmd + Option + I`

Or right-click anywhere on the page and select "Inspect" or "Inspect Element"

### Step 4: Go to Console Tab

In the Developer Tools panel, click on the **Console** tab

### Step 5: Copy and Paste the Script

1. Open the file: `scripts/download_sharepoint_docs_complete.js`
2. Select all content (`Ctrl+A` or `Cmd+A`)
3. Copy (`Ctrl+C` or `Cmd+C`)
4. Click in the Console tab
5. Paste (`Ctrl+V` or `Cmd+V`)
6. Press `Enter` to run

### Step 6: Monitor Progress

The script will:
- ✅ Check each document's modification date
- ⏭️  Skip files modified before 2024-01-01
- ⬇️  Download files modified after 2023-12-31
- 📊 Show real-time progress

**Expected Output**:
```
🚀 SharePoint Document Downloader Started
📅 Filtering for files modified after: 2023-12-31T23:59:59.000Z
📋 Total documents to check: 1004

📦 Batch 1/335
─────────────────────────────────────────────────────────────────
📄 Bid Action Log Check List
   File: BMS-BDEV-FOR-005 Bid Action Log Check List.xlsx
   Last Modified: 2024-03-15T10:30:00.000Z
   ⬇️  Downloading...
   📦 Size: 45.23 KB
   ✅ DOWNLOADED
...
```

### Step 7: Wait for Completion

- The script processes **3 files at a time** to avoid rate limiting
- There's a **2-second delay** between downloads
- **Estimated time**: ~30-60 minutes for all files (depending on how many are recent)

### Step 8: Check Your Downloads

Downloaded files will appear in your browser's default Downloads folder.

---

## ⚙️ Script Configuration

You can modify these settings at the top of the script:

```javascript
const CUTOFF_DATE = new Date('2023-12-31T23:59:59Z');  // Only files after this date
const DELAY_MS = 2000;                                  // Delay between downloads (ms)
const BATCH_SIZE = 3;                                   // Files per batch
const MAX_RETRIES = 2;                                  // Retry failed downloads
```

---

## 📊 What the Script Does

### 1. Date Filtering
- Checks the `Last-Modified` header for each file
- Only downloads files modified after December 31, 2023
- Skips older files automatically

### 2. Batch Processing
- Processes files in small batches to avoid overwhelming SharePoint
- Includes delays between downloads
- Prevents rate limiting

### 3. Error Handling
- Automatically retries failed downloads (up to 2 times)
- Reports errors at the end
- Continues processing even if some files fail

### 4. Progress Tracking
- Shows real-time progress for each file
- Displays batch progress
- Provides final summary with statistics

---

## 📈 Expected Results

### Final Summary Example:
```
═══════════════════════════════════════════════════════════════════
🎉 DOWNLOAD COMPLETE
═══════════════════════════════════════════════════════════════════
📊 Total Processed: 1004
✅ Downloaded: 342
⏭️  Skipped (old files): 650
❌ Errors: 12
💾 Total Size: 156.78 MB
═══════════════════════════════════════════════════════════════════
```

---

## 🔧 Troubleshooting

### Issue: "Cannot extract filename"
**Solution**: The URL format may be different. Check the URL structure in the console output.

### Issue: "HTTP 401: Unauthorized"
**Solution**: You're not logged into SharePoint. Log in and try again.

### Issue: "HTTP 403: Forbidden"
**Solution**: You don't have permission to access that file. Skip it or request access.

### Issue: "HTTP 429: Too Many Requests"
**Solution**: Increase the `DELAY_MS` value in the script (e.g., to 5000 for 5 seconds).

### Issue: Downloads stop or browser freezes
**Solution**: 
- Reduce `BATCH_SIZE` to 1
- Increase `DELAY_MS` to 5000
- Close other tabs to free up memory

### Issue: "Date unknown, downloading anyway"
**Solution**: The file's modification date couldn't be determined. The script will download it to be safe.

---

## 📁 After Downloading

### Organize the Files

1. Create a directory structure:
```bash
mkdir -p /workspace/bms_data/uploads_2024
```

2. Move downloaded files:
```bash
mv ~/Downloads/BMS-*.* /workspace/bms_data/uploads_2024/
```

### Process the Documents

Once downloaded, you can process them with the Enhanced Document Processor:

```bash
cd /workspace/001-bms-agent
source .venv/bin/activate
python scripts/process_directory.py /workspace/bms_data/uploads_2024
```

---

## 🎯 Next Steps

After downloading and processing:

1. **Re-index in Qdrant**: The new documents will be added to the vector database
2. **Update Quality Scores**: Run the quality scoring script
3. **Re-run Evaluation**: Test retrieval accuracy with the expanded dataset

```bash
# Re-index documents
python scripts/reindex_documents.py

# Update quality scores
python scripts/update_quality_scores.py

# Run evaluation
python scripts/evaluate_retrieval.py
```

---

## 📝 Notes

- **Browser Compatibility**: Tested on Chrome 120+, Firefox 120+, Edge 120+
- **Network**: Requires stable internet connection
- **Storage**: Ensure you have enough disk space (~200-300 MB estimated)
- **Time**: Plan for 30-60 minutes depending on network speed and file count

---

## ✅ Success Criteria

You'll know it worked when:
- ✅ Console shows "🎉 DOWNLOAD COMPLETE"
- ✅ Downloaded files appear in your Downloads folder
- ✅ File names start with "BMS-" prefix
- ✅ Summary shows downloaded count > 0

---

## 🆘 Need Help?

If you encounter issues:
1. Check the console for error messages
2. Verify you're logged into SharePoint
3. Try reducing batch size and increasing delay
4. Check your network connection
5. Ensure you have sufficient disk space

**Happy Downloading!** 🚀
