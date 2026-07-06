import os
import json
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "OmniVision API"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    FASTAPI_HOST: str = os.getenv("FASTAPI_HOST", "0.0.0.0")
    FASTAPI_PORT: int = int(os.getenv("FASTAPI_PORT", 8000))
    API_BASE_URL: str = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")
    
    # AI Config
    BLIP_MODEL: str = os.getenv("BLIP_MODEL", "Salesforce/blip2-opt-2.7b")
    CLIP_MODEL: str = os.getenv("CLIP_MODEL", "openai/clip-vit-base-patch32")
    TRANSLATION_MODEL: str = os.getenv("TRANSLATION_MODEL", "ai4bharat/indictrans2-en-indic-dist-200M")
    TTS_MODEL: str = os.getenv("TTS_MODEL", "tts_models/multilingual/multi-dataset/xtts_v2")
    
    GROUNDING_SIMILARITY_THRESHOLD: float = float(os.getenv("GROUNDING_SIMILARITY_THRESHOLD", 0.75))
    
    @property
    def ACTIVE_KNOWLEDGE_PACKS(self) -> List[str]:
        raw = os.getenv("ACTIVE_KNOWLEDGE_PACKS", '["heritage_pack"]')
        return json.loads(raw)
    
    # Paths
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "static/uploads")
    AUDIO_DIR: str = os.getenv("AUDIO_DIR", "static/audio")
    KNOWLEDGE_BASE_DIR: str = os.getenv("KNOWLEDGE_BASE_DIR", "knowledge_base")
    
    # Limits
    MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", 10))

    class Config:
        env_file = ".env"
        extra = "allow"

def get_settings() -> Settings:
    return Settings()
