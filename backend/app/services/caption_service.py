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

    @staticmethod
    def _format_caption(text: str) -> str:
        if not text:
            return text
        sentences = text.replace(" .", ".").split(". ")
        formatted = []
        for s in sentences:
            s = s.strip()
            if not s:
                continue
            if s and s[0].islower():
                s = s[0].upper() + s[1:]
            if not s.endswith("."):
                s += "."
            formatted.append(s)
        return " ".join(formatted)

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

            max_new_tokens = 200 if detailed else 100

            inputs = processor(images=image, return_tensors="pt").to(
                device, torch.float16 if device == "cuda" else torch.float32
            )

            with torch.inference_mode():
                generated_ids = model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,
                    num_beams=5,
                    repetition_penalty=1.1,
                    no_repeat_ngram_size=3,
                    early_stopping=True,
                    do_sample=True,
                    temperature=0.7,
                    top_p=0.9,
                )
            generated_text = processor.batch_decode(generated_ids, skip_special_tokens=True)[
                0
            ].strip()
            generated_text = self._format_caption(generated_text)

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
