import logging
from PIL import Image
import torch
from app.managers.model_manager import get_model_manager
from app.exceptions.handlers import CriticalAIException

logger = logging.getLogger("omnivision")

class CaptionService:
    def __init__(self):
        self.model_manager = get_model_manager()

    def generate(self, image: Image.Image, detailed: bool = False) -> str:
        try:
            logger.info("Generating visual caption using BLIP-2...")
            blip_bundle = self.model_manager.get_model("blip")
            processor = blip_bundle["processor"]
            model = blip_bundle["model"]
            device = self.model_manager.device
            
            prompt = "Describe this image in detail:" if detailed else None
            max_new_tokens = 80 if detailed else 40
            
            inputs = processor(image, text=prompt, return_tensors="pt").to(device, torch.float16 if device == "cuda" else torch.float32)
            
            generated_ids = model.generate(**inputs, max_new_tokens=max_new_tokens)
            generated_text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0].strip()
            
            # Explicit cleanup
            del inputs
            del generated_ids
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                
            logger.info(f"Generated Caption: {generated_text}")
            return generated_text
            
        except Exception as e:
            logger.error(f"BLIP generation failed: {str(e)}")
            raise CriticalAIException("Failed to generate visual caption due to model error.")
