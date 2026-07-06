import logging
import torch
from PIL import Image
from typing import List
from app.managers.model_manager import get_model_manager
from app.exceptions.handlers import CriticalAIException

logger = logging.getLogger("omnivision")

class EmbeddingService:
    def __init__(self):
        self.model_manager = get_model_manager()

    def generate_embedding(self, image: Image.Image) -> List[float]:
        try:
            logger.info("Generating semantic embedding using CLIP...")
            clip_bundle = self.model_manager.get_model("clip")
            processor = clip_bundle["processor"]
            model = clip_bundle["model"]
            device = self.model_manager.device
            
            inputs = processor(images=image, return_tensors="pt").to(device)
            
            with torch.no_grad():
                image_features = model.get_image_features(**inputs)
                # L2 Normalization for Cosine Similarity (FAISS IndexFlatIP)
                image_features = image_features / image_features.norm(p=2, dim=-1, keepdim=True)
            
            vector = image_features.cpu().numpy().tolist()[0]
            
            # Cleanup
            del inputs
            del image_features
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                
            logger.debug("Embedding generated successfully.")
            return vector
            
        except Exception as e:
            logger.error(f"CLIP embedding failed: {str(e)}")
            raise CriticalAIException("Failed to generate image embedding.")
