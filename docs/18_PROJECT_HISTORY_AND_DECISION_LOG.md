# 18_PROJECT_HISTORY_AND_DECISION_LOG.md
Version 1.0
Status: LOCKED

## 1. Introduction
This document serves as the engineering diary for OmniVision. It records the architectural evolution, the alternatives considered, and the rationale behind major technical decisions. Documenting this ensures future maintainers understand *why* the system is built this way, preventing the recurrence of previously solved problems.

## 2. Architecture Evolution

### 2.1 The Academic Prototype (v0.1)
- **Initial Idea**: A simple Python script using `ResNet50` and an `LSTM` trained on the `Flickr8k` dataset to generate image captions.
- **Challenge**: The generated captions were extremely basic ("A dog running on grass") and completely ignorant of real-world entities. Training took days, and the result was far below modern standards.
- **Decision**: Abandon the CNN+LSTM approach. Pivot to using a pretrained Vision-Language Model (VLM) for state-of-the-art zero-shot reasoning.

### 2.2 The VLM Pivot (v0.5)
- **Selection**: Evaluated OpenAI CLIP (captioning variant), BLIP, and BLIP-2.
- **Decision**: Selected `Salesforce/blip2-opt-2.7b`. The Q-Former architecture provided incredible detail, and it was small enough to run locally.
- **Challenge**: Loading BLIP-2 in FP16 required ~5.5GB VRAM. It crashed instantly on the target RTX 3050 (4GB).
- **Resolution**: Implemented 4-bit quantization using `bitsandbytes`, reducing the VRAM footprint to ~1.8GB with negligible loss in caption quality.

### 2.3 The Hallucination Problem (v0.8)
- **Issue**: BLIP-2 is excellent at describing visual attributes but fails at factual identification. It would describe the Eiffel Tower as "A tall metal tower".
- **Attempt 1**: Fine-tune BLIP-2 on a dataset of monuments. Rejected due to immense compute costs and loss of generalization.
- **Attempt 2**: Visual RAG. Use CLIP to embed the image and search a FAISS index of historical facts.
- **Challenge**: FAISS always returns the *closest* match. If the user uploaded a picture of a generic bridge, FAISS would retrieve "The Golden Gate Bridge", forcing the AI to hallucinate.
- **Resolution**: Engineered the **Confidence Gate**. Grounding is only applied if the FAISS cosine similarity score exceeds `0.75`. This single decision transformed the project from a tech demo into a reliable product.

### 2.4 The Deployment Refactor (v1.0)
- **Initial State**: Everything ran in a single `app.py` Streamlit script. The UI froze for 15 seconds during inference.
- **Resolution**: Split the project into a microservice-inspired architecture. 
  - FastAPI handles the heavy backend Orchestration.
  - Streamlit acts purely as a thin presentation layer.
  - Implemented the `ModelManager` to swap models in and out of GPU VRAM dynamically.

## 3. Technology Selection Trade-offs

### 3.1 Vector Database: FAISS vs. Pinecone
- **Considered**: Pinecone (Cloud Vector DB).
- **Trade-off**: Pinecone is powerful but requires internet access and API keys, reducing the portability of the MVP.
- **Decision**: Used FAISS. It runs locally on the CPU, is blazing fast, and requires zero setup. Designed the `RetrievalService` with dependency injection so Pinecone can be easily swapped in for v2.0.

### 3.2 Translation: Google API vs. IndicTrans2
- **Considered**: Google Translate API.
- **Trade-off**: Google API is fast but has rate limits, costs money at scale, and requires internet.
- **Decision**: Selected `ai4bharat/indictrans2-en-indic-dist-200M`. It provides research-grade, offline translation for Indian languages. The distilled 200M model was chosen over the base model to save memory.

### 3.3 Text-to-Speech: Google gTTS vs. Coqui XTTS-v2
- **Considered**: `gTTS` (Google Text-to-Speech).
- **Trade-off**: `gTTS` is just an API wrapper, relying on the cloud. The voice sounds robotic.
- **Decision**: Selected `Coqui XTTS-v2`. It generates incredibly natural, human-like speech locally and supports multiple languages. 
- **Challenge**: XTTS is massive (~2GB VRAM). 
- **Resolution**: Forced the `ModelManager` to flush BLIP and CLIP from the GPU before loading XTTS.

## 4. Future Upgrade Path (The Next Challenge)
The most significant technical debt in v1.0 is the **VRAM Swapping Latency**. Moving 2GB models between system RAM and GPU VRAM takes 2-4 seconds, artificially inflating the pipeline latency. 

**Proposed v2.0 Solution**: 
When deployed to a cloud instance (e.g., AWS `g4dn.2xlarge` with an NVIDIA T4 16GB GPU), the `ModelManager` configuration will be toggled to `LAZY_UNLOAD = False`. All models (BLIP, CLIP, IndicTrans, XTTS) will be loaded simultaneously into VRAM and kept hot, dropping pipeline latency from ~15 seconds down to ~3 seconds.
