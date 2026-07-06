# 08_API_SPECIFICATION.md
Version 1.0
Status: LOCKED

## 1. Introduction
This document defines the RESTful API contracts for the OmniVision backend. The API is built with FastAPI, strictly adhering to OpenAPI 3.0 standards. It handles all multipart image uploads and returns structured JSON responses.

## 2. Base URL & Authentication
- **Base URL**: `http://localhost:8000/api/v1`
- **Authentication**: None for v1.0. (JWT Bearer Token reserved for v2.0).

## 3. Endpoints

### 3.1 Health Check
**Endpoint:** `GET /health`
**Description:** Verifies that the FastAPI server is running and the orchestrator is ready.
**Response (200 OK):**
```json
{
  "status": "online",
  "version": "1.0",
  "timestamp": "2026-07-06T12:00:00Z"
}
```

### 3.2 Process Image (Full Pipeline)
**Endpoint:** `POST /process-image`
**Description:** Uploads an image, runs the full AI inference pipeline (Caption, Embedding, Retrieval, Grounding, Translation, TTS), and returns the complete result object.

**Request Form-Data:**
- `file`: (Binary) The image file (`.jpg`, `.jpeg`, `.png`). Max 10MB.

**Response (200 OK):**
```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "success",
  "data": {
    "raw_caption": "A stone structure with pillars.",
    "final_caption": "A stone structure with pillars. Specifically, this is the Sanchi Stupa, an ancient Buddhist complex.",
    "translations": {
      "hindi": "स्तंभों वाली एक पत्थर की संरचना। विशेष रूप से, यह सांची स्तूप है...",
      "telugu": "స్తంభాలతో ఉన్న రాతి నిర్మాణం..."
    },
    "audio_urls": {
      "english": "/static/audio/550e8400_en.wav",
      "hindi": "/static/audio/550e8400_hi.wav",
      "telugu": "/static/audio/550e8400_te.wav"
    }
  },
  "explainability": {
    "top_retrieved_entity": "Sanchi Stupa",
    "similarity_score": 0.82,
    "threshold_used": 0.75,
    "grounding_applied": true
  },
  "metadata": {
    "processing_time_seconds": 12.4,
    "models_used": ["BLIP-2", "CLIP", "IndicTrans2", "XTTS-v2"]
  }
}
```

**Response (422 Unprocessable Entity):**
Triggered if the uploaded file is not an image or exceeds size limits.
```json
{
  "error": "Validation Error",
  "message": "Invalid file format. Only JPG and PNG are supported."
}
```

**Response (500 Internal Server Error):**
Triggered if a critical AI model (e.g., BLIP) fails to load or infer.
```json
{
  "error": "CaptionGenerationError",
  "message": "Failed to generate visual caption due to GPU memory limit."
}
```

### 3.3 Text-to-Speech (Standalone Utility)
**Endpoint:** `POST /tts`
**Description:** Converts arbitrary text to speech. Used for UI interaction feedback or independent testing.
**Request Body (application/json):**
```json
{
  "text": "Hello, welcome to OmniVision.",
  "language": "english"
}
```
**Response (200 OK):**
```json
{
  "audio_url": "/static/audio/abc123_en.wav"
}
```

## 4. Error Handling Schema
All errors adhere to a standardized schema structure to allow the frontend to gracefully parse and display warnings.
```json
{
  "error": "ExceptionClassName",
  "message": "Human readable message describing the failure."
}
```

## 5. Static File Serving
The backend mounts a static directory to serve generated audio files to the frontend.
**Endpoint:** `GET /static/audio/{filename}`
**Description:** Returns the `.wav` binary file.
