#!/bin/bash
# Monitor migration progress

LOG_FILE="/workspace/logs/full_migration.log"
REPORT_FILE="/workspace/logs/full_migration_report.json"

echo "=== MIGRATION PROGRESS MONITOR ==="
echo

# Check if migration is running
if pgrep -f "simple_migrate_4096d.py" > /dev/null; then
    echo "✓ Migration process is RUNNING"
else
    echo "✗ Migration process is NOT running"
fi

echo

# Count processed documents
PROCESSED=$(grep -c "✓ Uploaded" "$LOG_FILE" 2>/dev/null || echo "0")
FAILED=$(grep -c "✗ Failed" "$LOG_FILE" 2>/dev/null || echo "0")
TOTAL_EXPECTED=620

echo "Documents processed: $PROCESSED / $TOTAL_EXPECTED"
echo "Documents failed: $FAILED"
echo "Progress: $(echo "scale=1; $PROCESSED * 100 / $TOTAL_EXPECTED" | bc)%"
echo

# Show last 5 processed files
echo "--- Last 5 processed files ---"
grep "Processing:" "$LOG_FILE" | tail -5 | sed 's/.*Processing: //'
echo

# Show recent errors if any
ERROR_COUNT=$(grep -c "ERROR" "$LOG_FILE" 2>/dev/null || echo "0")
if [ "$ERROR_COUNT" -gt 0 ]; then
    echo "--- Recent errors (last 3) ---"
    grep "ERROR" "$LOG_FILE" | tail -3
    echo
fi

# Check Qdrant collection status
echo "--- Qdrant Collection Status ---"
curl -s http://localhost:6333/collections/nomad_bms_documents | \
    jq '{points: .result.points_count, vectors: .result.vectors_count, status: .result.status}'
echo

# Check if report exists
if [ -f "$REPORT_FILE" ]; then
    echo "--- Migration Report (if complete) ---"
    jq '{processed: .processed, failed: .failed, chunks: .chunks, elapsed_min: (.elapsed_seconds / 60 | floor)}' "$REPORT_FILE" 2>/dev/null
fi
