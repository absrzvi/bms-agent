# T032: SharePoint Download Script Testing

**Task**: Test SharePoint document download automation  
**Status**: 📋 READY TO START  
**Estimated Time**: 15-20 minutes

---

## 🎯 Objectives

1. Export cookies from SharePoint browser session
2. Test download script with small sample (5 documents)
3. Verify file organization by type
4. Validate error handling
5. Confirm metadata extraction

---

## 📋 Prerequisites

- [ ] Access to SharePoint: `https://nomadrail.sharepoint.com`
- [ ] Browser with cookie export extension installed
- [ ] Python environment activated
- [ ] Download scripts available

---

## 🚀 Step-by-Step Execution

### Step 1: Export Cookies (5 minutes)

**Install Browser Extension**:
- **Chrome/Edge**: [Get cookies.txt LOCALLY](https://chrome.google.com/webstore)
- **Firefox**: [cookies.txt](https://addons.mozilla.org)

**Export Cookies**:
```bash
# 1. Open browser and log into SharePoint
# URL: https://nomadrail.sharepoint.com

# 2. Click extension icon
# 3. Click "Export" or "Export As"
# 4. Choose "Netscape format"
# 5. Save as: sharepoint_cookies.txt
```

**Upload to Server**:
```bash
# Copy to project directory
cp /path/to/sharepoint_cookies.txt /workspace/001-bms-agent/

# Verify file exists
ls -lh /workspace/001-bms-agent/sharepoint_cookies.txt

# Check content (first few lines)
head -5 /workspace/001-bms-agent/sharepoint_cookies.txt
```

**Expected Output**:
```
# Netscape HTTP Cookie File
.sharepoint.com	TRUE	/	TRUE	0	FedAuth	...
.sharepoint.com	TRUE	/	TRUE	0	rtFa	...
```

---

### Step 2: Test Download (5 minutes)

**Activate Environment**:
```bash
cd /workspace/001-bms-agent
source .venv/bin/activate
```

**Test with 5 Documents**:
```bash
python scripts/download_sharepoint_server.py \
    --cookies sharepoint_cookies.txt \
    --csv docs/bms-docs-urls.md \
    --output /workspace/bms_data/test_download \
    --cutoff-date 2023-12-31 \
    --limit 5 \
    --delay 2
```

**Expected Output**:
```
🚀 SharePoint Document Downloader
══════════════════════════════════════════════════════════════════════
✅ Found 1004 documents
✅ Loaded 15 cookies from sharepoint_cookies.txt
⚠️  Limited to first 5 documents for testing

Starting download process...
📋 Total documents: 5
📅 Cutoff date: 2023-12-31
💾 Output directory: /workspace/bms_data/test_download
⏱️  Delay between downloads: 2s

[1/5]
📄 Bid Action Log Check List
   File: BMS-BDEV-FOR-005 Bid Action Log Check List.xlsx
   Last Modified: 2024-03-15 10:30:00
   ⬇️  Downloading...
   📦 Size: 45.23 KB
   💾 Saved to: /workspace/bms_data/test_download/BMS-BDEV-FOR-005...
   ✅ DOWNLOADED

[2/5]
📄 Old Document
   Last Modified: 2022-05-10 08:15:00
   ⏭️  SKIPPED (too old)

...

══════════════════════════════════════════════════════════════════════
🎉 DOWNLOAD COMPLETE
══════════════════════════════════════════════════════════════════════
📊 Total Processed: 5
✅ Downloaded: 3
⏭️  Skipped (old): 2
❌ Errors: 0
💾 Total Size: 156.78 KB
══════════════════════════════════════════════════════════════════════
```

---

### Step 3: Verify File Organization (2 minutes)

**Check Downloaded Files**:
```bash
# List all downloaded files
ls -lh /workspace/bms_data/test_download/

# Expected: Files directly in test_download/
# Example:
# BMS-BDEV-FOR-005 Bid Action Log Check List.xlsx
# BMS-BDEV-FOR-008 Bid Kick Off Template.pptx
# BMS-BDEV-FOR-001 BOR For External Opportunities.docx
```

**Verify File Types**:
```bash
# Check file extensions
file /workspace/bms_data/test_download/*

# Expected output:
# ...Check List.xlsx: Microsoft Excel 2007+
# ...Template.pptx: Microsoft PowerPoint 2007+
# ...Opportunities.docx: Microsoft Word 2007+
```

---

### Step 4: Test Error Handling (3 minutes)

**Test Invalid Cookies**:
```bash
# Rename cookies file
mv /workspace/001-bms-agent/sharepoint_cookies.txt /workspace/001-bms-agent/sharepoint_cookies.txt.bak

# Try download (should fail gracefully)
python scripts/download_sharepoint_server.py --limit 1

# Expected: Error message about missing cookies
# ❌ Cookies file not found: /workspace/001-bms-agent/sharepoint_cookies.txt

# Restore cookies
mv /workspace/001-bms-agent/sharepoint_cookies.txt.bak /workspace/001-bms-agent/sharepoint_cookies.txt
```

**Test Network Error Handling**:
```bash
# Test with invalid URL (should handle gracefully)
# Script should continue processing other documents
```

---

### Step 5: Validate Metadata (2 minutes)

**Check Metadata Extraction**:
```bash
# View download report (if generated)
cat /workspace/bms_data/test_download/download_results.json | jq

# Expected fields:
# - filename
# - size
# - modification_date
# - download_timestamp
# - status (success/failed)
```

**Verify File Sizes**:
```bash
# Check that files are not empty
find /workspace/bms_data/test_download -type f -size 0

# Expected: No output (no zero-byte files)
```

---

## ✅ Acceptance Criteria Checklist

- [ ] **Cookies Exported**: Successfully exported from SharePoint
- [ ] **Script Runs**: `--limit 5` completes without crashes
- [ ] **Files Downloaded**: At least 1-3 files downloaded (depending on dates)
- [ ] **File Organization**: Files saved to correct directory
- [ ] **Error Handling**: Invalid cookies handled gracefully
- [ ] **Metadata Captured**: Filename, size, date extracted correctly
- [ ] **No Crashes**: Script handles errors without crashing
- [ ] **Logs Clear**: Console output is readable and informative

---

## 🔍 Troubleshooting

### Issue: "Cookies file not found"
```bash
# Check file location
ls -lh /workspace/001-bms-agent/sharepoint_cookies.txt

# If missing, re-export from browser
```

### Issue: "HTTP 401: Unauthorized"
```bash
# Cookies expired - re-export fresh cookies
# Log into SharePoint again
# Export new cookies
```

### Issue: "Cannot extract filename"
```bash
# Some URLs may have different formats
# Script will skip these and continue
# Check logs for specific URLs
```

### Issue: No files downloaded (all skipped)
```bash
# All files may be older than cutoff date
# Try earlier cutoff: --cutoff-date 2020-01-01
# Or check specific file dates on SharePoint
```

---

## 📊 Success Metrics

| Metric | Target | Actual |
|--------|--------|--------|
| **Files Processed** | 5 | ___ |
| **Files Downloaded** | 1-5 | ___ |
| **Files Skipped** | 0-4 | ___ |
| **Errors** | 0 | ___ |
| **Script Runtime** | <2 min | ___ |

---

## 🎯 Next Steps

**If T032 Passes**:
1. Clean up test directory: `rm -rf /workspace/bms_data/test_download/`
2. Proceed to **T033**: Full SharePoint download (all post-2023 documents)
3. Update tasks.md: Mark T032 as ✅ COMPLETED

**If T032 Fails**:
1. Review error logs
2. Fix identified issues
3. Re-test with `--limit 5`
4. Document any script improvements needed

---

## 📝 Documentation

**Update After Completion**:
```bash
# Record results in tasks.md
# Note any issues encountered
# Document actual vs expected results
# Capture download statistics
```

**Files to Update**:
- `tasks.md` - Mark T032 complete
- `TESTING.md` - Add test results
- `docs/SHAREPOINT_DOWNLOAD_INSTRUCTIONS.md` - Note any improvements

---

## 🚀 Ready to Start?

```bash
# Quick start command
cd /workspace/001-bms-agent
source .venv/bin/activate

# Export cookies first, then:
python scripts/download_sharepoint_server.py --limit 5
```

**Estimated Total Time**: 15-20 minutes  
**Risk Level**: Low (test only, no production impact)  
**Rollback**: Delete test directory if needed

---

**Good luck with T032!** 🎉
