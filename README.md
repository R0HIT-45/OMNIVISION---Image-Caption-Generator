# OmniVision

[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-00a393.svg)](https://fastapi.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**OmniVision** is an enterprise-grade AI Image Caption Generator with Visual Retrieval-Augmented Generation (RAG) for context-aware caption grounding.

Unlike standard captioning models that generate generic descriptions ("A tall building"), OmniVision uses CLIP + FAISS to ground its vision in factual knowledge ("The Charminar, an iconic monument in Hyderabad"). Includes multilingual translation (Hindi, Telugu) and text-to-speech narration.

## Features

- **Visual RAG** -- CLIP embedding + FAISS vector retrieval for context-aware grounding
- **Confidence Gate** -- Cosine similarity threshold to prevent AI hallucination
- **Multilingual Translation** -- IndicTrans2 for Hindi and Telugu
- **Text-to-Speech** -- XTTS v2 for multilingual audio narration
- **ModelManager** -- Thread-safe lazy loading with GPU memory swapping (runs on 4GB RTX 3050)
- **Deployment Profiles** -- `development` / `demo` / `production` for model selection
- **Explainability Dashboard** -- Shows raw caption, retrieved fact, confidence score, and per-stage timing
- **Structured JSON Logging** -- Request ID correlation across all pipeline stages

## Architecture

```
Image Upload
    |
    v
Image Validation
    |
    v
BLIP Caption  ---------> Raw Caption
    |
    v
CLIP Embedding
    |
    v
FAISS Retrieval -------> Knowledge Pack
    |
    v
Confidence Gate
    |                    |
    | score >= 0.75      | score < 0.75
    v                    v
Grounding Applied       Raw Caption Only
    |                    |
    v                    v
Translation (Hindi/Telugu)
    |
    v
Text-to-Speech
    |
    v
Explainability Dashboard
```

## Folder Structure

```
OmniVision/
├── backend/app/              # Enterprise FastAPI backend
│   ├── config/               # Settings, logging, startup validation
│   ├── exceptions/           # Custom exception hierarchy (400/415/500/503)
│   ├── managers/             # ModelManager singleton (VRAM swapping)
│   ├── middleware/            # Request logging middleware
│   ├── models/               # Model registry & base interfaces
│   ├── orchestrator/         # RequestCoordinator, ResponseBuilder & FrontendTransformer
│   ├── routes/               # API v1 endpoints (domain + frontend-compatible)
│   ├── schemas/              # Pydantic request/response models
│   └── services/             # Single-responsibility AI services
├── frontend/                 # React + TanStack Router + Tailwind frontend
├── knowledge_base/           # FAISS indices & JSON manifests
├── scripts/                  # Knowledge pack builder CLI
├── tests/                    # Enterprise test suite
├── docs/                     # 21-document enterprise design suite
├── archive/                  # Archived Phase 2 legacy backend
├── static/                   # Ephemeral audio & uploads
├── requirements-base.txt     # CPU-compatible dependencies
├── requirements-cuda.txt     # CUDA installation guide
├── Dockerfile                # GPU-enabled backend container
└── docker-compose.yml        # Full-stack deployment
```

## Installation

### Prerequisites
- Python 3.11+
- Node.js 20+ (for frontend)
- NVIDIA GPU (4GB+ VRAM) with CUDA 11.8+ (for demo/production profiles)

### Backend Setup
```bash
# 1. Clone the repository
git clone https://github.com/yourusername/OmniVision.git
cd OmniVision

# 2. Create virtual environment
python -m venv venv
# Windows: venv\Scripts\activate
# Linux/Mac: source venv/bin/activate

# 3. Install CUDA-enabled PyTorch
pip install torch==2.1.2+cu118 torchvision==0.16.2+cu118 torchaudio==2.1.2+cu118 --index-url https://download.pytorch.org/whl/cu118

# 4. Install remaining dependencies
pip install -r requirements-base.txt

# 5. Copy and configure environment
copy .env.example .env
```

### Frontend Setup
```bash
cd frontend
bun install    # or npm install
bun run dev    # or npm run dev
```

### Build Knowledge Pack
```bash
python scripts/build_knowledge_pack.py --pack heritage_pack --json sample_facts.json
```

### Start Backend
```bash
# Windows
.\run_backend.ps1

# Or manually
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

API docs at `http://localhost:8000/docs`

### Start Frontend
```bash
cd frontend
bun run dev
```

App at `http://localhost:3000`

### Docker
```bash
docker-compose up --build
```

## Testing
```bash
pytest tests/ -v
```

## Deployment Profiles

| Profile | Caption Model | VRAM | Use Case |
|---------|--------------|------|----------|
| `development` | BLIP Base | ~900 MB | CPU-friendly development |
| `demo` | BLIP-2 4-bit | ~1.8 GB | Interview demos (CUDA required) |
| `production` | BLIP-2 4-bit | ~1.8 GB | Production deployment |

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React, TanStack Router, Tailwind CSS, shadcn/ui |
| Backend | FastAPI |
| Vision | BLIP / BLIP-2 |
| Embedding | CLIP |
| Vector DB | FAISS |
| Translation | IndicTrans2 |
| TTS | Coqui XTTS-v2 |
| Deployment | Docker + NVIDIA |

## License

MIT License.

## Contributors

Developed by [Your Name]. Architecture and engineering reviewed to enterprise standards.
