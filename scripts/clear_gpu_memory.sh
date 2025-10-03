#!/bin/bash
# Clear GPU Memory - Kill stuck processes
# Use this if you get CUDA OOM errors

echo "🔍 Checking GPU memory usage..."
nvidia-smi

echo ""
echo "⚠️  WARNING: This will kill all Python processes using GPU memory"
echo "Press Ctrl+C to cancel, or Enter to continue..."
read

echo ""
echo "🔪 Killing Python processes..."

# Get all Python process IDs using GPU
PIDS=$(nvidia-smi --query-compute-apps=pid --format=csv,noheader)

if [ -z "$PIDS" ]; then
    echo "✅ No GPU processes found"
else
    for PID in $PIDS; do
        echo "Killing process $PID..."
        kill -9 $PID 2>/dev/null || sudo kill -9 $PID 2>/dev/null
    done
    
    echo ""
    echo "⏳ Waiting for GPU memory to clear..."
    sleep 3
    
    echo ""
    echo "🔍 GPU memory after cleanup:"
    nvidia-smi
fi

echo ""
echo "✅ Done! You can now run your batch processing with --cpu flag"
echo "   Example: python scripts/batch_process_parallel.py -w 4"
