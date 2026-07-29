import logging
import time

from fastapi import UploadFile

from backend.app.exceptions.handlers import (
    CriticalAIException,
    OmniVisionException,
    TranslationException,
    TTSException,
)
from backend.app.orchestrator.response_builder import ResponseBuilder
from backend.app.schemas.schemas import OmniVisionResponse, ProcessingContext, StageError
from backend.app.services.caption_service import CaptionService
from backend.app.services.embedding_service import EmbeddingService
from backend.app.services.grounding_service import GroundingService
from backend.app.services.image_service import ImageService
from backend.app.services.retrieval_service import RetrievalService
from backend.app.services.translation_service import TranslationService
from backend.app.services.tts_service import TTSService
from backend.app.services.output_validator import (
    validate_audio_paths,
    validate_caption,
    validate_embedding,
    validate_translations,
)

logger = logging.getLogger("omnivision")

_coordinator: "RequestCoordinator | None" = None


def initialize_orchestrator() -> "RequestCoordinator":
    global _coordinator
    if _coordinator is not None:
        return _coordinator
    _coordinator = RequestCoordinator()
    return _coordinator


def get_orchestrator() -> "RequestCoordinator":
    global _coordinator
    if _coordinator is None:
        _coordinator = RequestCoordinator()
    return _coordinator


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

    def warm_up(self):
        logger.info("Initializing OmniVision...")

        logger.info("  Loading BLIP (caption model)...")
        self.caption_service.warm_up()
        logger.info("  ✓ BLIP ready")

        logger.info("  Loading CLIP (embedding model)...")
        self.embedding_service.warm_up()
        logger.info("  ✓ CLIP ready")

        logger.info("  Loading Translation (NLLB-200)...")
        self.translation_service.warm_up()
        logger.info("  ✓ Translation ready")

        logger.info("  Loading Retrieval Index (FAISS)...")
        self.retrieval_service.warm_up()
        logger.info("  ✓ Retrieval ready")

        logger.info("  ⏭  Skipping TTS (lazy-load to preserve VRAM)")
        logger.info("OmniVision backend ready.")

    def shutdown(self):
        logger.info("Shutting down OmniVision...")
        self.tts_service.shutdown()
        logger.info("Shutdown complete.")

    async def process(self, file: UploadFile, request_id: str) -> OmniVisionResponse:
        logger.info(
            "Pipeline started",
            extra={"request_id": request_id, "pipeline_stage": "init", "success": True},
        )

        ctx = ProcessingContext(request_id=request_id, start_time=time.time())

        try:
            # 1. Validation & Preprocessing
            pil_image = await self.image_service.validate_and_preprocess(file)
            ctx.validated = True

            # 2a. Caption generation
            t0 = time.time()
            ctx.raw_caption = self.caption_service.generate(
                pil_image, detailed=True, request_id=request_id
            )
            ctx.caption_time = time.time() - t0
            caption_err = validate_caption(ctx.raw_caption)
            if caption_err:
                logger.warning(f"Caption quality: {caption_err}", extra={"request_id": request_id, "pipeline_stage": "caption"})
                ctx.stage_errors.append(StageError(stage="caption", reason=caption_err))

            # 2b. Embedding generation
            t0 = time.time()
            ctx.embedding = self.embedding_service.generate_embedding(
                pil_image, request_id=request_id
            )
            ctx.embedding_time = time.time() - t0
            embedding_err = validate_embedding(ctx.embedding)
            if embedding_err:
                logger.warning(f"Embedding quality: {embedding_err}", extra={"request_id": request_id, "pipeline_stage": "embedding"})
                ctx.stage_errors.append(StageError(stage="embedding", reason=embedding_err))

            # 3. Retrieval
            t0 = time.time()
            ctx.retrieved_entries = self.retrieval_service.search(ctx.embedding, k=3)
            ctx.retrieval_time = time.time() - t0

            # 4. Grounding (Confidence Gate)
            t0 = time.time()
            grounding_result = self.grounding_service.evaluate_and_ground(
                ctx.raw_caption, ctx.retrieved_entries
            )
            ctx.final_caption = grounding_result["final_caption"]
            ctx.grounding_applied = grounding_result["grounding_applied"]
            ctx.top_entity = grounding_result["top_entity"]
            ctx.top_fact = grounding_result.get("top_fact")
            ctx.top_score = grounding_result["top_score"]
            ctx.confidenceLabel = grounding_result.get("confidenceLabel")
            ctx.matchedEntity = grounding_result.get("matchedEntity")
            ctx.reason = grounding_result.get("reason")
            ctx.grounding_time = time.time() - t0

            # 5. Translation
            t0 = time.time()
            try:
                ctx.translations = self.translation_service.translate(ctx.final_caption)
            except TranslationException as e:
                logger.warning(
                    f"Translation failed: {e}",
                    extra={
                        "request_id": request_id,
                        "pipeline_stage": "translation",
                        "success": False,
                    },
                )
                ctx.stage_errors.append(StageError(stage="translation", reason=str(e)))
            ctx.translation_time = time.time() - t0

            # 6. Audio Generation
            t0 = time.time()
            texts_to_speak = {"english": ctx.final_caption}
            texts_to_speak.update(ctx.translations)
            try:
                ctx.audio_paths = self.tts_service.generate(texts_to_speak, request_id=request_id)
            except TTSException as e:
                logger.warning(
                    f"TTS failed: {e}",
                    extra={
                        "request_id": request_id,
                        "pipeline_stage": "tts",
                        "success": False,
                    },
                )
                ctx.stage_errors.append(StageError(stage="speech", reason=str(e)))
            ctx.audio_time = time.time() - t0

            trn_errors = validate_translations(ctx.translations)
            for err in trn_errors:
                ctx.stage_errors.append(StageError(stage="translation", reason=err))
            audio_errors = validate_audio_paths(ctx.audio_paths)
            for err in audio_errors:
                ctx.stage_errors.append(StageError(stage="speech", reason=err))

            logger.info(
                "Pipeline completed",
                extra={
                    "request_id": request_id,
                    "pipeline_stage": "complete",
                    "caption_len": len(ctx.raw_caption or ""),
                    "embedding_dim": len(ctx.embedding) if ctx.embedding else 0,
                    "retrieved_count": len(ctx.retrieved_entries),
                    "grounding_applied": ctx.grounding_applied,
                    "translations": list(ctx.translations.keys()),
                    "audio_langs": list(ctx.audio_paths.keys()),
                    "stage_errors": len(ctx.stage_errors),
                    "total_time_ms": round((time.time() - ctx.start_time) * 1000, 2),
                },
            )
            return self.response_builder.build_success(ctx)

        except OmniVisionException as e:
            logger.error(
                f"Pipeline exception: {e}",
                extra={"request_id": request_id, "pipeline_stage": "error", "success": False},
            )
            raise
        except Exception as e:
            logger.error(
                f"Unexpected pipeline failure: {e}",
                extra={"request_id": request_id, "pipeline_stage": "error", "success": False},
            )
            raise CriticalAIException(f"Pipeline crashed: {str(e)}")
