# 16_SYSTEM_OPERATIONS_GUIDE.md
Version 1.0
Status: LOCKED

## 1. Introduction
This System Operations Guide defines the procedures for starting, monitoring, and maintaining the OmniVision AI Platform in a production-like environment. It ensures system stability and provides runbooks for handling operational failures.

## 2. Startup Sequence
To prevent race conditions, the platform must be booted in a strict order.

### 2.1 Boot Order (Local/Dev)
1. **Verify Environment**: Ensure `.env` is populated with `HF_HOME`, thresholds, and ports.
2. **Backend Initialization**: Run `uvicorn app.main:app --port 8000`.
   - The `ModelManager` initializes in an empty state (no VRAM consumed).
   - The `RetrievalService` loads the FAISS index from disk into CPU RAM.
3. **Frontend Initialization**: Run `streamlit run app.py`.
   - Streamlit boots and binds to port 8501.

### 2.2 Boot Order (Docker)
`docker-compose up -d` handles the boot order automatically using `depends_on`:
```yaml
services:
  frontend:
    depends_on:
      backend:
        condition: service_healthy
```

## 3. Health Checks & Monitoring
### 3.1 Liveness Probe
The `GET /api/v1/health` endpoint serves as the liveness probe. If deployed to Kubernetes or a cloud load balancer, this endpoint should return HTTP 200 within 2 seconds.

### 3.2 Resource Monitoring
When running on constrained hardware (RTX 3050):
- **Command**: Run `watch -n 1 nvidia-smi` in a separate terminal.
- **Expected Behavior**: VRAM should spike to ~2.4GB during the Vision Phase, drop to ~400MB during cleanup, and spike to ~2GB during the Audio Phase. If it consistently hits 4096MB and triggers OOM, the cleanup utility in `utils/memory_utils.py` is failing.

## 4. Log Rotation Strategy
AI applications generate massive logs due to tensor shape debugging and request tracing.
- **Implementation**: The backend uses Python's `logging.handlers.TimedRotatingFileHandler`.
- **Policy**: Logs are rotated daily at midnight (`when='midnight'`) and kept for 7 days (`backupCount=7`). Older logs are automatically deleted to prevent disk exhaustion.

## 5. Failure Recovery Runbooks

### 5.1 Issue: CUDA Out of Memory (OOM)
- **Symptom**: HTTP 500 error, logs show `RuntimeError: CUDA out of memory`.
- **Resolution**: 
  1. Restart the FastAPI server to clear zombie GPU processes.
  2. Verify that `ModelManager.unload_model()` is correctly invoking `gc.collect()` and `torch.cuda.empty_cache()`.
  3. Ensure no other applications (e.g., Chrome with hardware acceleration) are consuming VRAM.

### 5.2 Issue: FAISS Index Corruption
- **Symptom**: Retrieval service throws segmentation faults or returns garbage text.
- **Resolution**: Delete the `index.faiss` file in the Knowledge Pack directory and re-run the offline embedding script (`scripts/build_knowledge_pack.py`) to regenerate the index from the pristine `metadata.json`.

### 5.3 Issue: HuggingFace Download Hanging
- **Symptom**: Application hangs indefinitely on first request; no logs are produced.
- **Resolution**: Ensure the server has internet access for the initial download. If air-gapped, manually transfer the `.cache/huggingface` folder from a connected machine to the target server's `HF_HOME` directory.
