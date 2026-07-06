import logging
import time
from fastapi import UploadFile
from typing import Optional

from app.schemas.schemas import ProcessingContext, OmniVisionResponse
from app.services.image_service import ImageService
from app.services.caption_service import CaptionService
from app.services.embedding_service import EmbeddingService
from app.services.retrieval_service import RetrievalService
from app.services.grounding_service import GroundingService
from app.services.translation_service import TranslationService
from app.services.tts_service import TTSService
from app.orchestrator.response_builder import ResponseBuilder
from app.exceptions.handlers import CriticalAIException, TranslationException, TTSException, OmniVisionException

logger = logging.getLogger("omnivision")

class RequestCoordinator:
    def __init__(self):
        self.image_service = ImageService()
        self.caption_service = CaptionService()
        self.embedding_service = EmbeddingService()
        self.retrieval_service = RetrievalService()
        self.grounding_service = GroundingService()
        self.translation_service = TranslationService()
        self.tts_service = TTSService()
        self.response_builder = ResponseBuilder()

    async def process(self, file: UploadFile, request_id: str) -> OmniVisionResponse:
        logger.info(f"Orchestrator started for request {request_id}", extra={"request_id": request_id, "phase": "init", "success": True})
        
        ctx = ProcessingContext(request_id=request_id, start_time=time.time())
        
        try:
            # 1. Validation & Preprocessing
            pil_image = await self.image_service.validate_and_preprocess(file)
            ctx.validated = True
            
            # 2. Vision Inference
            t0 = time.time()
            ctx.raw_caption = self.caption_service.generate(pil_image, detailed=True)
            ctx.embedding = self.embedding_service.generate_embedding(pil_image)
            ctx.vision_time = time.time() - t0
            
            # 3. Retrieval
            t0 = time.time()
            ctx.retrieved_entries = self.retrieval_service.search(ctx.embedding, k=1)
            ctx.retrieval_time = time.time() - t0
            
            # 4. Grounding (Confidence Gate)
            t0 = time.time()
            grounding_result = self.grounding_service.evaluate_and_ground(ctx.raw_caption, ctx.retrieved_entries)
            ctx.final_caption = grounding_result["final_caption"]
            ctx.grounding_applied = grounding_result["grounding_applied"]
            ctx.top_entity = grounding_result["top_entity"]
            ctx.top_fact = grounding_result.get("top_fact")
            ctx.top_score = grounding_result["top_score"]
            ctx.grounding_time = time.time() - t0
            
            # 5. Translation
            t0 = time.time()
            try:
                translations = self.translation_service.translate(ctx.final_caption)
                ctx.translations = translations
            except TranslationException as e:
                logger.warning(f"Translation step failed, skipping. {e}")
            ctx.translation_time = time.time() - t0
                
            # 6. Audio Generation
            t0 = time.time()
            texts_to_speak = {"english": ctx.final_caption}
            texts_to_speak.update(ctx.translations)
            
            try:
                audio_paths = self.tts_service.generate(texts_to_speak, request_id=request_id)
                ctx.audio_paths = audio_paths
            except TTSException as e:
                logger.warning(f"TTS step failed, skipping. {e}")
            ctx.audio_time = time.time() - t0
                
            return self.response_builder.build_success(ctx)
            
        except OmniVisionException as e:
            # Re-raise known API exceptions (Validation, UnsupportedMediaType, etc.)
            logger.error(f"API Exception in pipeline: {e}", extra={"request_id": request_id, "success": False})
            raise e
        except Exception as e:
            logger.error(f"Unexpected failure in Orchestrator: {e}", extra={"request_id": request_id, "success": False})
            raise CriticalAIException(f"Pipeline crashed unexpectedly: {str(e)}")

def get_orchestrator() -> RequestCoordinator:
    return RequestCoordinator()
