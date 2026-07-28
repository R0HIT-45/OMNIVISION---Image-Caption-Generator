from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


def _to_camel(name: str) -> str:
    parts = name.split("_")
    return parts[0] + "".join(w.capitalize() for w in parts[1:])


# ── Domain models (internal) ──────────────────────────────────


class ExplainabilityData(BaseModel):
    top_retrieved_entity: Optional[str]
    retrieved_fact: Optional[str]
    similarity_score: float
    threshold_used: float
    grounding_applied: bool
    confidenceLabel: Optional[str] = None
    matchedEntity: Optional[str] = None
    reason: Optional[str] = None


class ResponseData(BaseModel):
    raw_caption: str
    final_caption: str
    translations: Dict[str, str]
    audio_urls: Dict[str, str]


class ModelVersions(BaseModel):
    caption: str
    embedding: str
    translation: str
    tts: str


class ProcessingTimes(BaseModel):
    caption_ms: float
    embedding_ms: float
    retrieval_ms: float
    grounding_ms: float
    translation_ms: float
    audio_ms: float
    total_ms: float


class Metadata(BaseModel):
    processing_time_ms: float
    model_versions: ModelVersions
    processing_times: ProcessingTimes


class StageError(BaseModel):
    stage: str
    reason: str


class OmniVisionResponse(BaseModel):
    request_id: str
    status: str
    data: Optional[ResponseData]
    explainability: Optional[ExplainabilityData]
    metadata: Optional[Metadata]
    retrieved_entries: List[Dict] = []
    stage_errors: List[StageError] = []


# ── Internal context used by the Orchestrator ─────────────────


class ProcessingContext(BaseModel):
    request_id: str
    image_path: Optional[str] = None
    validated: bool = False

    raw_caption: Optional[str] = None
    embedding: Optional[List[float]] = None
    retrieved_entries: List[Dict] = []

    grounding_applied: bool = False
    final_caption: Optional[str] = None
    top_entity: Optional[str] = None
    top_fact: Optional[str] = None
    top_score: float = 0.0
    confidenceLabel: Optional[str] = None
    matchedEntity: Optional[str] = None
    reason: Optional[str] = None

    translations: Dict[str, str] = {}
    audio_paths: Dict[str, str] = {}

    errors: List[str] = []
    stage_errors: List[StageError] = []

    # Timings (seconds)
    start_time: float = 0.0
    caption_time: float = 0.0
    embedding_time: float = 0.0
    retrieval_time: float = 0.0
    grounding_time: float = 0.0
    translation_time: float = 0.0
    audio_time: float = 0.0


# ── Frontend response models (camelCase JSON) ─────────────────


class PipelineStageFE(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    label: str
    model: str
    description: str
    latency_ms: float = Field(serialization_alias="latencyMs")
    status: str


class TranslationFE(BaseModel):
    code: str
    language: str
    caption: str


class RetrievedDocumentFE(BaseModel):
    id: str
    title: str
    score: float
    snippet: str


class ProcessResult(BaseModel):
    model_config = ConfigDict(alias_generator=_to_camel, populate_by_name=True)

    caption: str
    confidence: float
    tokens: int
    request_id: str = Field(serialization_alias="requestId")
    total_latency_ms: float = Field(serialization_alias="totalLatencyMs")
    confidence_label: Optional[str] = Field(serialization_alias="confidenceLabel", default=None)
    matched_entity: Optional[str] = Field(serialization_alias="matchedEntity", default=None)
    reason: Optional[str] = None
    stages: List[PipelineStageFE]
    translations: List[TranslationFE]
    retrieval: List[RetrievedDocumentFE]
