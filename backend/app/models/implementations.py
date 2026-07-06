import logging
import torch
from typing import Dict, Any
from app.models.base import BaseCaptionModel, BaseEmbeddingModel, BaseTranslationModel, BaseTTSModel
from app.config.settings import get_settings

logger = logging.getLogger("omnivision")
settings = get_settings()

class BLIP2Model(BaseCaptionModel):
    def __init__(self):
        self.processor = None
        self.model = None
        
    def load(self, device: str) -> None:
        logger.info(f"Loading BLIP-2 model: {settings.BLIP_MODEL} (4-bit)")
        from transformers import Blip2Processor, Blip2ForConditionalGeneration, BitsAndBytesConfig
        
        quantization_config = None
        if device == "cuda":
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16
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
        # Implementation moved to service or kept here. We'll let service handle inference 
        # using the raw components for now, to minimize refactoring risk.
        pass

class BLIPBaseModel(BaseCaptionModel):
    def __init__(self):
        self.processor = None
        self.model = None
        
    def load(self, device: str) -> None:
        logger.info(f"Loading BLIP Base model: {settings.BLIP_MODEL}")
        from transformers import BlipProcessor, BlipForConditionalGeneration
        
        self.processor = BlipProcessor.from_pretrained(settings.BLIP_MODEL)
        self.model = BlipForConditionalGeneration.from_pretrained(settings.BLIP_MODEL).to(device)
            
    def get_components(self) -> Dict[str, Any]:
        return {"processor": self.processor, "model": self.model}

    def generate(self, image: Any, detailed: bool = False) -> str:
        pass

class CLIPModel(BaseEmbeddingModel):
    def __init__(self):
        self.processor = None
        self.model = None

    def load(self, device: str) -> None:
        logger.info(f"Loading CLIP model: {settings.CLIP_MODEL}")
        from transformers import CLIPProcessor, CLIPModel as HFCLIPModel
        self.processor = CLIPProcessor.from_pretrained(settings.CLIP_MODEL)
        self.model = HFCLIPModel.from_pretrained(settings.CLIP_MODEL).to(device)

    def get_components(self) -> Dict[str, Any]:
        return {"processor": self.processor, "model": self.model}

    def embed(self, image: Any) -> list[float]:
        pass

class IndicTrans2Model(BaseTranslationModel):
    def __init__(self):
        self.tokenizer = None
        self.model = None

    def load(self, device: str) -> None:
        logger.info(f"Loading Translation model: {settings.TRANSLATION_MODEL}")
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(settings.TRANSLATION_MODEL, trust_remote_code=True)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(
            settings.TRANSLATION_MODEL, 
            trust_remote_code=True
        ).to(device)

    def get_components(self) -> Dict[str, Any]:
        return {"tokenizer": self.tokenizer, "model": self.model}

    def translate(self, text: str, target_lang: str) -> str:
        pass

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
        pass
