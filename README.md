# OmniVision 👁️

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100.0%2B-00a393.svg)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.25.0%2B-FF4B4B.svg)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**OmniVision** is an enterprise-grade AI Accessibility Platform designed to generate highly accurate, context-aware image captions using a Visual Retrieval-Augmented Generation (RAG) pipeline.

Unlike standard image captioning models that generate generic descriptions (e.g., "A tall building"), OmniVision uses CLIP and FAISS to ground its vision in historical facts (e.g., "The Charminar, an iconic monument in Hyderabad"). The platform includes Indic language translation and Text-to-Speech (TTS) narration, making it a comprehensive accessibility tool.

## 🌟 Project Vision & Problem Statement
Current generative models hallucinate when asked to identify specific factual entities from images, and retrieval models lack natural language reasoning. OmniVision solves this by marrying a frozen Vision-Language Model (BLIP-2) with an external vector database via a strict **Confidence Gate** algorithm.

## ✨ Features
- **Visual RAG**: Grounded image captioning using CLIP + FAISS.
- **Confidence Gate**: Strict cosine similarity thresholding to prevent AI hallucinations.
- **Multilingual Support**: Real-time translation to Hindi and Telugu using IndicTrans2.
- **Speech Synthesis**: Human-like audio narration using Coqui XTTS-v2.
- **VRAM Optimized**: Runs a massive multi-model pipeline on a 4GB RTX 3050 via dynamic memory swapping.
- **Explainable AI**: A transparent UI that shows exactly how the AI made its grounding decisions.

## 🏗️ Architecture
OmniVision is built using a decoupled Service-Oriented Architecture (SOA).

- **Frontend**: Streamlit (Presentation Layer & Explainability Dashboard)
- **Backend**: FastAPI (Async API Layer & AI Orchestration)
- **Model Registry**: Standardized interfaces for swapping AI models.

### Folder Structure
```text
OmniVision/
├── backend/app/
│   ├── config/          # Environment & settings
│   ├── exceptions/      # Custom error hierarchy
│   ├── managers/        # VRAM Model Swapping Singleton
│   ├── middleware/      # Structured JSON Logging
│   ├── models/          # Model Registry & Base Interfaces
│   ├── orchestrator/    # Request Coordinator & Pipeline
│   ├── routes/          # REST Endpoints
│   ├── schemas/         # Pydantic validation
│   └── services/        # Single-responsibility AI Services
├── frontend/            # Streamlit UI & Components
├── knowledge_base/      # FAISS indices and JSON manifests
├── scripts/             # Tooling for building FAISS packs
├── static/              # Ephemeral audio & uploads
└── docs/                # 18-Document Enterprise Design Suite
```

## 🚀 The Visual RAG Pipeline
1. **Vision**: BLIP-2 generates a raw visual description.
2. **Embedding**: CLIP generates a 512-dim embedding of the image.
3. **Retrieval**: FAISS searches the Knowledge Pack for the closest historical fact.
4. **Grounding**: If Similarity Score >= `0.75`, the fact is injected into the caption.
5. **Translation**: IndicTrans2 translates the final text.
6. **Audio**: XTTS-v2 synthesizes the speech.

## 💻 Installation

### Prerequisites
- Python 3.10+
- NVIDIA GPU (Minimum 4GB VRAM) with CUDA 11.8+ installed.

### Setup
```bash
# 1. Clone the repository
git clone https://github.com/yourusername/OmniVision.git
cd OmniVision

# 2. Create and activate a virtual environment
python -m venv venv
# Windows: venv\Scripts\activate
# Linux/Mac: source venv/bin/activate

# 3. Install PyTorch for your CUDA version (Example for CUDA 11.8)
pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# 4. Install remaining dependencies
pip install -r requirements.txt
```

## ⚙️ Running Locally

**1. Build the Sample Knowledge Pack:**
```bash
python scripts/build_knowledge_pack.py --pack heritage_pack --json sample_facts.json
```

**2. Start the FastAPI Backend:**
Open a new terminal and run:
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```
*API Docs available at `http://localhost:8000/docs`*

**3. Start the Streamlit Frontend:**
Open another terminal and run:
```bash
cd frontend
streamlit run app.py
```
*App available at `http://localhost:8501`*

## 🐳 Docker (Coming Soon)
Production deployment via Docker Compose with NVIDIA GPU passthrough is detailed in `docs/11_DEPLOYMENT_GUIDE.md`.

## 🔮 Future Scope (v2.0)
- Video Temporal Captioning (Frame sampling)
- OCR Integration
- Cloud Vector DB Migration (Pinecone/Qdrant)
- LLaVA / Qwen2.5-VL Model Upgrades via the Model Registry

## 📜 License
This project is licensed under the MIT License.

## 👥 Contributors
Developed by [Your Name]. Architecture and engineering blueprint reviewed by Principal AI Engineering standards.
