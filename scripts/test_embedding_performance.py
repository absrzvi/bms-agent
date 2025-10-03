#!/usr/bin/env python3
"""
Test embedding generation performance to diagnose bottleneck
"""

import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "bms-agent" / "scr"))

from sentence_transformers import SentenceTransformer
import torch

print("="*80)
print("🔍 Embedding Performance Diagnostic")
print("="*80)
print()

# Test 1: Check CUDA availability
print("1️⃣ CUDA Availability:")
print(f"   CUDA Available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"   CUDA Device: {torch.cuda.get_device_name(0)}")
    print(f"   CUDA Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
print()

# Test 2: Load model on CPU
print("2️⃣ Loading model on CPU...")
start = time.time()
model_cpu = SentenceTransformer('sentence-transformers/all-mpnet-base-v2', device='cpu')
load_time_cpu = time.time() - start
print(f"   ✅ CPU Model loaded in {load_time_cpu:.2f} seconds")
print()

# Test 3: Load model on GPU (if available)
if torch.cuda.is_available():
    print("3️⃣ Loading model on GPU...")
    start = time.time()
    model_gpu = SentenceTransformer('sentence-transformers/all-mpnet-base-v2', device='cuda')
    load_time_gpu = time.time() - start
    print(f"   ✅ GPU Model loaded in {load_time_gpu:.2f} seconds")
    print()

# Test 4: Generate embeddings on CPU
print("4️⃣ Testing CPU embedding generation...")
test_texts = [
    "This is a test document about railway safety procedures.",
    "Employee handbook section on leave policies.",
    "Information security guidelines for data protection.",
    "Network configuration standards for train systems.",
]

start = time.time()
embeddings_cpu = model_cpu.encode(test_texts, convert_to_numpy=True, show_progress_bar=False)
cpu_time = time.time() - start
print(f"   ✅ Generated {len(test_texts)} embeddings in {cpu_time:.3f} seconds")
print(f"   ⚡ Rate: {len(test_texts)/cpu_time:.2f} embeddings/sec")
print(f"   📊 Embedding shape: {embeddings_cpu.shape}")
print()

# Test 5: Generate embeddings on GPU (if available)
if torch.cuda.is_available():
    print("5️⃣ Testing GPU embedding generation...")
    start = time.time()
    embeddings_gpu = model_gpu.encode(test_texts, convert_to_numpy=True, show_progress_bar=False)
    gpu_time = time.time() - start
    print(f"   ✅ Generated {len(test_texts)} embeddings in {gpu_time:.3f} seconds")
    print(f"   ⚡ Rate: {len(test_texts)/gpu_time:.2f} embeddings/sec")
    print(f"   📊 Embedding shape: {embeddings_gpu.shape}")
    print(f"   🚀 Speedup: {cpu_time/gpu_time:.2f}x faster than CPU")
    print()

# Test 6: Batch size impact
print("6️⃣ Testing batch size impact on CPU...")
batch_sizes = [1, 4, 8, 16, 32]
for batch_size in batch_sizes:
    test_batch = test_texts * (batch_size // len(test_texts) + 1)
    test_batch = test_batch[:batch_size]
    
    start = time.time()
    _ = model_cpu.encode(test_batch, convert_to_numpy=True, show_progress_bar=False, batch_size=batch_size)
    elapsed = time.time() - start
    rate = batch_size / elapsed
    print(f"   Batch size {batch_size:2d}: {elapsed:.3f}s ({rate:.2f} emb/sec)")
print()

# Test 7: Memory usage
print("7️⃣ Memory Usage:")
import psutil
process = psutil.Process()
mem_info = process.memory_info()
print(f"   RSS Memory: {mem_info.rss / 1e9:.2f} GB")
print(f"   VMS Memory: {mem_info.vms / 1e9:.2f} GB")
if torch.cuda.is_available():
    print(f"   GPU Memory: {torch.cuda.memory_allocated() / 1e9:.2f} GB")
print()

print("="*80)
print("✅ Diagnostic Complete")
print("="*80)
