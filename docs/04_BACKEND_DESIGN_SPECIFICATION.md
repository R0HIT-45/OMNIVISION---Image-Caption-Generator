# 04_BACKEND_DESIGN_SPECIFICATION.md
Version 1.0
Status: LOCKED

## 1. Introduction
This document details the backend architecture for the OmniVision platform. It expands upon the logical design established in the `03_ENTERPRISE_SOFTWARE_ARCHITECTURE.md` blueprint. The backend is built using FastAPI, adopting a modular, service-oriented structure designed for high cohesion, lazy AI model loading, and asynchronous request orchestration.

## 2. FastAPI Architecture
The backend is structured as a RESTful API using FastAPI and Uvicorn. Unlike standard CRUD applications, OmniVision is an AI orchestration platform. The FastAPI layer acts strictly as a gateway: it validates requests and delegates them to the `AI Orchestrator`, ensuring that HTTP routing logic is completely decoupled from AI inference logic.

### 2.1 Key Characteristics
- **Asynchronous Execution**: The API layer uses `async def` for I/O bound operations (like file uploads and network responses) but offloads heavy AI inference to background threads or dedicated processes if needed, preventing the event loop from blocking.
- **Dependency Injection**: Used heavily for injecting configuration, database connections (future), and the Singleton ModelManager.
- **Pydantic Validation**: Every incoming request and outgoing response is strongly typed and validated via Pydantic models.

## 3. Folder Responsibilities

```text
backend/
├── app/
│   ├── main.py                 # FastAPI application factory and entry point
│   ├── routes/                 # HTTP endpoint definitions (routers)
│   │   ├── api_v1.py           # Main API router aggregating sub-routers
│   │   └── health.py           # Health check endpoints
│   ├── orchestrator/           # Request Coordinator and Workflow logic
│   │   ├── request_coordinator.py
│   │   └── response_builder.py # Standardizes output responses
│   ├── services/               # AI and business logic (Single Responsibility)
│   │   ├── image_service.py
│   │   ├── caption_service.py
│   │   ├── embedding_service.py
│   │   ├── retrieval_service.py
│   │   ├── grounding_service.py
│   │   ├── translation_service.py
│   │   └── tts_service.py
│   ├── managers/               # Resource managers
│   │   └── model_manager.py    # Singleton model lifecycle manager
│   ├── models/                 # ORM Models (Future DB integration)
│   ├── schemas/                # Pydantic schemas (Request/Response)
│   ├── config/                 # Environment and app configuration
│   │   └── settings.py
│   ├── utils/                  # Shared utilities
│   │   ├── memory_utils.py     # GPU/CPU memory cleanup
│   │   └── file_utils.py       # File handling
│   ├── middleware/             # Request interceptors (CORS, Logging)
│   └── exceptions/             # Custom exception hierarchy and handlers
├── tests/                      # Pytest test suite
└── requirements.txt            # Python dependencies
```

## 4. Dependency Injection
FastAPI's dependency injection system is utilized to manage the lifecycle of core components.
- **Config Injection**: `get_settings()` injects the validated configuration object.
- **ModelManager Injection**: `get_model_manager()` injects the Singleton instance of the ModelManager, ensuring models are not redundantly loaded across different requests.

```python
# Example of Dependency Injection in a Route
@router.post("/process-image", response_model=OmniVisionResponse)
async def process_image_route(
    file: UploadFile = File(...),
    orchestrator: RequestCoordinator = Depends(get_orchestrator)
):
    return await orchestrator.process(file)
```

## 5. Request Lifecycle
When a client submits an image to `/api/v1/process`, the request undergoes a strict lifecycle:

1. **Middleware Interception**: The `RequestLoggingMiddleware` assigns a UUID to the request and logs the start time.
2. **Route Validation**: FastAPI validates the multipart form-data via Pydantic.
3. **Orchestrator Hand-off**: The route passes the `UploadFile` to the `RequestCoordinator`.
4. **Service Execution**: The Orchestrator sequentially (and conditionally) invokes the Services (Image → Caption & Embedding → Retrieval → Grounding → Translation → TTS).
5. **Response Building**: The `ResponseBuilder` takes the Orchestrator's internal `ProcessingContext` and formats it into the standard `OmniVisionResponse`.
6. **Middleware Exit**: The logging middleware records the total processing time and response status.

## 6. Singleton ModelManager
The `ModelManager` is the most critical infrastructure component for maintaining stability on constrained hardware (e.g., 4GB VRAM).

### 6.1 Design Pattern
Implemented as a strict Singleton. The application initializes it once at startup.
```python
class ModelManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelManager, cls).__new__(cls)
            cls._instance.loaded_models = {}
        return cls._instance
```

### 6.2 Lazy Loading and GPU Swapping
Models are loaded into memory *only* when requested by a service. If the Orchestrator calls `tts_service`, the `ModelManager` checks if `XTTS` is loaded. If VRAM is full, it dynamically unloads `BLIP` and `CLIP`, runs `torch.cuda.empty_cache()`, and then loads `XTTS`.

## 7. Exception Hierarchy
To ensure Graceful Degradation (Architecture Principle 4.5), OmniVision uses a custom exception hierarchy.

- `OmniVisionBaseException`: Base class.
- `CriticalAIException`: (e.g., `CaptionGenerationError`). Halts the request, returns HTTP 500.
- `NonCriticalAIException`: (e.g., `TranslationTimeoutError`). Caught by the Orchestrator. The field is set to `null` or a warning is added, and the request proceeds to the next stage.
- `ValidationException`: Returns HTTP 422.

The `exceptions/handlers.py` maps these to standardized JSON HTTP responses.

## 8. Logging Architecture
Using Python's standard `logging` library configured via `dictConfig`.
- **Structured JSON Logging**: Logs are output in JSON format for easy parsing by future monitoring tools (e.g., ELK stack).
- **Request Tracing**: Every log entry includes the `request_id` injected by the middleware.
- **Log Levels**: 
  - `INFO`: Lifecycle milestones (e.g., "Starting Grounding Phase").
  - `DEBUG`: Tensor shapes, GPU memory stats, and similarity scores.
  - `ERROR`: Stack traces for failed service calls.

## 9. Config Loading
Configuration is managed using `pydantic-settings`. 
The `Settings` class reads from `.env` and environment variables, providing strong typing and default fallbacks.
```python
class Settings(BaseSettings):
    APP_NAME: str = "OmniVision API"
    ENVIRONMENT: str = "development"
    GROUNDING_SIMILARITY_THRESHOLD: float = 0.75
    ACTIVE_KNOWLEDGE_PACKS: list[str] = ["heritage_pack"]
    MAX_UPLOAD_SIZE_MB: int = 10
    
    class Config:
        env_file = ".env"
```

## 10. Middleware
Two primary middlewares are deployed:
1. **CORSMiddleware**: Allows Streamlit (running on port 8501) to communicate with FastAPI (running on port 8000).
2. **RequestLoggingMiddleware**: Generates a UUID for `X-Request-ID`, logs request start/end, and measures latency.

## 11. Response Builder
Located at `orchestrator/response_builder.py`.
The internal state of a request is held in a `ProcessingContext` object. The `ResponseBuilder` converts this internal state into the external `OmniVisionResponse` schema.

Responsibilities:
- **Sanitization**: Removes internal tensor paths or temporary file routes.
- **URL Resolution**: Converts local file paths (e.g., `static/audio/file.wav`) to absolute URLs for the frontend.
- **Explainability Construction**: Packages the similarity scores, thresholds, and retrieved entities into the `explainability` JSON block.

## 12. Component & Sequence Interaction
*Note: Refer to 03_ENTERPRISE_SOFTWARE_ARCHITECTURE.md for the core sequence diagram.*

**Orchestrator Interaction with ModelManager (Sequence):**
1. Orchestrator calls `CaptionService.generate(image)`.
2. `CaptionService` requests BLIP model from `ModelManager.get_model("blip")`.
3. `ModelManager` checks if VRAM has space. If yes, loads BLIP and returns reference.
4. `CaptionService` runs inference and returns text.
5. Orchestrator calls `TTSService.generate(text)`.
6. `TTSService` requests XTTS model from `ModelManager`.
7. `ModelManager` sees VRAM is full, calls `unload_model("blip")`, clears cache, loads XTTS, returns reference.

This backend design guarantees that the FastAPI layer remains fast, responsive, and decoupled from the heavy, memory-intensive AI operations.
