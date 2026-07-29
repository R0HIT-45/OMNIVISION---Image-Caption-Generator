FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    git \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Install CUDA-enabled PyTorch first (cached layer)
RUN pip3 install torch==2.1.2+cu118 torchvision==0.16.2+cu118 torchaudio==2.1.2+cu118 --index-url https://download.pytorch.org/whl/cu118

# Install Python dependencies
COPY requirements-base.txt requirements-lock.txt* ./ 
RUN pip3 install -r requirements-base.txt

# Copy entire project
COPY . .

# Ensure directories exist
RUN mkdir -p static/uploads static/audio knowledge_base

# Create non-root user
RUN useradd -m -u 1000 omnivision && chown -R omnivision:omnivision /app
USER omnivision

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD python3 -c "import urllib.request; assert urllib.request.urlopen('http://localhost:8000/api/v1/health').status == 200"

# Run from project root
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
