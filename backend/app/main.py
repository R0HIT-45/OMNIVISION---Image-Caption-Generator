import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config.settings import get_settings
from app.config.logging_config import setup_logging
from app.exceptions.handlers import register_exception_handlers
from app.middleware.logging_middleware import RequestLoggingMiddleware

# Setup logging
setup_logging()
logger = logging.getLogger("omnivision")

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    description="Enterprise AI Image Captioning and Narration Platform",
    version="1.0.0"
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggingMiddleware)

# Exception Handlers
register_exception_handlers(app)

# Static Files (for audio outputs)
# Ensure directories exist
import os
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.AUDIO_DIR, exist_ok=True)
app.mount("/static/audio", StaticFiles(directory=settings.AUDIO_DIR), name="audio")

@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "online",
        "version": "1.0",
        "timestamp": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()
    }

# Import and include API routers
from app.routes.api_v1 import router as api_router
app.include_router(api_router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting {settings.APP_NAME} on {settings.FASTAPI_HOST}:{settings.FASTAPI_PORT}")
    uvicorn.run("app.main:app", host=settings.FASTAPI_HOST, port=settings.FASTAPI_PORT, reload=True)
