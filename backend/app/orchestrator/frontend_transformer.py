import logging
from typing import List

from backend.app.config.settings import get_settings
from backend.app.schemas.schemas import (
    OmniVisionResponse,
    PipelineStageFE,
    ProcessResult,
    RetrievedDocumentFE,
    TranslationFE,
)

logger = logging.getLogger("omnivision")
settings = get_settings()

LANG_DISPLAY = {
    "hindi": ("hi", "\u0939\u093f\u0928\u094d\u0926\u0940"),
    "telugu": ("te", "\u0c24\u0c46\u0c32\u0c41\u0c17\u0c41"),
}

STAGE_META = {
    "vision": (
        "Vision Encoder",
        "Extracts visual features and detects salient regions in the source image.",
    ),
    "embedding": (
        "Embedding",
        "Projects visual features into the shared multimodal vector space.",
    ),
    "retrieval": (
        "FAISS Retrieval",
        "Retrieves the nearest knowledge-base passages for grounded context.",
    ),
    "grounding": (
        "Grounded Generation",
        "Generates the caption conditioned on retrieved evidence and confidence scoring.",
    ),
    "translation": (
        "Translation",
        "Produces multilingual caption variants with terminology preservation.",
    ),
    "speech": (
        "Speech Synthesis",
        "Renders natural narration audio for the selected language.",
    ),
}

STAGE_ORDER = ["vision", "embedding", "retrieval", "grounding", "translation", "speech"]


def _model_label(stage_id: str, times) -> str:
    if stage_id == "vision":
        return f"{settings.BLIP_MODEL}"
    if stage_id == "embedding":
        return f"{settings.CLIP_MODEL}"
    if stage_id == "retrieval":
        return "FAISS IndexFlatIP"
    if stage_id == "grounding":
        return f"Confidence Gate \u00b7 {settings.GROUNDING_SIMILARITY_THRESHOLD}"
    if stage_id == "translation":
        return f"{settings.TRANSLATION_MODEL}"
    if stage_id == "speech":
        return f"{settings.TTS_MODEL}"
    return stage_id


def _stage_latency(stage_id: str, times) -> float:
    mapping = {
        "vision": times.caption_ms,
        "embedding": times.embedding_ms,
        "retrieval": times.retrieval_ms,
        "grounding": times.grounding_ms,
        "translation": times.translation_ms,
        "speech": times.audio_ms,
    }
    return mapping.get(stage_id, 0.0)


def transform_to_process_result(response: OmniVisionResponse) -> ProcessResult:
    caption = response.data.final_caption if response.data else ""
    times = response.metadata.processing_times if response.metadata else None

    # Build stages
    stages: List[PipelineStageFE] = []
    for stage_id in STAGE_ORDER:
        label, description = STAGE_META[stage_id]
        failed = any(e.stage == stage_id for e in response.stage_errors)
        stages.append(
            PipelineStageFE(
                id=stage_id,
                label=label,
                model=_model_label(stage_id, times),
                description=description,
                latency_ms=_stage_latency(stage_id, times) if times else 0.0,
                status="failed" if failed else "complete",
            )
        )

    # Build translations (English always first)
    translations: List[TranslationFE] = [
        TranslationFE(code="en", language="English", caption=caption)
    ]
    if response.data and response.data.translations:
        for lang_key, translated_text in response.data.translations.items():
            code_info = LANG_DISPLAY.get(lang_key)
            if code_info:
                translations.append(
                    TranslationFE(
                        code=code_info[0],
                        language=code_info[1],
                        caption=translated_text,
                    )
                )

    # Build retrieval
    retrieval: List[RetrievedDocumentFE] = []
    for i, entry in enumerate(response.retrieved_entries):
        retrieval.append(
            RetrievedDocumentFE(
                id=f"kb-{i:04d}",
                title=entry.get("entity", "Unknown"),
                score=entry.get("score", 0.0),
                snippet=entry.get("fact", ""),
            )
        )

    confidence = response.explainability.similarity_score if response.explainability else 0.0
    token_count = len(caption.split()) if caption else 0

    return ProcessResult(
        caption=caption,
        confidence=confidence,
        tokens=token_count,
        request_id=f"ovn_{response.request_id}",
        total_latency_ms=times.total_ms if times else 0.0,
        confidence_label=(
            response.explainability.confidenceLabel if response.explainability else None
        ),
        matched_entity=response.explainability.matchedEntity if response.explainability else None,
        reason=response.explainability.reason if response.explainability else None,
        stages=stages,
        translations=translations,
        retrieval=retrieval,
    )
