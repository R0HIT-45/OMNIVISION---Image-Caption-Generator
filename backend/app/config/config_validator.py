import os
import torch
import logging
from app.config.settings import get_settings

logger = logging.getLogger("omnivision.startup")

def validate_configuration():
    """Validates the system configuration on FastAPI startup. Fails fast if invalid."""
    logger.info("Running startup configuration validation...")
    settings = get_settings()

    # 1. Profile Validation
    valid_profiles = ["development", "demo", "production"]
    if settings.PROFILE not in valid_profiles:
        raise ValueError(f"Invalid PROFILE '{settings.PROFILE}'. Must be one of {valid_profiles}.")

    # 2. Directory Validation
    directories = [settings.UPLOAD_DIR, settings.AUDIO_DIR, settings.KNOWLEDGE_BASE_DIR]
    for directory in directories:
        if not os.path.exists(directory):
            logger.info(f"Directory {directory} does not exist. Creating it now.")
            os.makedirs(directory, exist_ok=True)

    # 3. CUDA Validation (Crucial for Demo/Production profiles)
    cuda_available = torch.cuda.is_available()
    if settings.PROFILE in ["demo", "production"] and not cuda_available:
        logger.warning(f"PROFILE is '{settings.PROFILE}' but CUDA is not available! The system will attempt to fall back to CPU, which may crash or be extremely slow.")
    
    # 4. Threshold Validation
    if not (0.0 <= settings.GROUNDING_SIMILARITY_THRESHOLD <= 1.0):
        raise ValueError(f"GROUNDING_SIMILARITY_THRESHOLD must be between 0.0 and 1.0. Found: {settings.GROUNDING_SIMILARITY_THRESHOLD}")

    # 5. Knowledge Pack Validation
    for pack in settings.ACTIVE_KNOWLEDGE_PACKS:
        pack_path = os.path.join(settings.KNOWLEDGE_BASE_DIR, pack, "index.faiss")
        if not os.path.exists(pack_path):
            logger.error(f"Knowledge Pack Error: Application Startup Failed. Active pack '{pack}' is missing its index.faiss file at {pack_path}.")
            raise ValueError(f"Missing required Knowledge Pack: {pack}")

    logger.info("Configuration validation completed successfully.")

