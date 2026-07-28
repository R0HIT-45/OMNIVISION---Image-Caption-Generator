import logging
import threading
from enum import Enum
from typing import Any, Dict

import torch

from backend.app.config.settings import get_settings
from backend.app.models.registry import get_model_class
from backend.app.utils.memory_utils import clear_gpu_memory

logger = logging.getLogger("omnivision")
settings = get_settings()


class ModelState(Enum):
    UNLOADED = "UNLOADED"
    LOADING = "LOADING"
    READY = "READY"
    UNLOADING = "UNLOADING"
    FAILED = "FAILED"


class ModelManager:
    """
    Singleton manager to handle lazy loading and unloading of massive AI models.
    Crucial for running BLIP, CLIP, IndicTrans, and XTTS sequentially on 4GB VRAM.
    Tracks state to prevent race conditions.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ModelManager, cls).__new__(cls)
                cls._instance._models = {}  # Dictionary of instantiated model wrapper classes
                cls._instance._model_states = {}  # Dictionary tracking ModelState
                cls._instance.device = "cuda" if torch.cuda.is_available() else "cpu"
                logger.info(f"ModelManager initialized on device: {cls._instance.device}")
        return cls._instance

    def _get_model_id_for_key(self, model_key: str) -> str:
        if model_key == "blip":
            return settings.BLIP_MODEL
        if model_key == "clip":
            return settings.CLIP_MODEL
        if model_key == "translation":
            return settings.TRANSLATION_MODEL
        if model_key == "tts":
            return settings.TTS_MODEL
        raise ValueError(f"Unknown model key: {model_key}")

    def _get_category_for_key(self, model_key: str) -> str:
        if model_key == "blip":
            return "caption"
        if model_key == "clip":
            return "embedding"
        if model_key == "translation":
            return "translation"
        if model_key == "tts":
            return "tts"
        raise ValueError(f"Unknown model key: {model_key}")

    def get_model(self, model_key: str) -> Dict[str, Any]:
        """
        Retrieves a model's components. If not loaded, loads it.
        """
        with self._lock:
            state = self._model_states.get(model_key, ModelState.UNLOADED)

            if state == ModelState.READY:
                return self._models[model_key].get_components()

            if state in [ModelState.LOADING, ModelState.UNLOADING]:
                raise RuntimeError(
                    f"Race condition detected: Model {model_key} is currently {state.value}"
                )

            # If we need TTS, perform aggressive memory swap
            if model_key == "tts":
                logger.warning("Preparing to load TTS. Unloading Vision models to prevent OOM.")
                self._unload_model_unsafe("blip")
                self._unload_model_unsafe("clip")
                self._unload_model_unsafe("translation")

            # Load the model
            self._model_states[model_key] = ModelState.LOADING
            try:
                if model_key == "tts":
                    clear_gpu_memory()  # Clear before massive allocation

                model_id = self._get_model_id_for_key(model_key)
                category = self._get_category_for_key(model_key)
                ModelClass = get_model_class(category, model_id)

                instance = ModelClass()
                instance.load(self.device)

                self._models[model_key] = instance
                self._model_states[model_key] = ModelState.READY

                return instance.get_components()
            except Exception as e:
                self._model_states[model_key] = ModelState.FAILED
                logger.error(f"Failed to load model {model_key}: {e}")
                raise e

    def _unload_model_unsafe(self, model_key: str):
        """Internal unload method that assumes lock is already acquired."""
        if self._model_states.get(model_key) == ModelState.READY:
            self._model_states[model_key] = ModelState.UNLOADING
            logger.info(f"Unloading model: {model_key}")
            if model_key in self._models:
                del self._models[model_key]
            self._model_states[model_key] = ModelState.UNLOADED
            clear_gpu_memory()

    def unload_model(self, model_key: str):
        """Thread-safe public unload method."""
        with self._lock:
            self._unload_model_unsafe(model_key)


def get_model_manager() -> ModelManager:
    return ModelManager()
