from pydantic import BaseModel
from typing import Dict, List, Optional

class ExplainabilityData(BaseModel):
    top_retrieved_entity: Optional[str]
    retrieved_fact: Optional[str]
    similarity_score: float
    threshold_used: float
    grounding_applied: bool

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
    vision_ms: float
    retrieval_ms: float
    grounding_ms: float
    translation_ms: float
    audio_ms: float
    total_ms: float

class Metadata(BaseModel):
    processing_time_ms: float
    model_versions: ModelVersions
    processing_times: ProcessingTimes

class OmniVisionResponse(BaseModel):
    request_id: str
    status: str
    data: Optional[ResponseData]
    explainability: Optional[ExplainabilityData]
    metadata: Optional[Metadata]

# Internal context object used by the Orchestrator
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
    
    translations: Dict[str, str] = {}
    audio_paths: Dict[str, str] = {}
    
    errors: List[str] = []
    
    # Timings
    start_time: float = 0.0
    vision_time: float = 0.0
    retrieval_time: float = 0.0
    grounding_time: float = 0.0
    translation_time: float = 0.0
    audio_time: float = 0.0
