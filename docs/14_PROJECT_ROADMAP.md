# 14_PROJECT_ROADMAP.md
Version 1.0
Status: LOCKED

## 1. Introduction
This roadmap outlines the evolution of OmniVision from an academic Minimum Viable Product (MVP) to a scalable, cloud-native enterprise application.

## 2. Version 1.0 (Current MVP)
**Focus**: Core Pipeline & Accessibility
- [x] BLIP-2 Caption Generation
- [x] CLIP + FAISS Knowledge Grounding
- [x] Confidence Gate mechanism
- [x] IndicTrans2 Translation (Hindi, Telugu)
- [x] XTTS Audio Narration
- [x] FastAPI Backend & Streamlit Frontend
- [x] VRAM Memory Swapping Algorithm
- [x] Explainability Dashboard

## 3. Version 1.5
**Focus**: Performance & Expanded Reach
- **Additional Languages**: Integrate Tamil, Kannada, and Malayalam translations.
- **Model Upgrades**: Evaluate replacing BLIP-2 with Florence-2 for faster, more accurate visual parsing.
- **Advanced Caching**: Implement Redis to cache translation and TTS outputs for frequently uploaded images to bypass expensive GPU inference.
- **Streaming UI**: Implement WebSocket or Server-Sent Events (SSE) so the Streamlit UI updates in real-time as each pipeline stage completes, rather than waiting for the entire payload.

## 4. Version 2.0
**Focus**: Persistence & User Management
- **Database Integration**: Implement the PostgreSQL schemas outlined in `09_DATABASE_ARCHITECTURE.md`.
- **User Authentication**: Add JWT-based login, allowing users to save their caption history.
- **Analytics Dashboard**: Admins can view metrics on how often the Confidence Gate accepts or rejects grounding.
- **Cloud Vector DB**: Migrate from local FAISS to Pinecone or Qdrant for managing massive Knowledge Packs.

## 5. Version 3.0
**Focus**: Advanced Multimodal Capabilities
- **Video Captioning**: Frame sampling and temporal logic to narrate short video clips.
- **OCR Integration**: Detect text within the image and integrate it into the caption automatically.
- **Visual Question Answering (VQA)**: Allow the user to ask specific questions about the uploaded image in a chat interface.

## 6. Future Research Directions
- **Edge Deployment**: Compiling the models using ONNX or TensorRT to deploy OmniVision on mobile devices or edge hardware (like NVIDIA Jetson) for visually impaired users without internet dependency.
- **Self-Refining Captions**: Using a lightweight local LLM (like Llama-3-8B) as a final critic to review and polish the grounded caption before translation.
