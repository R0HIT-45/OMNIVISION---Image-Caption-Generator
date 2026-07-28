import time

from backend.app.config.settings import get_settings
from backend.app.schemas.schemas import (
    ExplainabilityData,
    Metadata,
    ModelVersions,
    OmniVisionResponse,
    ProcessingContext,
    ProcessingTimes,
    ResponseData,
)

settings = get_settings()


class ResponseBuilder:
    def build_success(self, ctx: ProcessingContext) -> OmniVisionResponse:
        total_time = time.time() - ctx.start_time

        data = ResponseData(
            raw_caption=ctx.raw_caption or "",
            final_caption=ctx.final_caption or "",
            translations=ctx.translations,
            audio_urls=ctx.audio_paths,
        )

        explainability = ExplainabilityData(
            top_retrieved_entity=ctx.top_entity,
            retrieved_fact=ctx.top_fact,
            similarity_score=ctx.top_score,
            threshold_used=settings.GROUNDING_SIMILARITY_THRESHOLD,
            grounding_applied=ctx.grounding_applied,
            confidenceLabel=ctx.confidenceLabel,
            matchedEntity=ctx.matchedEntity,
            reason=ctx.reason,
        )

        model_versions = ModelVersions(
            caption=settings.BLIP_MODEL,
            embedding=settings.CLIP_MODEL,
            translation=settings.TRANSLATION_MODEL,
            tts=settings.TTS_MODEL,
        )

        processing_times = ProcessingTimes(
            caption_ms=round(ctx.caption_time * 1000, 2),
            embedding_ms=round(ctx.embedding_time * 1000, 2),
            retrieval_ms=round(ctx.retrieval_time * 1000, 2),
            grounding_ms=round(ctx.grounding_time * 1000, 2),
            translation_ms=round(ctx.translation_time * 1000, 2),
            audio_ms=round(ctx.audio_time * 1000, 2),
            total_ms=round(total_time * 1000, 2),
        )

        metadata = Metadata(
            processing_time_ms=round(total_time * 1000, 2),
            model_versions=model_versions,
            processing_times=processing_times,
        )

        return OmniVisionResponse(
            request_id=ctx.request_id,
            status="success",
            data=data,
            explainability=explainability,
            metadata=metadata,
            retrieved_entries=ctx.retrieved_entries,
            stage_errors=ctx.stage_errors,
        )
