import logging
import math
from typing import List, Optional

logger = logging.getLogger("omnivision")


def validate_caption(caption: str, min_length: int = 5) -> Optional[str]:
    if not caption or len(caption.strip()) < min_length:
        return f"Caption too short ({len(caption.strip())} chars, min {min_length})"
    return None


def validate_embedding(embedding: List[float]) -> Optional[str]:
    if not embedding:
        return "Embedding is empty"
    norm = math.sqrt(sum(v * v for v in embedding))
    if math.isnan(norm) or math.isinf(norm):
        return f"Embedding norm is invalid: {norm}"
    if norm < 1e-6:
        return f"Embedding norm is near zero: {norm}"
    if norm > 10.0:
        return f"Embedding norm unusually large: {norm}"
    return None


def validate_translations(translations: dict, expected_languages: Optional[List[str]] = None) -> List[str]:
    errors = []
    if not translations:
        errors.append("No translations produced")
        return errors
    for lang, text in translations.items():
        if not text or not text.strip():
            errors.append(f"Translation for '{lang}' is empty")
    return errors


def validate_audio_paths(audio_paths: dict) -> List[str]:
    import os
    errors = []
    for lang, path in audio_paths.items():
        if path and not os.path.isfile(path):
            errors.append(f"Audio file for '{lang}' does not exist: {path}")
    return errors
