import logging
from typing import Any, Dict

import torch

from backend.app.config.settings import get_settings
from backend.app.models.base import (
    BaseCaptionModel,
    BaseEmbeddingModel,
    BaseTranslationModel,
    BaseTTSModel,
)

logger = logging.getLogger("omnivision")
settings = get_settings()


class BLIP2Model(BaseCaptionModel):
    def __init__(self):
        self.processor = None
        self.model = None

    def load(self, device: str) -> None:
        logger.info(f"Loading BLIP-2 model: {settings.BLIP_MODEL} (4-bit)")
        from transformers import BitsAndBytesConfig, Blip2ForConditionalGeneration, Blip2Processor

        quantization_config = None
        if device == "cuda":
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True, bnb_4bit_compute_dtype=torch.float16
            )

        self.processor = Blip2Processor.from_pretrained(settings.BLIP_MODEL)
        device_map = "auto" if device == "cuda" else None

        self.model = Blip2ForConditionalGeneration.from_pretrained(
            settings.BLIP_MODEL,
            quantization_config=quantization_config,
            device_map=device_map,
        )
        if device == "cpu":
            self.model = self.model.to(device)

    def get_components(self) -> Dict[str, Any]:
        return {"processor": self.processor, "model": self.model}

    def generate(self, image: Any, detailed: bool = False) -> str:
        raise NotImplementedError("Inference delegated to service layer via ModelManager")


class BLIPBaseModel(BaseCaptionModel):
    def __init__(self):
        self.processor = None
        self.model = None

    def load(self, device: str) -> None:
        logger.info(f"Loading BLIP Base model: {settings.BLIP_MODEL}")
        from transformers import BlipForConditionalGeneration, BlipProcessor

        self.processor = BlipProcessor.from_pretrained(settings.BLIP_MODEL)
        self.model = BlipForConditionalGeneration.from_pretrained(settings.BLIP_MODEL).to(device)
        self.model.eval()

    def get_components(self) -> Dict[str, Any]:
        return {"processor": self.processor, "model": self.model}

    def generate(self, image: Any, detailed: bool = False) -> str:
        raise NotImplementedError("Inference delegated to service layer via ModelManager")


class CLIPModel(BaseEmbeddingModel):
    def __init__(self):
        self.processor = None
        self.model = None

    def load(self, device: str) -> None:
        logger.info(f"Loading CLIP model: {settings.CLIP_MODEL}")
        from transformers import CLIPModel as HFCLIPModel
        from transformers import CLIPProcessor

        self.processor = CLIPProcessor.from_pretrained(settings.CLIP_MODEL)
        self.model = HFCLIPModel.from_pretrained(settings.CLIP_MODEL).to(device)

    def get_components(self) -> Dict[str, Any]:
        return {"processor": self.processor, "model": self.model}

    def embed(self, image: Any) -> list[float]:
        raise NotImplementedError("Inference delegated to service layer via ModelManager")


class NLLBTranslationModel(BaseTranslationModel):
    def __init__(self):
        self.tokenizer = None
        self.model = None

    def load(self, device: str) -> None:
        logger.info(f"Loading Translation model: {settings.TRANSLATION_MODEL}")
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

        self.tokenizer = AutoTokenizer.from_pretrained(settings.TRANSLATION_MODEL)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(settings.TRANSLATION_MODEL).to(device)

    def get_components(self) -> Dict[str, Any]:
        return {"tokenizer": self.tokenizer, "model": self.model}

    def translate(self, text: str, target_lang: str) -> str:
        raise NotImplementedError("Inference delegated to service layer via ModelManager")


class XTTSModel(BaseTTSModel):
    def __init__(self):
        self.model = None

    def load(self, device: str) -> None:
        logger.info(f"Loading TTS model: {settings.TTS_MODEL}")
        from TTS.api import TTS

        self.model = TTS(settings.TTS_MODEL).to(device)

    def get_components(self) -> Dict[str, Any]:
        return {"model": self.model}

    def synthesize(self, text: str, target_lang: str, output_path: str) -> None:
        raise NotImplementedError("Inference delegated to service layer via ModelManager")
