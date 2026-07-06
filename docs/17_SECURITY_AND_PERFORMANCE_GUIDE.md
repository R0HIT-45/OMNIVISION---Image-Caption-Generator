# 17_SECURITY_AND_PERFORMANCE_GUIDE.md
Version 1.0
Status: LOCKED

## 1. Introduction
This guide covers the proactive measures implemented in OmniVision to secure the application against malicious input and to optimize AI inference speed and resource utilization on consumer hardware.

## 2. Security Architecture

### 2.1 Input Validation & Secure File Handling
Allowing users to upload files to a server is a significant attack vector. OmniVision mitigates this through multiple layers:
1. **Size Limits**: Enforced at the FastAPI layer. Uploads exceeding `MAX_UPLOAD_SIZE_MB` (10MB) are rejected before being fully buffered into RAM, preventing Denial of Service (DoS) attacks via memory exhaustion.
2. **MIME Type Validation**: The `ImageService` explicitly checks the file signature (magic bytes) using the `python-magic` library or PIL verification, rather than relying solely on the file extension (e.g., rejecting an `.exe` disguised as `.jpg`).
3. **Path Traversal Prevention**: Uploaded files are immediately renamed to a secure UUID (e.g., `550e8400.jpg`). Original filenames are discarded or heavily sanitized to prevent directory traversal attacks (e.g., `../../../etc/passwd`).

### 2.2 API Protection
- **CORS Configuration**: The FastAPI backend explicitly configures Cross-Origin Resource Sharing (CORS) to only accept requests from the Streamlit frontend origin (`http://localhost:8501`), blocking unauthorized external domains from invoking expensive GPU endpoints.
- **Concurrency Limiting**: Implemented a strict semaphore in the `RequestCoordinator`. If `concurrent_requests > 1`, the server returns `HTTP 429 Too Many Requests` to prevent the GPU from crashing under spam.

## 3. Performance Optimization

### 3.1 Model Caching & Resource Limits
- **Singleton Pattern**: The `ModelManager` guarantees that massive models like BLIP-2 (1.8GB) are loaded exactly once into VRAM (or RAM) and kept hot until explicitly swapped out.
- **Lazy Loading**: Models are not loaded during server boot, reducing startup time from 30 seconds to 1 second. Models load during the first user request.

### 3.2 Memory Optimization (VRAM)
Operating a multimodal pipeline on an RTX 3050 (4GB) requires extreme optimization:
1. **4-bit Quantization**: BLIP-2 is loaded using `bitsandbytes` (`load_in_4bit=True`). This slashes the VRAM footprint from ~5.5GB (FP16) down to ~1.8GB, making it viable on consumer hardware.
2. **Distilled Translation**: IndicTrans2 uses the `dist-200M` parameter model instead of the base model, heavily reducing translation latency and memory.
3. **CPU Offloading**: 
   - FAISS executes entirely on the CPU. Vector search over thousands of records takes milliseconds on a modern CPU, saving VRAM.
   - When XTTS (Speech Synthesis) is invoked, the `ModelManager` moves the BLIP-2 model weights from GPU VRAM back to system RAM (CPU) to make room, rather than deleting and re-downloading them.

### 3.3 CPU/GPU Utilization
- **Async I/O**: Network requests, file saving, and database queries (v2.0) are asynchronous. The CPU thread is yielded back to the event loop during these operations, keeping the API highly responsive.
- **Synchronous Inference Threading**: Because PyTorch inference is CPU/GPU blocking, the Orchestrator offloads `model.generate()` calls to a background thread pool (`run_in_threadpool`) to prevent the FastAPI event loop from freezing.
