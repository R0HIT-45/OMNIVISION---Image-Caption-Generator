from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseAIModel(ABC):
    """
    Abstract base class for all AI models in OmniVision.
    Ensures all models can be loaded and unloaded uniformly.
    """
    @abstractmethod
    def load(self, device: str) -> None:
        """Loads the model into the specified device."""
        pass
        
    @abstractmethod
    def get_components(self) -> Dict[str, Any]:
        """Returns the loaded components (e.g., model, processor, tokenizer)."""
        pass

class BaseCaptionModel(BaseAIModel):
    """Base interface for image captioning models (BLIP, Florence, LLaVA)."""
    @abstractmethod
    def generate(self, image: Any, detailed: bool = False) -> str:
        pass

class BaseEmbeddingModel(BaseAIModel):
    """Base interface for vision encoders (CLIP)."""
    @abstractmethod
    def embed(self, image: Any) -> list[float]:
        pass

class BaseTranslationModel(BaseAIModel):
    """Base interface for machine translation models."""
    @abstractmethod
    def translate(self, text: str, target_lang: str) -> str:
        pass

class BaseTTSModel(BaseAIModel):
    """Base interface for Text-to-Speech models."""
    @abstractmethod
    def synthesize(self, text: str, target_lang: str, output_path: str) -> None:
        pass
