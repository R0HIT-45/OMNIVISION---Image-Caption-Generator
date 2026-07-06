"""Caption generation service — supports BLIP base and BLIP-2 models.

The model is selected via the MODEL_NAME environment variable.
Dual caption mode produces a short caption and a detailed description.
"""

import logging
import threading
import time
from pathlib import Path
from typing import Any

from backend.utils.config import settings

logger = logging.getLogger(__name__)

# Prompt templates for dual caption mode
_SHORT_PROMPT = "Describe this image in one concise sentence."
_DETAILED_PROMPT = (
    "Provide a detailed description of this image including objects, "
    "actions, surroundings and context."
)


class CaptionService:
    """Lazy-loaded inference service for image captioning."""

    def __init__(self) -> None:
        self._processor: Any = None
        self._model: Any = None
        self._device: str | None = None
        self._lock = threading.Lock()
        self._quantized = False
        self._is_blip2: bool = False  # True when using BLIP-2 architecture

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def is_loaded(self) -> bool:
        return self._model is not None and self._processor is not None

    @property
    def device(self) -> str:
        if self._device is None:
            import torch

            self._device = "cuda" if torch.cuda.is_available() else "cpu"
        return self._device

    # ------------------------------------------------------------------
    # Model loading
    # ------------------------------------------------------------------

    def load_model(self) -> None:
        """Load processor and model (thread-safe, idempotent)."""
        import torch

        model_name: str = settings.model_name
        self._is_blip2 = "blip2" in model_name.lower()

        if self._is_blip2:
            from transformers import (
                Blip2ForConditionalGeneration,
                Blip2Processor,
            )

            processor_cls = Blip2Processor
            model_cls = Blip2ForConditionalGeneration
        else:
            from transformers import (
                BlipForConditionalGeneration,
                BlipProcessor,
            )

            processor_cls = BlipProcessor
            model_cls = BlipForConditionalGeneration

        with self._lock:
            if self.is_loaded:
                return

            device = self.device
            logger.info(
                "Loading model '%s' on device '%s' (blip2=%s)",
                model_name,
                device,
                self._is_blip2,
            )
            start = time.perf_counter()

            self._processor = processor_cls.from_pretrained(model_name)

            model_kwargs: dict = {}
            if device == "cuda":
                try:
                    from transformers import BitsAndBytesConfig

                    model_kwargs["quantization_config"] = BitsAndBytesConfig(
                        load_in_4bit=True,
                        bnb_4bit_compute_dtype=torch.float16,
                        bnb_4bit_use_double_quant=True,
                        bnb_4bit_quant_type="nf4",
                    )
                    model_kwargs["device_map"] = "auto"
                    self._quantized = True
                    logger.info("Using 4-bit quantization")
                except (ImportError, Exception) as exc:
                    logger.warning(
                        "4-bit quantization unavailable (%s); falling back to float16",
                        exc,
                    )
                    model_kwargs["torch_dtype"] = torch.float16
                    model_kwargs["device_map"] = "auto"
            else:
                logger.warning("CUDA not available; running model on CPU (slow)")
                model_kwargs["torch_dtype"] = torch.float32

            self._model = model_cls.from_pretrained(model_name, **model_kwargs)

            if device == "cpu":
                self._model.to(device)

            elapsed = time.perf_counter() - start
            logger.info(
                "Model loaded in %.2f seconds (quantized=%s)",
                elapsed,
                self._quantized,
            )

    # ------------------------------------------------------------------
    # Caption generation
    # ------------------------------------------------------------------

    def _generate(
        self,
        image,
        prompt: str | None,
        max_new_tokens: int,
    ) -> str:
        """Run a single generation pass."""
        import torch

        assert self._processor is not None
        assert self._model is not None

        if self._is_blip2:
            # BLIP-2 uses prompt-based generation
            inputs = self._processor(
                images=image, text=prompt or "", return_tensors="pt"
            )
        else:
            # BLIP base — conditional generation (no text prompt) or prompted
            if prompt:
                inputs = self._processor(
                    images=image, text=prompt, return_tensors="pt"
                )
            else:
                inputs = self._processor(images=image, return_tensors="pt")

        inputs = inputs.to(self.device)

        with torch.inference_mode():
            generated_ids = self._model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                num_beams=5,
            )

        caption = self._processor.batch_decode(
            generated_ids,
            skip_special_tokens=True,
        )[0].strip()

        return caption

    def generate_captions(
        self,
        image_path: Path,
    ) -> dict[str, str]:
        """Generate both short and detailed captions for the given image.

        Returns
        -------
        dict with keys ``short_caption`` and ``detailed_caption``.
        """
        from PIL import Image

        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        self.load_model()

        image = Image.open(image_path).convert("RGB")

        # --- Short caption ---
        short_caption = self._generate(
            image,
            prompt=_SHORT_PROMPT,
            max_new_tokens=30,
        )

        # --- Detailed caption ---
        detailed_caption = self._generate(
            image,
            prompt=_DETAILED_PROMPT,
            max_new_tokens=100,
        )

        logger.info(
            "Captions for %s — short: %s | detailed: %s",
            image_path.name,
            short_caption[:60],
            detailed_caption[:80],
        )

        return {
            "short_caption": short_caption,
            "detailed_caption": detailed_caption,
        }


# Module-level singleton
caption_service = CaptionService()
"""Caption generation service — supports BLIP base and BLIP-2 models.

The model is selected via the MODEL_NAME environment variable.
Dual caption mode produces a short caption and a detailed description.
"""

import logging
import threading
import time
from pathlib import Path
from typing import Any

from backend.utils.config import settings

logger = logging.getLogger(__name__)

# Prompt templates for dual caption mode
_SHORT_PROMPT = "Describe this image in one concise sentence."
_DETAILED_PROMPT = (
    "Provide a detailed description of this image including objects, "
    "actions, surroundings and context."
)


class CaptionService:
    """Lazy-loaded inference service for image captioning."""

    def __init__(self) -> None:
        self._processor: Any = None
        self._model: Any = None
        self._device: str | None = None
        self._lock = threading.Lock()
        self._quantized = False
        self._is_blip2: bool = False  # True when using BLIP-2 architecture

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def is_loaded(self) -> bool:
        return self._model is not None and self._processor is not None

    @property
    def device(self) -> str:
        if self._device is None:
            import torch

            self._device = "cuda" if torch.cuda.is_available() else "cpu"
        return self._device

    # ------------------------------------------------------------------
    # Model loading
    # ------------------------------------------------------------------

    def load_model(self) -> None:
        """Load processor and model (thread-safe, idempotent)."""
        import torch

        model_name: str = settings.model_name
        self._is_blip2 = "blip2" in model_name.lower()

        if self._is_blip2:
            from transformers import (
                Blip2ForConditionalGeneration,
                Blip2Processor,
            )

            processor_cls = Blip2Processor
            model_cls = Blip2ForConditionalGeneration
        else:
            from transformers import (
                BlipForConditionalGeneration,
                BlipProcessor,
            )

            processor_cls = BlipProcessor
            model_cls = BlipForConditionalGeneration

        with self._lock:
            if self.is_loaded:
                return

            device = self.device
            logger.info(
                "Loading model '%s' on device '%s' (blip2=%s)",
                model_name,
                device,
                self._is_blip2,
            )
            start = time.perf_counter()

            self._processor = processor_cls.from_pretrained(model_name)

            model_kwargs: dict = {}
            if device == "cuda":
                try:
                    from transformers import BitsAndBytesConfig

                    model_kwargs["quantization_config"] = BitsAndBytesConfig(
                        load_in_4bit=True,
                        bnb_4bit_compute_dtype=torch.float16,
                        bnb_4bit_use_double_quant=True,
                        bnb_4bit_quant_type="nf4",
                    )
                    model_kwargs["device_map"] = "auto"
                    self._quantized = True
                    logger.info("Using 4-bit quantization")
                except (ImportError, Exception) as exc:
                    logger.warning(
                        "4-bit quantization unavailable (%s); falling back to float16",
                        exc,
                    )
                    model_kwargs["torch_dtype"] = torch.float16
                    model_kwargs["device_map"] = "auto"
            else:
                logger.warning("CUDA not available; running model on CPU (slow)")
                model_kwargs["torch_dtype"] = torch.float32

            self._model = model_cls.from_pretrained(model_name, **model_kwargs)

            if device == "cpu":
                self._model.to(device)

            elapsed = time.perf_counter() - start
            logger.info(
                "Model loaded in %.2f seconds (quantized=%s)",
                elapsed,
                self._quantized,
            )

    # ------------------------------------------------------------------
    # Caption generation
    # ------------------------------------------------------------------

    def _generate(
        self,
        image,
        prompt: str | None,
        max_new_tokens: int,
    ) -> str:
        """Run a single generation pass."""
        import torch

        assert self._processor is not None
        assert self._model is not None

        if self._is_blip2:
            # BLIP-2 uses prompt-based generation
            inputs = self._processor(
                images=image, text=prompt or "", return_tensors="pt"
            )
        else:
            # BLIP base — conditional generation (no text prompt) or prompted
            if prompt:
                inputs = self._processor(
                    images=image, text=prompt, return_tensors="pt"
                )
            else:
                inputs = self._processor(images=image, return_tensors="pt")

        inputs = inputs.to(self.device)

        with torch.inference_mode():
            generated_ids = self._model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                num_beams=5,
            )

        caption = self._processor.batch_decode(
            generated_ids,
            skip_special_tokens=True,
        )[0].strip()

        return caption

    def generate_captions(
        self,
        image_path: Path,
    ) -> dict[str, str]:
        """Generate both short and detailed captions for the given image.

        Returns
        -------
        dict with keys ``short_caption`` and ``detailed_caption``.
        """
        from PIL import Image

        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        self.load_model()

        image = Image.open(image_path).convert("RGB")

        # --- Short caption ---
        short_caption = self._generate(
            image,
            prompt=_SHORT_PROMPT,
            max_new_tokens=30,
        )

        # --- Detailed caption ---
        detailed_caption = self._generate(
            image,
            prompt=_DETAILED_PROMPT,
            max_new_tokens=100,
        )

        logger.info(
            "Captions for %s — short: %s | detailed: %s",
            image_path.name,
            short_caption[:60],
            detailed_caption[:80],
        )

        return {
            "short_caption": short_caption,
            "detailed_caption": detailed_caption,
        }


# Module-level singleton
caption_service = CaptionService()
"""BLIP-2 caption generation service with optional 4-bit quantization."""

import logging
import threading
import time
from pathlib import Path
from typing import Any

from backend.utils.config import settings

logger = logging.getLogger(__name__)


class Blip2CaptionService:
    """Lazy-loaded BLIP-2 inference service for image captioning."""

    def __init__(self) -> None:
        self._processor: Any = None
        self._model: Any = None
        self._device: str | None = None
        self._lock = threading.Lock()
        self._quantized = False

    @property
    def is_loaded(self) -> bool:
        return self._model is not None and self._processor is not None

    @property
    def device(self) -> str:
        if self._device is None:
            import torch

            self._device = "cuda" if torch.cuda.is_available() else "cpu"
        return self._device

    def load_model(self) -> None:
        """Load BLIP-2 processor and model (thread-safe, idempotent)."""
        import torch
        from transformers import Blip2ForConditionalGeneration, Blip2Processor

        with self._lock:
            if self.is_loaded:
                return

            device = self.device
            logger.info(
                "Loading BLIP-2 model '%s' on device '%s'",
                settings.blip2_model,
                device,
            )
            start = time.perf_counter()

            self._processor = Blip2Processor.from_pretrained(settings.blip2_model)

            model_kwargs: dict = {}
            if device == "cuda":
                try:
                    from transformers import BitsAndBytesConfig

                    model_kwargs["quantization_config"] = BitsAndBytesConfig(
                        load_in_4bit=True,
                        bnb_4bit_compute_dtype=torch.float16,
                        bnb_4bit_use_double_quant=True,
                        bnb_4bit_quant_type="nf4",
                    )
                    model_kwargs["device_map"] = "auto"
                    self._quantized = True
                    logger.info("Using 4-bit quantization for BLIP-2")
                except (ImportError, Exception) as exc:
                    logger.warning(
                        "4-bit quantization unavailable (%s); falling back to float16",
                        exc,
                    )
                    model_kwargs["torch_dtype"] = torch.float16
                    model_kwargs["device_map"] = "auto"
            else:
                logger.warning("CUDA not available; running BLIP-2 on CPU (slow)")
                model_kwargs["torch_dtype"] = torch.float32

            self._model = Blip2ForConditionalGeneration.from_pretrained(
                settings.blip2_model,
                **model_kwargs,
            )

            if device == "cpu":
                self._model.to(device)

            elapsed = time.perf_counter() - start
            logger.info(
                "BLIP-2 loaded in %.2f seconds (quantized=%s)",
                elapsed,
                self._quantized,
            )

    def generate_caption(self, image_path: Path, max_new_tokens: int = 50) -> str:
        """Generate an English caption for the given image."""
        import torch
        from PIL import Image

        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        self.load_model()
        assert self._processor is not None
        assert self._model is not None

        image = Image.open(image_path).convert("RGB")
        inputs = self._processor(images=image, return_tensors="pt")

        if self.device == "cuda":
            inputs = inputs.to("cuda")
        else:
            inputs = inputs.to(self.device)

        with torch.inference_mode():
            generated_ids = self._model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                num_beams=5,
            )

        caption = self._processor.batch_decode(
            generated_ids,
            skip_special_tokens=True,
        )[0].strip()

        logger.info("Generated caption for %s: %s", image_path.name, caption[:80])
        return caption


blip_service = Blip2CaptionService()
