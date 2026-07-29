import io
import logging

from fastapi import UploadFile
from PIL import Image

from backend.app.exceptions.handlers import UnsupportedMediaTypeException, ValidationException

logger = logging.getLogger("omnivision")

MAX_PIXELS = 50_000_000  # 50 megapixel sanity limit


class ImageService:
    def __init__(self):
        self.allowed_types = ["image/jpeg", "image/png", "image/jpg", "image/webp"]
        self.max_size = 12 * 1024 * 1024  # 12 MB

    async def validate_and_preprocess(self, file: UploadFile) -> Image.Image:
        logger.info(f"Validating image: {file.filename}")

        if file.content_type not in self.allowed_types:
            raise UnsupportedMediaTypeException(
                "Invalid file format. Only JPG, PNG, and WebP are supported."
            )

        file_bytes = await file.read()

        if len(file_bytes) > self.max_size:
            raise ValidationException("File size exceeds the 12MB limit.")

        try:
            # Verify image header before full decode (decompression bomb protection)
            with Image.open(io.BytesIO(file_bytes)) as verify_img:
                verify_img.verify()
            image = Image.open(io.BytesIO(file_bytes))
            if image.mode != "RGB":
                image = image.convert("RGB")

            w, h = image.size
            if w * h > MAX_PIXELS:
                raise ValidationException(
                    f"Image dimensions ({w}x{h}) exceed the {MAX_PIXELS:,} pixel limit."
                )

            max_dim = 1024
            if max(image.size) > max_dim:
                image.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)

            logger.debug(f"Image preprocessed. Final size: {image.size}")
            return image
        except ValidationException:
            raise
        except Exception as e:
            logger.error(f"Failed to process image: {str(e)}")
            raise ValidationException("Corrupted or invalid image file.")
