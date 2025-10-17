# Quick Start: Hybrid CPU+GPU Document Processing

## TL;DR - Run This Now

```bash
# Hybrid mode (RECOMMENDED): 4 CPU workers + 1 GPU worker
python scripts/batch_process_parallel.py -w 4 --gpu-workers 1
```

## What's New?

Your batch processing script now supports **hybrid CPU+GPU mode** - using both CPU and GPU workers together for maximum throughput while avoiding CUDA out of memory errors.

## Usage Examples

### 1. Hybrid Mode (Best Performance)

```bash
# Default: 4 CPU workers + 1 GPU worker
python scripts/batch_process_parallel.py -w 4 --gpu-workers 1

# More CPU workers for large batches
python scripts/batch_process_parallel.py -w 8 --gpu-workers 1

# Maximum parallelism (if you have many CPU cores)
python scripts/batch_process_parallel.py -w 16 --gpu-workers 1
```

**When to use:**
- ✅ Production workloads
- ✅ Large batches (100+ documents)
- ✅ When you want maximum throughput
- ✅ GPU is available but you need parallelism

### 2. CPU-Only Mode (Safest)

```bash
# Pure CPU mode - no GPU usage
python scripts/batch_process_parallel.py -w 8 --cpu-only

# Maximum CPU workers
python scripts/batch_process_parallel.py -w 16 --cpu-only
```

**When to use:**
- ✅ GPU is busy with other tasks
- ✅ CUDA errors persist
- ✅ You want guaranteed stability
- ✅ Processing very large batches (1000+ docs)

### 3. Single-Threaded (Testing)

```bash
# Single document with GPU (fastest per-doc)
python scripts/batch_process_incoming.py

# Single document with CPU (if GPU busy)
python scripts/batch_process_incoming.py --cpu
```

**When to use:**
- ✅ Testing single documents
- ✅ Debugging processing issues
- ✅ Small batches (<10 documents)

## How It Works

### Hybrid Mode Architecture

```
┌─────────────────────────────────────────┐
│         Document Queue (100 files)      │
└─────────────────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        │   Round-Robin         │
        │   Distribution        │
        └───────────┬───────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
    ┌───▼────┐            ┌─────▼─────┐
    │ GPU    │            │ CPU       │
    │ Worker │            │ Workers   │
    │   1x   │            │   4x      │
    └───┬────┘            └─────┬─────┘
        │                       │
        └───────────┬───────────┘
                    │
            ┌───────▼────────┐
            │  Qdrant DB     │
            │  (768-d vecs)  │
            └────────────────┘
```

### Task Distribution

- **GPU Worker**: Processes every 5th document (faster per-doc)
- **CPU Workers**: Process remaining documents (parallel throughput)
- **Result**: Best of both worlds - speed + parallelism

## Performance Expectations

| Configuration | Throughput | Use Case |
|--------------|------------|----------|
| 4 CPU + 1 GPU | 3-5 docs/sec | General production |
| 8 CPU + 1 GPU | 6-10 docs/sec | Large batches |
| 16 CPU only | 5-10 docs/sec | Very large batches |
| 1 GPU only | 0.5-1 doc/sec | Small batches |

## Monitoring

### Check GPU Usage

```bash
# Real-time GPU monitoring
watch -n 1 nvidia-smi

# Should see only 1 Python process using GPU
```

### Check Progress

```bash
# Watch processing logs
tail -f /workspace/logs/batch_processing_parallel.log

# The script shows real-time progress:
# [45/100] document.pdf ✅ [GPU] 23 chunks, quality: 0.85
#   Progress: 45.0% | Rate: 4.2 docs/sec | ETA: 2.2 min | CPU: 36 GPU: 9
```

## Troubleshooting

### Still Getting CUDA OOM?

1. **Reduce GPU workers to 0:**
   ```bash
   python scripts/batch_process_parallel.py -w 8 --cpu-only
   ```

2. **Clear stuck GPU processes:**
   ```bash
   ./scripts/clear_gpu_memory.sh
   ```

3. **Check what's using GPU:**
   ```bash
   nvidia-smi
   ```

### Slow Performance?

1. **Increase CPU workers:**
   ```bash
   python scripts/batch_process_parallel.py -w 16 --gpu-workers 1
   ```

2. **Check CPU usage:**
   ```bash
   htop
   ```

3. **Verify Qdrant is running:**
   ```bash
   curl http://localhost:6333/collections
   ```

## Advanced Configuration

### Environment Variables

```bash
# Force CPU globally (overrides all settings)
export CUDA_VISIBLE_DEVICES=""

# Limit PyTorch threads per worker
export OMP_NUM_THREADS=1

# Run with settings
python scripts/batch_process_parallel.py -w 8 --cpu-only
```

### Custom Worker Ratios

```bash
# More GPU workers (risky - may cause OOM)
python scripts/batch_process_parallel.py -w 4 --gpu-workers 2

# All CPU workers
python scripts/batch_process_parallel.py -w 32 --cpu-only
```

## Summary

✅ **Hybrid mode** gives you the best of both worlds  
✅ **1 GPU worker** prevents CUDA OOM errors  
✅ **Multiple CPU workers** maximize throughput  
✅ **Automatic load balancing** between devices  
✅ **Real-time monitoring** of CPU vs GPU usage  

**Recommended command:**
```bash
python scripts/batch_process_parallel.py -w 4 --gpu-workers 1
```

This will process your documents efficiently without running into memory issues!
