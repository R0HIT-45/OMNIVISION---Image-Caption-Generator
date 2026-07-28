import logging

import torch
from PIL import Image

from backend.app.exceptions.handlers import CriticalAIException
from backend.app.managers.model_manager import get_model_manager

logger = logging.getLogger("omnivision")


class CaptionService:
    def __init__(self):
        self.model_manager = get_model_manager()

    def warm_up(self):
        self.model_manager.get_model("blip")

    def generate(self, image: Image.Image, detailed: bool = False, request_id: str = "") -> str:
        try:
            logger.info(
                "Generating visual caption using Vision Model...",
                extra={"request_id": request_id, "pipeline_stage": "caption"},
            )
            blip_bundle = self.model_manager.get_model("blip")
            processor = blip_bundle["processor"]
            model = blip_bundle["model"]
            device = self.model_manager.device

            # For base BLIP models, unconditional generation often yields better, less repetitive results
            # than prefixing with a prompt unless the model was explicitly fine-tuned for instruction following.
            max_new_tokens = 80 if detailed else 40

            inputs = processor(image, return_tensors="pt").to(
                device, torch.float16 if device == "cuda" else torch.float32
            )

            generated_ids = model.generate(**inputs, max_new_tokens=max_new_tokens)
            generated_text = processor.batch_decode(generated_ids, skip_special_tokens=True)[
                0
            ].strip()

            del inputs
            del generated_ids
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            logger.info(
                f"Generated Caption: {generated_text}",
                extra={"request_id": request_id, "pipeline_stage": "caption"},
            )
            return generated_text

        except Exception as e:
            logger.error(
                f"BLIP generation failed: {str(e)}",
                extra={"request_id": request_id, "pipeline_stage": "caption", "success": False},
            )
            raise CriticalAIException("Failed to generate visual caption due to model error.")
