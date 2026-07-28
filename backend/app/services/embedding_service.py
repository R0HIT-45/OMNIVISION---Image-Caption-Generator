import logging
from typing import List

import torch
from PIL import Image

from backend.app.exceptions.handlers import CriticalAIException
from backend.app.managers.model_manager import get_model_manager

logger = logging.getLogger("omnivision")


class EmbeddingService:
    def __init__(self):
        self.model_manager = get_model_manager()

    def warm_up(self):
        self.model_manager.get_model("clip")

    def generate_embedding(self, image: Image.Image, request_id: str = "") -> List[float]:
        try:
            logger.info(
                "Generating semantic embedding using CLIP...",
                extra={"request_id": request_id, "pipeline_stage": "embedding"},
            )
            clip_bundle = self.model_manager.get_model("clip")
            processor = clip_bundle["processor"]
            model = clip_bundle["model"]
            device = self.model_manager.device

            inputs = processor(images=image, return_tensors="pt").to(device)

            with torch.no_grad():
                image_output = model.get_image_features(**inputs)
                if hasattr(image_output, "pooler_output"):
                    image_features = image_output.pooler_output
                else:
                    image_features = image_output
                # L2 Normalization for Cosine Similarity (FAISS IndexFlatIP)
                image_features = image_features / image_features.norm(p=2, dim=-1, keepdim=True)

            vector = image_features.cpu().numpy().tolist()[0]

            del inputs
            del image_features
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            logger.debug(
                "Embedding generated successfully.",
                extra={"request_id": request_id, "pipeline_stage": "embedding"},
            )
            return vector

        except Exception as e:
            logger.error(
                f"CLIP embedding failed: {str(e)}",
                extra={"request_id": request_id, "pipeline_stage": "embedding", "success": False},
            )
            raise CriticalAIException("Failed to generate image embedding.")
