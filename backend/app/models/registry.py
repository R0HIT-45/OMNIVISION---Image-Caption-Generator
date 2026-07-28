from typing import Type

from backend.app.models.base import BaseAIModel
from backend.app.models.implementations import (
    BLIP2Model,
    BLIPBaseModel,
    CLIPModel,
    NLLBTranslationModel,
    XTTSModel,
)

# The registry maps internal identifiers to concrete model classes.
# This makes it trivial to swap out models without changing orchestration logic.

CAPTION_MODELS = {
    "blip2-opt-2.7b": BLIP2Model,
    "blip-image-captioning-base": BLIPBaseModel,
    # "florence-2": Florence2Model
}

EMBEDDING_MODELS = {
    "clip-vit-base-patch32": CLIPModel,
}

TRANSLATION_MODELS = {
    "nllb-200-distilled-600M": NLLBTranslationModel,
}

TTS_MODELS = {
    "xtts_v2": XTTSModel,
}


def get_model_class(model_category: str, model_id: str) -> Type[BaseAIModel]:
    registry = {}
    if model_category == "caption":
        registry = CAPTION_MODELS
    elif model_category == "embedding":
        registry = EMBEDDING_MODELS
    elif model_category == "translation":
        registry = TRANSLATION_MODELS
    elif model_category == "tts":
        registry = TTS_MODELS
    else:
        raise ValueError(f"Unknown model category: {model_category}")

    # Match the model ID (which might have organization prefixes like Salesforce/)
    # We check if the ID ends with the registered key
    for key, cls in registry.items():
        if model_id.endswith(key):
            return cls

    raise ValueError(f"No registered model class for {model_category}: {model_id}")
