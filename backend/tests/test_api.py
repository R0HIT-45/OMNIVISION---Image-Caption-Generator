import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# We need to mock settings and model manager before importing main
import sys
import os

from backend.app.main import app
from backend.app.schemas.schemas import ProcessResult

client = TestClient(app)

def test_health_check():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"

@pytest.fixture
def mock_pipeline():
    with patch("backend.app.orchestrator.request_coordinator.RequestCoordinator.process") as mock_process:
        yield mock_process

def test_process_success(mock_pipeline):
    from backend.app.schemas.schemas import OmniVisionResponse, ResponseData, ExplainabilityData, Metadata, ModelVersions, ProcessingTimes
    
    mock_pipeline.return_value = OmniVisionResponse(
        request_id="test-123",
        status="success",
        data=ResponseData(
            raw_caption="A test caption",
            final_caption="A test caption Context: Test fact",
            translations={"hindi": "टेस्ट", "telugu": "టెస్ట్"},
            audio_urls={}
        ),
        explainability=ExplainabilityData(
            top_retrieved_entity="Test Entity",
            retrieved_fact="Test fact",
            similarity_score=0.85,
            threshold_used=0.75,
            grounding_applied=True,
            confidenceLabel="High",
            matchedEntity="Test Entity",
            reason="Strong match"
        ),
        metadata=Metadata(
            processing_time_ms=1000.0,
            model_versions=ModelVersions(caption="test", embedding="test", translation="test", tts="test"),
            processing_times=ProcessingTimes(caption_ms=100, embedding_ms=100, retrieval_ms=100, grounding_ms=100, translation_ms=100, audio_ms=100, total_ms=1000)
        )
    )

    with open("scripts/test_images/noise.jpg", "rb") as f:
        response = client.post("/api/v1/process", files={"file": ("test.jpg", f, "image/jpeg")})
    
    assert response.status_code == 200
    data = response.json()
    assert data["caption"] == "A test caption Context: Test fact"
    assert data["confidenceLabel"] == "High"
    assert data["translations"][1]["code"] == "hi"

def test_process_invalid_file():
    # Empty file
    response = client.post("/api/v1/process", files={"file": ("test.txt", b"", "text/plain")})
    assert response.status_code == 400

