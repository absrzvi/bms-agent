# Quick Start: Download SharePoint Documents

## 🚀 5-Minute Setup

### Step 1: Export Cookies (2 minutes)

**Chrome/Edge**:
1. Install extension: [Get cookies.txt LOCALLY](https://chrome.google.com/webstore)
2. Go to: `https://nomadrail.sharepoint.com` and log in
3. Click extension icon → Export → Save as `sharepoint_cookies.txt`

**Firefox**:
1. Install extension: [cookies.txt](https://addons.mozilla.org)
2. Go to: `https://nomadrail.sharepoint.com` and log in
3. Click extension icon → Export → Save as `sharepoint_cookies.txt`

### Step 2: Upload Cookies to Server (1 minute)

```bash
# Option A: Direct copy (if you have file access)
cp /path/to/sharepoint_cookies.txt /workspace/001-bms-agent/

# Option B: SCP from your machine
scp sharepoint_cookies.txt user@server:/workspace/001-bms-agent/

# Option C: Create and paste
nano /workspace/001-bms-agent/sharepoint_cookies.txt
# Paste content, Ctrl+O to save, Ctrl+X to exit
```

### Step 3: Run Download Script (2 minutes)

```bash
cd /workspace/001-bms-agent
source .venv/bin/activate

# Test with 5 files first
python scripts/download_sharepoint_server.py --limit 5

# If successful, download all
python scripts/download_sharepoint_server.py
```

---

## 📊 What to Expect

```
🚀 SharePoint Document Downloader
══════════════════════════════════════════════════════════════════
✅ Found 1004 documents
✅ Loaded 15 cookies

Starting download process...
📋 Total documents: 1004
📅 Cutoff date: 2023-12-31
💾 Output directory: /workspace/bms_data/uploads_2024
⏱️  Delay between downloads: 2s

[1/1004]
📄 Bid Action Log Check List
   ⬇️  Downloading...
   ✅ DOWNLOADED (45.23 KB)

[2/1004]
📄 Old Document
   ⏭️  SKIPPED (too old)
```

**Time**: ~30-60 minutes for all files  
**Output**: `/workspace/bms_data/uploads_2024/`

---

## 🎯 Common Commands

```bash
# Test with first 5 documents
python scripts/download_sharepoint_server.py --limit 5

# Download all recent files (after 2023-12-31)
python scripts/download_sharepoint_server.py

# Custom cutoff date
python scripts/download_sharepoint_server.py --cutoff-date 2024-01-01

# Custom output directory
python scripts/download_sharepoint_server.py --output /custom/path

# Faster downloads (1 second delay)
python scripts/download_sharepoint_server.py --delay 1

# Show help
python scripts/download_sharepoint_server.py --help
```

---

## ⚠️ Troubleshooting

### "Cookies file not found"
```bash
# Check if file exists
ls -lh /workspace/001-bms-agent/sharepoint_cookies.txt

# If missing, create it
nano /workspace/001-bms-agent/sharepoint_cookies.txt
```

### "HTTP 401: Unauthorized"
Your cookies expired. Re-export fresh cookies from browser.

### "HTTP 429: Too Many Requests"
Slow down the downloads:
```bash
python scripts/download_sharepoint_server.py --delay 5
```

---

## 📁 After Downloading

### 1. Check Downloaded Files
```bash
ls -lh /workspace/bms_data/uploads_2024/
```

### 2. Process with Enhanced Document Processor
```bash
cd /workspace/001-bms-agent
source .venv/bin/activate
python scripts/process_directory.py /workspace/bms_data/uploads_2024
```

### 3. Re-index in Qdrant
```bash
python scripts/reindex_documents.py
```

### 4. Run Evaluation
```bash
python scripts/evaluate_retrieval.py
```

---

## 🔒 Security Reminder

```bash
# Delete cookies after use
rm /workspace/001-bms-agent/sharepoint_cookies.txt

# Verify it's in .gitignore
grep cookies .gitignore
```

---

## ✨ That's It!

No OAuth, no Azure AD, no complex authentication.  
Just cookies → download → process. 🎉

**Full Documentation**:
- Cookie Guide: `docs/COOKIE_EXTRACTION_GUIDE.md`
- Browser Script: `docs/SHAREPOINT_DOWNLOAD_INSTRUCTIONS.md`
