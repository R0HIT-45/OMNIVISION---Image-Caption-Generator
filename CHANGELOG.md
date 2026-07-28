# Changelog

All notable changes to OmniVision will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [1.0.0] - 2026-07-26

### Added

- **Visual RAG Pipeline** — CLIP embedding + FAISS vector retrieval for context-aware caption grounding
- **Confidence Gate** — Similarity threshold mechanism to prevent AI hallucination by skipping grounding when confidence is low
- **ModelManager Singleton** — Thread-safe lazy loading with GPU memory swapping for BLIP, CLIP, IndicTrans2, and XTTS
- **Deployment Profiles** — `development` (BLIP Base), `demo` (BLIP-2 4-bit), `production` profiles for model selection via environment
- **Enterprise FastAPI Backend** — Service-oriented architecture with orchestrator pattern, custom exception hierarchy, and structured JSON logging
- **Explainability Dashboard** — Streamlit UI showing raw caption, retrieved knowledge, confidence score, grounding decision, and per-stage timing
- **Multilingual Translation** — IndicTrans2 integration for Hindi and Telugu translation
- **Text-to-Speech** — XTTS v2 integration for multilingual audio narration
- **Knowledge Pack Builder** — CLI tool to generate FAISS vector indices from JSON fact collections
- **Request ID Correlation** — UUID-based request tracking across all pipeline stages
- **Structured JSON Logging** — Machine-readable logs with request_id, pipeline_stage, latency, and success fields
- **Startup Configuration Validation** — Fast-fail on invalid profile, missing CUDA, missing knowledge packs, or invalid thresholds
- **Health Endpoint** — System status including GPU info, CUDA availability, knowledge pack status, and model configuration
- **Docker Support** — GPU-enabled Docker Compose setup with NVIDIA runtime passthrough
- **Comprehensive Test Suite** — 14 tests covering API endpoints, Confidence Gate logic, pipeline ordering, and graceful degradation

### Changed

- Unified enterprise backend as the sole backend (archived Phase 1 and Phase 2 simple backends)
- All imports use `backend.app.` namespace for project-root execution
- Health endpoint returns detailed system status instead of minimal ping
- Services accept `request_id` parameter for correlated logging

### Fixed

- HTTP 415 returned for unsupported MIME types (was incorrectly 500)
- Dynamic model name logging based on active deployment profile
- FAISS knowledge pack validation on startup (fails fast if missing)
- CLIP `get_text_features`/`get_image_features` return type compatibility with transformers 5.x
- Build script CLIP embedding extraction (BaseModelOutputWithPooling handling)
- Logging module import (`logging.config.dictConfig`)
- TTS graceful fallback when speaker reference WAV is missing
