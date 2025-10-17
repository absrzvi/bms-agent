# Automated SharePoint Sync Guide

## Overview

Complete automated solution for daily SharePoint document synchronization with proper directory structure, error handling, and processing pipeline.

**Features**:
- ✅ Daily automated sync (checks for updates)
- ✅ Organized directory structure by file type
- ✅ Automatic processing with Enhanced Document Processor v4.0
- ✅ Error handling with failed document tracking
- ✅ Processed document archiving
- ✅ Comprehensive logging and reporting

---

## 📁 Directory Structure

```
/workspace/bms_data/
├── incoming/              # Downloaded files organized by type
│   ├── pdf/              # PDF documents
│   ├── docx/             # Word documents
│   ├── xlsx/             # Excel spreadsheets
│   ├── pptx/             # PowerPoint presentations
│   ├── csv/              # CSV files
│   └── txt/              # Text files
│
├── processing/            # Files currently being processed
│   └── [files being processed]
│
├── processed/             # Successfully processed (archive)
│   ├── pdf/              # Archived PDFs
│   ├── docx/             # Archived Word docs
│   └── ...               # Other types
│
├── failed/                # Failed to process
│   ├── pdf/              # Failed PDFs
│   │   ├── document.pdf
│   │   └── document.pdf.error.txt  # Error log
│   └── ...
│
└── uploads/               # API upload directory (existing)
```

---

## 🚀 Quick Start

### Step 1: Setup (One-time)

```bash
cd /workspace/001-bms-agent

# Run setup script
bash scripts/setup_daily_sync.sh
```

This creates:
- Directory structure
- Cron job template
- Systemd timer files
- Wrapper scripts

### Step 2: Export Cookies

```bash
# Export cookies from browser (see COOKIE_EXTRACTION_GUIDE.md)
# Save as: /workspace/001-bms-agent/sharepoint_cookies.txt
```

### Step 3: Test Manually

```bash
# Test with download only (no processing)
./scripts/run_sync.sh --download-only

# Test full sync (last 24 hours)
./scripts/run_sync.sh

# Test with last 7 days
./scripts/run_sync.sh --lookback-days 7
```

### Step 4: Enable Daily Automation

Choose one method:

**Option A: Cron (Simple)**
```bash
crontab -e
# Add this line:
0 2 * * * cd /workspace/001-bms-agent && .venv/bin/python scripts/sharepoint_sync_manager.py >> /workspace/logs/sharepoint_sync_cron.log 2>&1
```

**Option B: Systemd Timer (Robust)**
```bash
sudo cp /tmp/sharepoint-sync.service /etc/systemd/system/
sudo cp /tmp/sharepoint-sync.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable sharepoint-sync.timer
sudo systemctl start sharepoint-sync.timer
```

---

## 🔄 Workflow

### Daily Sync Process

```
1. DOWNLOAD
   ├─ Check SharePoint for updates (last 24 hours)
   ├─ Download new/modified documents
   └─ Save to temp directory

2. ORGANIZE
   ├─ Detect file type (pdf, docx, xlsx, etc.)
   ├─ Move to incoming/{type}/ directory
   └─ Handle duplicates with timestamps

3. PROCESS
   ├─ Move file to processing/
   ├─ Process with Enhanced Document Processor v4.0
   ├─ Extract text, chunk, generate embeddings
   ├─ Ingest to Qdrant database
   └─ Move to processed/{type}/ or failed/{type}/

4. REPORT
   ├─ Generate sync report (JSON)
   ├─ Log statistics
   └─ Update monitoring metrics
```

---

## 📊 Usage Examples

### Manual Sync

```bash
# Daily sync (last 24 hours)
python scripts/sharepoint_sync_manager.py

# Last 7 days
python scripts/sharepoint_sync_manager.py --lookback-days 7

# Custom date range
python scripts/sharepoint_sync_manager.py --cutoff-date 2024-01-01

# Download only (no processing)
python scripts/sharepoint_sync_manager.py --download-only

# Custom directories
python scripts/sharepoint_sync_manager.py --base-dir /custom/path
```

### Using Wrapper Script

```bash
# Quick daily sync
./scripts/run_sync.sh

# With options
./scripts/run_sync.sh --lookback-days 7
./scripts/run_sync.sh --download-only
```

### Check Status

```bash
# View logs
tail -f /workspace/logs/sharepoint_sync.log

# Check directory status
ls -lh /workspace/bms_data/incoming/pdf/
ls -lh /workspace/bms_data/processed/
ls -lh /workspace/bms_data/failed/

# View sync reports
ls -lh /workspace/bms_data/sync_report_*.json
cat /workspace/bms_data/sync_report_20250930_020000.json
```

---

## 📈 Expected Output

### Console Output

```
══════════════════════════════════════════════════════════════════════
🚀 SHAREPOINT SYNC MANAGER STARTED
══════════════════════════════════════════════════════════════════════
Timestamp: 2025-09-30T02:00:00
Lookback: 1 days
Cutoff Date: 2025-09-29

Initializing SharePoint downloader...
✅ Loaded 15 cookies from sharepoint_cookies.txt
✅ Downloader ready (cutoff: 2025-09-29)

══════════════════════════════════════════════════════════════════════
STEP 1: DOWNLOADING FROM SHAREPOINT
══════════════════════════════════════════════════════════════════════
📋 Found 1004 documents in catalog

[1/1004]
📄 Bid Action Log Check List
   File: BMS-BDEV-FOR-005 Bid Action Log Check List.xlsx
   Last Modified: 2025-09-29 15:30:00
   ⬇️  Downloading...
   📦 Size: 45.23 KB
   💾 Saved to: /workspace/bms_data/temp_downloads/...
   ✅ DOWNLOADED

[2/1004]
📄 Old Document
   Last Modified: 2024-01-15 10:00:00
   ⏭️  SKIPPED (too old)

✅ Downloaded: 15
⏭️  Skipped: 989

══════════════════════════════════════════════════════════════════════
STEP 2: ORGANIZING FILES BY TYPE
══════════════════════════════════════════════════════════════════════
📁 Found 15 files to organize
  ✅ document1.pdf → pdf/
  ✅ document2.docx → docx/
  ✅ document3.xlsx → xlsx/
✅ Organized: 15 files

══════════════════════════════════════════════════════════════════════
STEP 3: PROCESSING DOCUMENTS
══════════════════════════════════════════════════════════════════════
📄 Found 15 files to process
✅ Enhanced Document Processor v4.0 loaded

📄 Processing: document1.pdf
  ✅ Processed successfully

📄 Processing: document2.docx
  ❌ Processing failed: Invalid format

✅ Processed: 14
❌ Failed: 1

══════════════════════════════════════════════════════════════════════
🎉 SYNC COMPLETE
══════════════════════════════════════════════════════════════════════
📅 Cutoff Date: 2025-09-29
⬇️  Downloaded: 15
📁 Organized: 15
✅ Processed: 14
❌ Failed: 1
⏭️  Skipped: 989
══════════════════════════════════════════════════════════════════════

📊 Directory Status:
  incoming    :    0 files
  processed   :   14 files
  failed      :    1 files

💾 Report saved: /workspace/bms_data/sync_report_20250930_020000.json
```

### Sync Report (JSON)

```json
{
  "timestamp": "2025-09-30T02:00:00",
  "cutoff_date": "2025-09-29",
  "lookback_days": 1,
  "stats": {
    "downloaded": 15,
    "organized": 15,
    "processed": 14,
    "failed": 1,
    "skipped": 989
  },
  "directories": {
    "incoming": 0,
    "processing": 0,
    "processed": 14,
    "failed": 1
  }
}
```

---

## 🔧 Configuration

### Environment Variables

```bash
# Optional: Set in ~/.bashrc or environment
export BMS_UPLOAD_PATH="/workspace/bms_data/uploads"
export BMS_SYNC_LOOKBACK_DAYS=1
export BMS_SYNC_SCHEDULE="0 2 * * *"  # 2 AM daily
```

### Script Options

```python
# In sharepoint_sync_manager.py
LOOKBACK_DAYS = 1           # Days to look back for updates
DELAY_BETWEEN_DOWNLOADS = 2  # Seconds between downloads
MAX_RETRIES = 2             # Retry attempts for failed downloads
```

---

## 📝 Monitoring

### Check Sync Status

```bash
# View recent logs
tail -100 /workspace/logs/sharepoint_sync.log

# Check for errors
grep ERROR /workspace/logs/sharepoint_sync.log

# View failed documents
ls -lh /workspace/bms_data/failed/*/
cat /workspace/bms_data/failed/pdf/document.pdf.error.txt
```

### Systemd Timer Status

```bash
# Check timer status
sudo systemctl status sharepoint-sync.timer

# View timer schedule
sudo systemctl list-timers

# View last run
sudo journalctl -u sharepoint-sync.service -n 50

# Manual trigger
sudo systemctl start sharepoint-sync.service
```

### Cron Status

```bash
# View cron jobs
crontab -l

# Check cron logs
grep CRON /var/log/syslog
tail -f /workspace/logs/sharepoint_sync_cron.log
```

---

## 🔍 Troubleshooting

### Issue: No files downloaded

**Check**:
```bash
# Verify cookies are valid
ls -lh /workspace/001-bms-agent/sharepoint_cookies.txt

# Test download manually
python scripts/download_sharepoint_server.py --limit 5

# Check cutoff date
python scripts/sharepoint_sync_manager.py --lookback-days 7
```

### Issue: Processing failures

**Check**:
```bash
# View error logs
ls /workspace/bms_data/failed/
cat /workspace/bms_data/failed/pdf/*.error.txt

# Test processor manually
cd /workspace/001-bms-agent
python -c "
from bms_agent.scr.enhanced_document_processor import EnhancedDocumentProcessor
proc = EnhancedDocumentProcessor()
result = proc.process_document('/path/to/file.pdf')
print(result)
"
```

### Issue: Cookies expired

**Solution**:
```bash
# Re-export cookies from browser
# See: docs/COOKIE_EXTRACTION_GUIDE.md

# Replace old cookies
cp new_cookies.txt /workspace/001-bms-agent/sharepoint_cookies.txt

# Test
./scripts/run_sync.sh --download-only
```

### Issue: Disk space

**Check**:
```bash
# Check disk usage
df -h /workspace

# Clean old processed files (optional)
find /workspace/bms_data/processed/ -mtime +30 -delete

# Archive old files
tar -czf processed_archive_$(date +%Y%m).tar.gz /workspace/bms_data/processed/
```

---

## 🎯 Best Practices

### 1. Cookie Management
- Re-export cookies weekly
- Store securely
- Delete after testing

### 2. Monitoring
- Check logs daily
- Review failed documents weekly
- Monitor disk space

### 3. Maintenance
- Archive processed files monthly
- Clean temp directories
- Update sync reports

### 4. Testing
- Test manually before automation
- Use `--download-only` for testing
- Start with short lookback periods

---

## 📊 Performance

### Expected Metrics

| Metric | Value |
|--------|-------|
| **Download Speed** | 2-5 files/minute |
| **Processing Speed** | 1,135 chars/second |
| **Daily Updates** | 10-50 documents |
| **Sync Duration** | 5-30 minutes |
| **Disk Usage** | ~500 MB/month |

### Optimization

```bash
# Faster downloads (reduce delay)
python scripts/sharepoint_sync_manager.py --delay 1

# Process in parallel (future enhancement)
# Currently sequential for stability
```

---

## 🔄 Recovery

### Reprocess Failed Documents

```bash
# Move failed back to incoming
mv /workspace/bms_data/failed/pdf/* /workspace/bms_data/incoming/pdf/

# Run sync (will process incoming files)
./scripts/run_sync.sh
```

### Full Resync

```bash
# Download all documents (last 30 days)
python scripts/sharepoint_sync_manager.py --lookback-days 30

# Or custom date
python scripts/sharepoint_sync_manager.py --cutoff-date 2024-01-01
```

---

## ✅ Success Criteria

You'll know it's working when:
- ✅ Cron/timer runs daily without errors
- ✅ New documents appear in `incoming/` directories
- ✅ Files move to `processed/` after processing
- ✅ Sync reports generated daily
- ✅ Logs show successful completions
- ✅ Qdrant database updated with new documents

---

## 📚 Related Documentation

- **Cookie Setup**: `docs/COOKIE_EXTRACTION_GUIDE.md`
- **Quick Start**: `docs/QUICK_START_DOWNLOAD.md`
- **Enhanced Processor**: `docs/enhanced-document-processor-v4.md`
- **API Documentation**: `docs/API.md`

---

## 🆘 Support

If issues persist:
1. Check all logs in `/workspace/logs/`
2. Verify directory permissions
3. Test components individually
4. Review error messages in failed documents
5. Ensure cookies are fresh and valid

**Your automated SharePoint sync is ready!** 🎉
