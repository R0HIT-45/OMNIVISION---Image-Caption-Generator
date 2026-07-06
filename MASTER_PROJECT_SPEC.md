# OmniVision — Master Project Specification

> **Single source of truth** for implementation, documentation, reviews, and placement interviews.  
> **Version:** 1.0 | **Status:** Approved for Phase-wise Implementation

---

## 1. Project Identity

| Field | Value |
|-------|-------|
| **Title** | OmniVision: A Production-Ready Multilingual Image Captioning and Audio Narration Platform Using BLIP-2 |
| **Type** | AI Product Engineering Project (deployment-focused, not model-training) |
| **Domain** | Computer Vision, NLP, Machine Translation, Speech Synthesis, Accessibility AI |
| **Prepared By** | Vinayak (B.Tech, CSE) |
| **Target Hardware** | HP Victus 15 — RTX 3050 (4GB VRAM), Intel i5 |

---

## 2. Project Vision

OmniVision is **not** a basic "Image → Caption" college mini-project.

It is a **Vision → Language → Speech** accessibility platform that:

1. Understands image content using BLIP-2
2. Generates **short** and **detailed** captions
3. Translates captions into **Hindi** and **Telugu** (IndicTrans2)
4. Converts text into **audio narration** (Coqui XTTS-v2)
5. Delivers everything through a **production-ready web application**

### Core Contribution (Interview-Safe Statement)

> *"OmniVision extends a state-of-the-art vision-language model into a multilingual accessibility platform by integrating adaptive caption generation, regional language translation, and real-time audio narration within a unified, optimized deployment framework."*

**Do NOT claim:** custom BLIP-2 training, research breakthroughs, or invented algorithms.  
**Do claim:** system engineering, quantization, staged inference, modular architecture, accessibility integration.

---

## 3. Problem Statement

Digital platforms contain billions of images, but machines struggle to describe visual content in human language. Existing student-level captioning systems typically:

- Output **English-only** captions
- Provide **no audio** for visually impaired users
- Use **legacy CNN + LSTM** architectures (ResNet50 + LSTM on Flickr8k)
- Depend on **cloud APIs** (cost, latency, internet dependency)
- Stop at model training without **deployment** or **product thinking**

OmniVision addresses these gaps with an offline-first, accessibility-oriented, multilingual AI product.

---

## 4. Objectives

### Primary Objectives

| ID | Objective |
|----|-----------|
| O-1 | Generate accurate image captions using pretrained BLIP-2 |
| O-2 | Provide **Short Caption** and **Detailed Description** modes |
| O-3 | Translate captions into **Hindi** and **Telugu** |
| O-4 | Generate **real-time audio narration** |
| O-5 | Build a user-friendly web interface (Streamlit + FastAPI) |
| O-6 | Optimize inference for **RTX 3050 (4GB VRAM)** |

### Secondary Objectives

- Improve accessibility for visually impaired users
- Enable offline execution after initial model download
- Demonstrate modern AI deployment (MLOps mindset)
- Support future PostgreSQL history and analytics (v2.0)

---

## 5. Functional Requirements

| ID | Requirement | Details |
|----|-------------|---------|
| FR-1 | Image Upload | JPG, JPEG, PNG via web UI; max 10 MB |
| FR-2 | Short Caption | Concise identification caption |
| FR-3 | Detailed Caption | Rich scene description with actions, objects, context |
| FR-4 | Translation | English → Hindi, English → Telugu |
| FR-5 | Audio Narration | TTS output for selected language |
| FR-6 | Results Display | Image, captions, translations, audio player |
| FR-7 | API Communication | Streamlit ↔ FastAPI over HTTP |
| FR-8 | History (v2.0) | Store captions, translations, audio in PostgreSQL |
| FR-9 | Download (v2.0) | Download caption text and audio files |

### Caption Mode Examples

**Short:** `A boy playing football.`

**Detailed:** `A young boy wearing a blue jersey is playing football on a grassy field while spectators watch from the sidelines.`

---

## 6. Non-Functional Requirements

| Category | Requirement |
|----------|-------------|
| **Performance** | End-to-end pipeline < 10–15 seconds per image on RTX 3050 |
| **Scalability** | Modular services; future cloud/Docker deployment |
| **Reliability** | Graceful handling of invalid images and model errors |
| **Usability** | Beginner-friendly UI; clear output sections |
| **Maintainability** | Independent AI modules; swappable models |
| **Accessibility** | Audio narration for visually impaired users |
| **Security** | File type validation; input sanitization; bcrypt for auth (v2.0) |
| **Offline** | No paid cloud APIs; local inference after model download |

---

## 7. Technology Stack

### Locked Decisions

| Layer | Technology | Model / Package |
|-------|------------|-----------------|
| Vision-Language | BLIP-2 | `Salesforce/blip2-opt-2.7b` |
| Quantization | bitsandbytes | 4-bit via `BitsAndBytesConfig` |
| Translation | IndicTrans2 | `ai4bharat/indictrans2-en-indic-dist-200M` |
| Text-to-Speech | Coqui TTS | `tts_models/multilingual/multi-dataset/xtts_v2` |
| Backend | FastAPI + Uvicorn | Async endpoints |
| Frontend | Streamlit | Interactive dashboard |
| ML Framework | PyTorch | CUDA inference |
| Model Hub | Hugging Face | transformers, accelerate |
| Database (v2.0) | PostgreSQL | SQLAlchemy ORM |
| Containerization | Docker | Multi-stage build |
| Language | Python 3.10+ | — |
| IDE | VS Code | — |

### Why Each Choice (Interview Answers)

| Component | Justification |
|-----------|---------------|
| **BLIP-2** | State-of-the-art VLM; Q-Former bridges vision encoder + LLM; zero-shot captioning without custom training |
| **4-bit Quantization** | BLIP-2 FP16 needs ~5.5GB VRAM; 4-bit reduces to ~1.8GB on RTX 3050 |
| **IndicTrans2** | Open-source, offline, research-grade Indian language MT (AI4Bharat) |
| **Coqui XTTS-v2** | Open-source neural TTS; multilingual; runs locally |
| **FastAPI** | Async request handling; non-blocking during long inference |
| **Streamlit** | Rapid UI; separates presentation from inference layer |
| **PostgreSQL** | Production-grade; supports history, auth, analytics (v2.0) |
| **Docker** | Reproducible deployment; portfolio-ready |

---

## 8. System Architecture

### High-Level Flow

```
User Uploads Image
        │
        ▼
┌───────────────────┐
│  Streamlit UI     │
└─────────┬─────────┘
          │ HTTP
          ▼
┌───────────────────┐
│  FastAPI Backend  │
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│  BLIP-2 (4-bit)   │
│  Caption Gen      │
└─────────┬─────────┘
          │
    ┌─────┴─────┐
    ▼           ▼
 Short      Detailed
 Caption    Caption
    │           │
    └─────┬─────┘
          ▼
┌───────────────────┐
│   IndicTrans2     │
└─────────┬─────────┘
          │
    ┌─────┼─────┐
    ▼     ▼     ▼
  EN    HI    TE
    │     │     │
    └─────┼─────┘
          ▼
┌───────────────────┐
│  Coqui XTTS-v2    │
└─────────┬─────────┘
          ▼
   Audio Narration
          │
          ▼
   Streamlit Display
```

### Staged Inference (Critical for 4GB VRAM)

**Do NOT load all models simultaneously.**

```
BLIP-2 Inference
      ↓
Release GPU Memory (del model, torch.cuda.empty_cache())
      ↓
IndicTrans2 Translation
      ↓
Release GPU Memory
      ↓
XTTS-v2 Audio Generation
      ↓
Release GPU Memory
```

**Interview line:** *"We use staged inference — each model is loaded, executed, and memory-cleaned before the next stage to prevent VRAM exhaustion on consumer hardware."*

### Memory Budget (RTX 3050)

| Component | Approx. VRAM |
|-----------|--------------|
| BLIP-2 (4-bit) | ~1.8 GB |
| IndicTrans2 (distilled) | ~400 MB |
| XTTS-v2 | ~1–2 GB (varies) |
| **Strategy** | Sequential loading, never concurrent |

---

## 9. Folder Structure

```
OmniVision/
│
├── backend/
│   ├── main.py                    # FastAPI app entry
│   ├── routes/
│   │   ├── caption.py             # POST /caption, /process-image
│   │   ├── translate.py           # POST /translate
│   │   └── tts.py                 # POST /tts
│   ├── services/
│   │   ├── blip_service.py        # BLIP-2 load + caption generation
│   │   ├── translation_service.py # IndicTrans2
│   │   └── speech_service.py      # Coqui XTTS-v2
│   ├── models/
│   │   └── schemas.py             # Pydantic request/response models
│   └── utils/
│       ├── image_utils.py         # Validation, preprocessing
│       ├── memory_utils.py        # GPU cleanup helpers
│       └── config.py              # Env vars, paths, model names
│
├── frontend/
│   └── app.py                     # Streamlit dashboard
│
├── database/
│   ├── models.py                  # SQLAlchemy models (v2.0)
│   └── connection.py              # DB session (v2.0)
│
├── static/
│   ├── uploads/                   # Temporary uploaded images
│   └── audio/                     # Generated audio files
│
├── tests/
│   ├── test_caption.py
│   ├── test_translation.py
│   └── test_api.py
│
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
│
├── docs/
│   ├── SRS.md
│   ├── HLD.md
│   └── architecture.png
│
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## 10. API Design

### Endpoints

| Method | Endpoint | Purpose | Request | Response |
|--------|----------|---------|---------|----------|
| GET | `/health` | Health check | — | `{ "status": "ok" }` |
| POST | `/caption` | Generate captions | `file: UploadFile` | `{ short_caption, detailed_caption }` |
| POST | `/translate` | Translate text | `{ text, target_lang }` | `{ translated_text }` |
| POST | `/tts` | Generate audio | `{ text, language }` | `{ audio_path }` |
| POST | `/process-image` | Full pipeline | `file: UploadFile` | Full result object |
| GET | `/history` | Caption history (v2.0) | — | List of past results |

### `/process-image` Response Schema

```json
{
  "image_id": "uuid",
  "short_caption": "A dog running on grass.",
  "detailed_caption": "A medium-sized brown dog is running...",
  "translations": {
    "hindi": "एक कुत्ता घास पर दौड़ रहा है।",
    "telugu": "ఒక కుక్క గడ్డిపై పరుగెత్తుతోంది."
  },
  "audio": {
    "english": "/static/audio/en_uuid.wav",
    "hindi": "/static/audio/hi_uuid.wav",
    "telugu": "/static/audio/te_uuid.wav"
  },
  "processing_time_seconds": 8.4
}
```

### BLIP-2 Prompt Strategy

| Mode | Prompt Template |
|------|-----------------|
| Short | `"a photo of"` or unconditional generation, `max_new_tokens=20` |
| Detailed | `"Describe this image in detail:"` , `max_new_tokens=80` |

---

## 11. Database Design (v2.0)

> **v1.0 MVP:** Local file storage only. **v2.0:** PostgreSQL.

### ERD

```
Users ──< Images ──< Captions ──< Translations
                            └──< AudioFiles

Users ──< ActivityLogs
```

### Tables

```sql
-- Users
CREATE TABLE users (
    user_id UUID PRIMARY KEY,
    username VARCHAR(100),
    email VARCHAR(150) UNIQUE,
    password_hash TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP
);

-- Images
CREATE TABLE images (
    image_id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(user_id),
    image_name VARCHAR(255),
    image_path TEXT,
    upload_time TIMESTAMP DEFAULT NOW()
);

-- Captions
CREATE TABLE captions (
    caption_id UUID PRIMARY KEY,
    image_id UUID REFERENCES images(image_id),
    short_caption TEXT,
    detailed_caption TEXT,
    generated_at TIMESTAMP DEFAULT NOW()
);

-- Translations
CREATE TABLE translations (
    translation_id UUID PRIMARY KEY,
    caption_id UUID REFERENCES captions(caption_id),
    language VARCHAR(50),
    translated_text TEXT,
    generated_at TIMESTAMP DEFAULT NOW()
);

-- Audio Files
CREATE TABLE audio_files (
    audio_id UUID PRIMARY KEY,
    caption_id UUID REFERENCES captions(caption_id),
    language VARCHAR(50),
    audio_path TEXT,
    generated_at TIMESTAMP DEFAULT NOW()
);

-- Activity Logs
CREATE TABLE activity_logs (
    log_id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(user_id),
    action VARCHAR(255),
    timestamp TIMESTAMP DEFAULT NOW()
);
```

### Indexes

```sql
CREATE INDEX idx_user_email ON users(email);
CREATE INDEX idx_user_images ON images(user_id);
CREATE INDEX idx_caption_image ON captions(image_id);
CREATE INDEX idx_translation_caption ON translations(caption_id);
```

---

## 12. Development Roadmap

### Phase 1 — Project Setup + BLIP-2 MVP
- [ ] Folder structure, virtual env, `requirements.txt`
- [ ] `blip_service.py` with 4-bit quantization
- [ ] FastAPI `/caption` endpoint
- [ ] Streamlit upload → display caption
- **Deliverable:** Working image → English caption

### Phase 2 — Dual Caption Modes
- [ ] Short + Detailed prompt engineering
- [ ] Update API response schema
- [ ] Streamlit UI sections for both modes
- **Deliverable:** Two caption styles from same image

### Phase 3 — IndicTrans2 Translation
- [ ] `translation_service.py`
- [ ] Hindi + Telugu endpoints
- [ ] Integrate into `/process-image`
- [ ] Staged GPU memory management
- **Deliverable:** Multilingual captions

### Phase 4 — Coqui XTTS-v2 Audio
- [ ] `speech_service.py`
- [ ] Audio file generation + playback in Streamlit
- [ ] Staged inference after translation
- **Deliverable:** Full Vision → Language → Speech pipeline

### Phase 5 — Full Pipeline + Polish
- [ ] `POST /process-image` orchestration
- [ ] Error handling, logging, loading spinners
- [ ] `memory_utils.py` for GPU cleanup
- **Deliverable:** End-to-end product

### Phase 6 — PostgreSQL Integration (v2.0)
- [ ] SQLAlchemy models, migrations
- [ ] History endpoint
- [ ] Optional user auth (JWT)
- **Deliverable:** Persistent caption history

### Phase 7 — Docker + Deployment
- [ ] Dockerfile, docker-compose
- [ ] `.env` configuration
- [ ] README with run instructions
- **Deliverable:** Containerized deployment

### Phase 8 — Optimization + Documentation
- [ ] Response caching for repeated translations
- [ ] Performance benchmarking
- [ ] Architecture diagram, project report, PPT
- **Deliverable:** Submission + placement package

---

## 13. Implementation Rules (For Cursor / Developers)

1. **Production-ready code** — no placeholders, no `TODO` stubs in committed code
2. **Phase-by-phase** — complete and verify each phase before next
3. **Logging** — use Python `logging` module in all services
4. **Exception handling** — wrap model inference in try/except with meaningful HTTP errors
5. **Memory management** — always call GPU cleanup between model stages
6. **Tests** — add unit tests per phase in `tests/`
7. **requirements.txt** — update after each phase with pinned versions
8. **No false claims** — code comments and docs must say "pretrained inference", not "trained"
9. **Stop after each phase** — explain code, wait for approval

---

## 14. Dependencies (requirements.txt baseline)

```
torch>=2.0.0
torchvision
torchaudio
transformers>=4.36.0
accelerate
bitsandbytes
fastapi
uvicorn[standard]
python-multipart
streamlit
requests
pillow
sentencepiece
TTS
sqlalchemy
psycopg2-binary
python-dotenv
pydantic
pydantic-settings
```

---

## 15. Environment Variables (.env.example)

```env
# API
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8000
STREAMLIT_PORT=8501

# Models
BLIP2_MODEL=Salesforce/blip2-opt-2.7b
INDICTRANS_MODEL=ai4bharat/indictrans2-en-indic-dist-200M
TTS_MODEL=tts_models/multilingual/multi-dataset/xtts_v2

# Paths
UPLOAD_DIR=static/uploads
AUDIO_DIR=static/audio

# Database (v2.0)
DATABASE_URL=postgresql://user:password@localhost:5432/omnivision

# Limits
MAX_UPLOAD_SIZE_MB=10
```

---

## 16. Deployment Strategy

### Development (Local)

```bash
# Terminal 1 — Backend
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 — Frontend
streamlit run frontend/app.py --server.port 8501
```

### Production (Docker)

```bash
docker-compose up --build
```

### Future Cloud

```
Nginx Reverse Proxy → FastAPI → Model Services
                  → Streamlit
                  → PostgreSQL
```

---

## 17. Testing Strategy

| Test Type | Scope |
|-----------|-------|
| Unit | `blip_service`, `translation_service`, `speech_service` |
| API | FastAPI endpoints with TestClient |
| Integration | Full `/process-image` pipeline |
| Manual | Upload diverse images; verify captions, translations, audio |
| Performance | Measure end-to-end latency on RTX 3050 |

### Success Criteria

- [ ] Image upload works (JPG, PNG, JPEG)
- [ ] BLIP-2 generates meaningful short + detailed captions
- [ ] Hindi and Telugu translations are readable
- [ ] Audio narration plays in Streamlit
- [ ] Pipeline completes without OOM on RTX 3050
- [ ] Invalid files rejected gracefully

---

## 18. Security Design

| Measure | Implementation |
|---------|----------------|
| File validation | Allow only `.jpg`, `.jpeg`, `.png` |
| Size limit | 10 MB max upload |
| Input sanitization | Validate all API request bodies via Pydantic |
| SQL injection | SQLAlchemy ORM (no raw SQL) |
| Password storage | bcrypt hashing (v2.0 auth) |
| Auth | JWT tokens (v2.0) |

---

## 19. Risks and Mitigation

| Risk | Mitigation |
|------|------------|
| GPU OOM | 4-bit quantization + staged inference |
| Slow inference | Distilled IndicTrans2; lazy model loading |
| XTTS memory heavy | Load TTS only after releasing BLIP-2 + IndicTrans2 |
| Model download size | Document one-time Hugging Face download |
| Translation quality | Use detailed caption as source for richer translations |

---

## 20. Future Scope

- Additional Indian languages (Tamil, Kannada, Malayalam)
- Real-time camera captioning
- Video caption generation
- OCR integration for text-in-image
- Mobile app (React Native / Flutter)
- Voice command interaction
- Cloud deployment (AWS/GCP)
- User authentication + caption history dashboard
- Scene object parsing panel (objects detected list)
- Explainable AI (why this caption)

---

## 21. Abstract (Final — For Report / IEEE Paper)

The rapid growth of digital media has led to an unprecedented increase in visual data across social platforms, cloud systems, and enterprise applications. Although images contain rich semantic information, machines often struggle to interpret and describe visual content meaningfully. Traditional image captioning systems generate limited monolingual outputs and lack accessibility features and deployment readiness for real-world use.

This project presents **OmniVision**, a production-ready multilingual image captioning and audio narration platform built on the BLIP-2 vision-language model. The system generates both concise and detailed image descriptions, translates captions into Hindi and Telugu using IndicTrans2, and converts textual outputs into natural speech through Coqui XTTS-v2. A modular architecture using FastAPI and Streamlit enables scalable deployment with an intuitive user interface.

The primary contribution is a multilingual accessibility-focused framework that extends modern vision-language models through adaptive caption generation, regional language translation, and real-time audio narration within a unified deployment architecture. BLIP-2 inference is optimized using 4-bit quantization for execution on consumer-grade hardware (RTX 3050, 4GB VRAM). The platform demonstrates the practical convergence of Computer Vision, Natural Language Processing, Machine Translation, and Speech Synthesis into an inclusive, deployment-ready AI solution.

---

## 22. Resume Bullet Points

```
OmniVision — Multilingual Image Captioning & Audio Narration Platform
• Engineered an end-to-end Vision→Language→Speech pipeline using BLIP-2, IndicTrans2,
  and Coqui XTTS-v2 with FastAPI backend and Streamlit frontend
• Optimized BLIP-2 inference via 4-bit quantization and staged GPU memory management
  to run on RTX 3050 (4GB VRAM) consumer hardware
• Built multilingual accessibility features: dual caption modes, Hindi/Telugu translation,
  and neural text-to-speech narration for visually impaired users
• Designed modular microservice-style architecture with async FastAPI endpoints and
  Docker containerization for production deployment
```

---

## 23. Viva / Interview — Top 10 Questions

| Question | Answer |
|----------|--------|
| What is your contribution? | Built a multilingual accessibility platform integrating BLIP-2, IndicTrans2, and TTS in a production deployment framework |
| Why BLIP-2 over ResNet+LSTM? | BLIP-2 uses Q-Former + LLM for contextual reasoning; zero-shot; industry standard VLM |
| Did you train BLIP-2? | No. We use pretrained inference with prompt engineering and 4-bit quantization |
| How do you handle 4GB VRAM? | 4-bit quantization (~1.8GB) + staged inference with memory cleanup between models |
| Why IndicTrans2 over Google Translate? | Offline, free, open-source, research-grade Indian language support |
| Why FastAPI over Flask? | Native async support; non-blocking during long inference jobs |
| Why both Streamlit and FastAPI? | Separation of concerns: UI vs inference API; backend reusable for mobile/other frontends |
| What metrics would you use? | BLEU, METEOR, CIDEr, SPICE for captions; latency and user accessibility for product |
| What is staged inference? | Load model → infer → release GPU → load next model; prevents OOM |
| Future improvements? | More languages, video captioning, PostgreSQL history, cloud deployment |

---

## 24. Cursor Implementation Prompt

Copy this when starting implementation in Cursor:

```
Read MASTER_PROJECT_SPEC.md completely.

You are a Senior AI/ML Engineer.

Build OmniVision phase by phase as defined in Section 12 (Development Roadmap).

Rules:
- Production-ready code only (no placeholders)
- Follow folder structure in Section 9
- Implement staged GPU inference per Section 8
- Add logging and exception handling
- Update requirements.txt after each phase
- Add tests in tests/
- Stop after each phase, explain the code, and wait for approval

Start with Phase 1: Project Setup + BLIP-2 MVP.
```

---

## 25. Document Index

| Document | Location | Status |
|----------|----------|--------|
| Master Spec | `MASTER_PROJECT_SPEC.md` | ✅ This file |
| SRS | `docs/SRS.md` | To be generated |
| HLD | `docs/HLD.md` | To be generated |
| Project Report | `docs/PROJECT_REPORT.md` | To be generated |
| IEEE Paper | `docs/IEEE_PAPER.md` | To be generated |
| Architecture Diagram | `docs/architecture.png` | To be generated |

---

**OmniVision v1.0 — Approved for Implementation**  
*If Cursor stops mid-phase, resume from the exact phase number in Section 12.*
