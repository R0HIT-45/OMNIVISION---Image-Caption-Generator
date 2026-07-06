"""Pydantic request/response schemas."""

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "OmniVision API"
    phase: str = "2"


class CaptionResponse(BaseModel):
    """Phase 2 dual-caption response."""

    short_caption: str = Field(
        ..., description="One concise sentence describing the image"
    )
    detailed_caption: str = Field(
        ...,
        description="Detailed description including objects, actions, surroundings and context",
    )
    image_path: str = Field(..., description="Relative path to saved upload")
    processing_time: float = Field(..., ge=0, description="Total inference time in seconds")
