import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.app.config.logging_config import setup_logging
from backend.app.config.settings import get_settings
from backend.app.exceptions.handlers import register_exception_handlers
from backend.app.middleware.logging_middleware import RequestLoggingMiddleware
from backend.app.config.config_validator import validate_configuration
from backend.app.orchestrator.request_coordinator import get_orchestrator, initialize_orchestrator
from backend.app.routes.api_frontend import router as frontend_api_router
from backend.app.routes.api_v1 import router as api_router

setup_logging()
logger = logging.getLogger("omnivision")

settings = get_settings()

validate_configuration()


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_orchestrator()
    coordinator = get_orchestrator()
    coordinator.warm_up()
    yield
    coordinator.shutdown()


app = FastAPI(
    title=settings.APP_NAME,
    description="Enterprise AI Image Captioning and Narration Platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggingMiddleware)

register_exception_handlers(app)

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.AUDIO_DIR, exist_ok=True)
app.mount("/static/audio", StaticFiles(directory=settings.AUDIO_DIR), name="audio")


@app.get("/api/v1/health")
async def health_check():
    import torch

    cuda_available = torch.cuda.is_available()
    gpu_name = torch.cuda.get_device_name(0) if cuda_available else None
    gpu_memory = torch.cuda.mem_get_info(0) if cuda_available else None

    kb_dir = settings.KNOWLEDGE_BASE_DIR
    packs_status = {}
    for pack in settings.ACTIVE_KNOWLEDGE_PACKS:
        index_path = os.path.join(kb_dir, pack, "index.faiss")
        packs_status[pack] = os.path.exists(index_path)

    return {
        "status": "online",
        "version": "1.0.0",
        "profile": settings.PROFILE,
        "cuda": cuda_available,
        "gpu": gpu_name,
        "gpu_memory_total_mb": round(gpu_memory.total / 1024**2) if gpu_memory else None,
        "gpu_memory_free_mb": round(gpu_memory.free / 1024**2) if gpu_memory else None,
        "knowledge_packs": packs_status,
        "grounding_threshold": settings.GROUNDING_SIMILARITY_THRESHOLD,
        "models": {
            "caption": settings.BLIP_MODEL,
            "embedding": settings.CLIP_MODEL,
            "translation": settings.TRANSLATION_MODEL,
            "tts": settings.TTS_MODEL,
        },
    }


app.include_router(api_router, prefix="/api/v1")
app.include_router(frontend_api_router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn

    logger.info(f"Starting {settings.APP_NAME} on {settings.FASTAPI_HOST}:{settings.FASTAPI_PORT}")
    uvicorn.run("app.main:app", host=settings.FASTAPI_HOST, port=settings.FASTAPI_PORT, reload=True)
