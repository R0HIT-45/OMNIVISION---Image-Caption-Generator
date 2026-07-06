# 20_PERFORMANCE_BENCHMARK.md
Version 1.0
Status: ACTIVE

## 1. Introduction
Enterprise ML applications must demonstrate consistent, predictable performance across defined hardware bounds. This document records the baseline telemetry, latencies, and resource consumption of the OmniVision pipeline when operating on the target consumer-grade hardware.

## 2. Benchmark Environment
The following hardware and software stack was utilized for all measurements documented below:

| Component | Specification |
|-----------|---------------|
| **OS** | Windows |
| **CPU** | Multi-core x86 Processor |
| **RAM** | System Default |
| **GPU** | NVIDIA GeForce RTX 3050 |
| **VRAM** | 6144MiB (6GB) |
| **Python** | 3.11.x (Required for XTTS) |
| **CUDA** | 11.8 (via `cu118` PyTorch Wheels) |
| **PyTorch** | 2.x (CUDA-enabled) |

## 3. Model Checkpoints & Profiles
OmniVision uses dynamic profiles to balance caption quality against VRAM limits.

**Deployment Profile: DEVELOPMENT**
- **Vision:** `Salesforce/blip-image-captioning-base` (~900MB)
- **Embedding:** `openai/clip-vit-base-patch32` (~600MB)
- **Translation:** `ai4bharat/indictrans2-en-indic-dist-200M` (~1.2GB)
- **TTS:** `Coqui XTTS-v2` (~1.8GB)

**Deployment Profile: DEMO**
- **Vision:** `Salesforce/blip2-opt-2.7b` (4-bit via bitsandbytes) (~2.8GB VRAM)
- *All other models remain identical.*

## 4. Latency Benchmarks (Expected Target)
*(These are theoretical baseline targets. Actual numbers will be populated during the final Verification Sprint inference.)*

| Pipeline Stage | Target Latency (CPU) | Target Latency (RTX 3050 CUDA) |
|----------------|----------------------|--------------------------------|
| **File Validation** | < 0.1s | < 0.1s |
| **Vision Inference (BLIP Base)** | ~3.0s | < 1.0s |
| **Vision Inference (BLIP-2 4-bit)** | N/A (Fails) | ~2.5s |
| **Embedding (CLIP)** | ~0.5s | < 0.2s |
| **Retrieval (FAISS)** | < 0.05s | < 0.05s (CPU Bound) |
| **Grounding Logic** | < 0.05s | < 0.05s |
| **Translation (IndicTrans2)** | ~1.5s | ~0.5s |
| **Speech Synthesis (XTTS-v2)** | ~8.0s | ~2.0s |
| **Total End-to-End Pipeline** | **~13.0s** | **~5.5s** |

## 5. Resource Consumption (VRAM Tracking)
The OmniVision `ModelManager` implements aggressive GPU memory swapping to prevent Out-Of-Memory (OOM) errors on 6GB/4GB GPUs.

- **Peak VRAM Target:** Must not exceed 4,000MB at any stage.
- **Cold Start Time (First Request):** ~15-20 seconds (Models load into RAM/VRAM).
- **Warm Inference Time:** See Latency targets above.
- **Memory Leaks:** `ModelManager.clear_gpu_memory()` enforces `torch.cuda.empty_cache()`. VRAM should return to baseline between requests.

## 6. Stress Testing Targets
- **Throughput:** ~10 Requests Per Minute (RPM) sustained.
- **Concurrency:** The Orchestrator handles sequential loading. Concurrent requests will queue internally or spike CPU RAM if VRAM is locked.

## 7. Next Steps for Final Verification
During Test 12 (Stress Testing), the engineer must populate the *Actual Latency* metrics into this document to finalize the portfolio presentation.
