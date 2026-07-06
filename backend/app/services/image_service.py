import io
from PIL import Image
from fastapi import UploadFile
from app.exceptions.handlers import ValidationException
import logging

logger = logging.getLogger("omnivision")

class ImageService:
    def __init__(self):
        self.allowed_types = ["image/jpeg", "image/png", "image/jpg"]
        self.max_size = 10 * 1024 * 1024  # 10 MB

    async def validate_and_preprocess(self, file: UploadFile) -> Image.Image:
        logger.info(f"Validating image: {file.filename}")
        
        # 1. Content-Type Validation
        if file.content_type not in self.allowed_types:
            raise ValidationException("Invalid file format. Only JPG and PNG are supported.")
            
        # 2. Read File Bytes
        file_bytes = await file.read()
        
        # 3. Size Validation
        if len(file_bytes) > self.max_size:
            raise ValidationException("File size exceeds the 10MB limit.")
            
        # 4. Open with PIL and Preprocess
        try:
            image = Image.open(io.BytesIO(file_bytes))
            # Convert to RGB (dropping alpha channel which causes issues with ViT)
            if image.mode != "RGB":
                image = image.convert("RGB")
                
            # Resize if too large to save memory during embedding
            max_dim = 1024
            if max(image.size) > max_dim:
                image.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
                
            logger.debug(f"Image preprocessed successfully. Final size: {image.size}")
            return image
        except Exception as e:
            logger.error(f"Failed to process image: {str(e)}")
            raise ValidationException("Corrupted or invalid image file.")
