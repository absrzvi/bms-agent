# 🔄 Automated SharePoint Sync - Quick Reference

## 🚀 One-Time Setup (5 minutes)

```bash
# 1. Run setup script
cd /workspace/001-bms-agent
bash scripts/setup_daily_sync.sh

# 2. Export cookies from browser
# Install extension: "Get cookies.txt LOCALLY"
# Export from: https://nomadrail.sharepoint.com
# Save as: sharepoint_cookies.txt

# 3. Upload cookies
cp sharepoint_cookies.txt /workspace/001-bms-agent/

# 4. Test
./scripts/run_sync.sh --download-only

# 5. Enable daily automation
crontab -e
# Add: 0 2 * * * cd /workspace/001-bms-agent && .venv/bin/python scripts/sharepoint_sync_manager.py >> /workspace/logs/sharepoint_sync_cron.log 2>&1
```

---

## 📁 Directory Structure

```
/workspace/bms_data/
├── incoming/     # Downloaded files (by type: pdf/, docx/, xlsx/, etc.)
├── processing/   # Currently being processed
├── processed/    # Successfully processed (archive)
├── failed/       # Failed documents + error logs
└── uploads/      # API upload directory
```

---

## 🎯 Common Commands

```bash
# Manual sync (last 24 hours)
./scripts/run_sync.sh

# Last 7 days
./scripts/run_sync.sh --lookback-days 7

# Download only (no processing)
./scripts/run_sync.sh --download-only

# View logs
tail -f /workspace/logs/sharepoint_sync.log

# Check status
ls -lh /workspace/bms_data/*/

# View reports
cat /workspace/bms_data/sync_report_*.json | jq
```

---

## 📊 What Happens Daily

```
2:00 AM → Check SharePoint for updates (last 24 hours)
       ↓
       Download new/modified documents (10-50 expected)
       ↓
       Organize by type (pdf/, docx/, xlsx/, etc.)
       ↓
       Process with Enhanced Document Processor v4.0
       ↓
       Ingest to Qdrant database
       ↓
       Archive to processed/ or failed/
       ↓
       Generate report
```

---

## 🔍 Monitoring

```bash
# Check if sync is running
ps aux | grep sharepoint_sync

# View recent syncs
grep "SYNC COMPLETE" /workspace/logs/sharepoint_sync.log

# Check failed documents
ls /workspace/bms_data/failed/
cat /workspace/bms_data/failed/*/*.error.txt

# Database status
curl -s http://localhost:6333/collections/nomad_bms_documents | jq '.result.points_count'
```

---

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| **No files downloaded** | Re-export cookies, check cutoff date |
| **Processing failures** | Check `/workspace/bms_data/failed/` for error logs |
| **Cookies expired** | Re-export from browser (weekly) |
| **Disk space full** | Archive old processed files |

---

## 📚 Full Documentation

- **Complete Guide**: `docs/AUTOMATED_SYNC_GUIDE.md`
- **System Overview**: `docs/SYNC_SYSTEM_OVERVIEW.md`
- **Cookie Setup**: `docs/COOKIE_EXTRACTION_GUIDE.md`
- **Quick Start**: `docs/QUICK_START_DOWNLOAD.md`

---

## ✅ Success Indicators

- ✅ Logs show daily "SYNC COMPLETE"
- ✅ New files in `processed/` directory
- ✅ Qdrant document count increases
- ✅ Daily reports generated
- ✅ Search returns recent documents

---

## 🆘 Quick Help

```bash
# Reprocess failed documents
mv /workspace/bms_data/failed/*/* /workspace/bms_data/incoming/
./scripts/run_sync.sh

# Full resync (last 30 days)
./scripts/run_sync.sh --lookback-days 30

# Check cron status
crontab -l
grep CRON /var/log/syslog

# Test processor
python -c "
from bms_agent.scr.enhanced_document_processor import EnhancedDocumentProcessor
proc = EnhancedDocumentProcessor()
print('Processor loaded successfully')
"
```

---

**Your automated SharePoint sync is ready! 🎉**

Set it up once, and it runs daily automatically, keeping your BMS knowledge base always up-to-date.
