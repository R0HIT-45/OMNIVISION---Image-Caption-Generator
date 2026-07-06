# 11_DEPLOYMENT_GUIDE.md
Version 1.0
Status: LOCKED

## 1. Introduction
This document defines the deployment architecture for OmniVision. Because the platform relies heavily on GPU acceleration and large AI models, the deployment strategy focuses on containerization, GPU passthrough, and environment configuration.

## 2. Docker Architecture
OmniVision uses `docker-compose` to orchestrate multiple containers, ensuring the Streamlit frontend and FastAPI backend remain isolated but can communicate over a shared internal network.

### 2.1 Multi-Container Setup
- **`backend` service**: Runs FastAPI via Uvicorn. Exposes port `8000`. Requires NVIDIA Container Toolkit for GPU access.
- **`frontend` service**: Runs Streamlit. Exposes port `8501`. Connects to the backend via HTTP.

### 2.2 Dockerfile (Backend Example)
To minimize image size, the Dockerfile uses a multi-stage build starting from the official NVIDIA PyTorch image.
```dockerfile
FROM pytorch/pytorch:2.1.0-cuda11.8-cudnn8-runtime
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 3. Environment Variables (.env)
A `.env` file must be present at the root directory before deployment.
```env
# Infrastructure
FASTAPI_PORT=8000
STREAMLIT_PORT=8501
BACKEND_URL=http://backend:8000/api/v1

# AI Thresholds
GROUNDING_SIMILARITY_THRESHOLD=0.75
ACTIVE_KNOWLEDGE_PACKS=["heritage_pack"]

# HuggingFace
HF_HOME=/app/cache/huggingface  # Maps to a Docker volume
```

## 4. Local Deployment (Windows/Linux)
For development without Docker:
1. Create a Python Virtual Environment: `python -m venv venv`
2. Activate and install dependencies: `pip install -r requirements.txt`
3. Terminal 1 (Backend): `cd backend && uvicorn app.main:app --reload`
4. Terminal 2 (Frontend): `cd frontend && streamlit run app.py`

## 5. Production Deployment (GPU Server)
For deploying to an AWS EC2 `g4dn.xlarge` (T4 GPU) or a local production server:

1. Ensure Docker and `nvidia-docker2` are installed.
2. Configure `docker-compose.yml` for GPU passthrough:
```yaml
services:
  backend:
    build: ./backend
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    volumes:
      - hf_cache:/app/cache/huggingface
```
3. **Execute**: `docker-compose up -d --build`

### 5.1 Nginx Reverse Proxy
In a true production environment, `Nginx` acts as the ingress controller.
- Traffic on port 80/443 is routed to Streamlit (port 8501).
- API requests can be routed directly to FastAPI if external API access is required.

## 6. HuggingFace Model Caching
Downloading 10GB+ of AI models upon every container restart is unacceptable. 
- The `HF_HOME` environment variable maps the HuggingFace cache to a persistent Docker Volume (`hf_cache`).
- Models are downloaded once. Subsequent container restarts load models instantly from the local disk cache.
