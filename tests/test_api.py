"""Enterprise API endpoint tests for OmniVision v1.0.

Tests the /api/v1/process-image endpoint and health check.
All AI services are mocked — no model loading required.
"""

from io import BytesIO
from unittest.mock import patch, MagicMock, AsyncMock

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)

# Minimal valid JPEG bytes for testing
_VALID_JPEG = (
    b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
    b"\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c"
    b"\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c"
    b"\x1c $.\' \",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x0b\x08"
    b"\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01"
    b"\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03"
    b"\x04\x05\x06\x07\x08\t\n\x0b\xff\xc4\x00\xb5\x10\x00\x02\x01\x03\x03"
    b"\x02\x04\x03\x05\x05\x04\x04\x00\x00\x01}\x01\x02\x03\x00\x04\x11\x05"
    b"\x12!1A\x06\x13Qa\x07\"q\x142\x81\x91\xa1\x08#B\xb1\xc1\x15R\xd1\xf0"
    b"\x24\x33\x62\xf2\x82\t\n\x16\x17\x18\x19\x1a%&\'()*456789:CDEFGHIJ"
    b"STUVWXYZcdefghijstuvwxyz\x83\x84\x85\x86\x87\x88\x89\x8a\x92\x93\x94"
    b"\x95\x96\x97\x98\x99\x9a\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xb2\xb3"
    b"\xb4\xb5\xb6\xb7\xb8\xb9\xba\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xd2"
    b"\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9"
    b"\xea\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xff\xda\x00\x08\x01\x01"
    b"\x00\x00?\x00\xfb\xd5\xff\xd9"
)


def test_health_endpoint():
    """Health endpoint returns system status."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "version" in data


def test_process_image_rejects_empty_file():
    """Empty uploads are rejected."""
    response = client.post(
        "/api/v1/process-image",
        files={"file": ("test.jpg", BytesIO(b""), "image/jpeg")},
    )
    assert response.status_code in [400, 422, 415]


def test_process_image_rejects_invalid_type():
    """Non-image uploads are rejected."""
    response = client.post(
        "/api/v1/process-image",
        files={"file": ("test.txt", BytesIO(b"not an image"), "text/plain")},
    )
    assert response.status_code in [400, 415]


@patch("backend.app.orchestrator.request_coordinator.CaptionService")
@patch("backend.app.orchestrator.request_coordinator.EmbeddingService")
@patch("backend.app.orchestrator.request_coordinator.RetrievalService")
@patch("backend.app.orchestrator.request_coordinator.GroundingService")
@patch("backend.app.orchestrator.request_coordinator.TranslationService")
@patch("backend.app.orchestrator.request_coordinator.TTSService")
def test_process_image_full_pipeline(
    mock_tts, mock_translation, mock_grounding,
    mock_retrieval, mock_embedding, mock_caption,
):
    """Full pipeline returns complete OmniVisionResponse."""
    # Mock image service to return a PIL image
    mock_image_instance = MagicMock()
    mock_image_instance.validate_and_preprocess = AsyncMock(return_value=MagicMock())

    # Mock caption service
    mock_caption_instance = MagicMock()
    mock_caption_instance.generate.return_value = "A photo of the Taj Mahal"
    mock_caption.return_value = mock_caption_instance

    # Mock embedding service
    mock_embedding_instance = MagicMock()
    mock_embedding_instance.generate_embedding.return_value = [0.1] * 512
    mock_embedding.return_value = mock_embedding_instance

    # Mock retrieval service
    mock_retrieval_instance = MagicMock()
    mock_retrieval_instance.search.return_value = [
        {"entity": "Taj Mahal", "fact": "Built in 1632 by Shah Jahan", "score": 0.85}
    ]
    mock_retrieval.return_value = mock_retrieval_instance

    # Mock grounding service
    mock_grounding_instance = MagicMock()
    mock_grounding_instance.evaluate_and_ground.return_value = {
        "final_caption": "A photo of the Taj Mahal Context: Built in 1632 by Shah Jahan",
        "grounding_applied": True,
        "top_entity": "Taj Mahal",
        "top_fact": "Built in 1632 by Shah Jahan",
        "top_score": 0.85,
    }
    mock_grounding.return_value = mock_grounding_instance

    # Mock translation service
    mock_translation_instance = MagicMock()
    mock_translation_instance.translate.return_value = {
        "hindi": "ताज महल की एक तस्वीर",
        "telugu": "తాజ్ మహల్ యొక్క ఫోటో",
    }
    mock_translation.return_value = mock_translation_instance

    # Mock TTS service
    mock_tts_instance = MagicMock()
    mock_tts_instance.generate.return_value = {
        "english": "/static/audio/test_en.wav",
        "hindi": "/static/audio/test_hi.wav",
    }
    mock_tts.return_value = mock_tts_instance

    with patch("backend.app.orchestrator.request_coordinator.ImageService", return_value=mock_image_instance):
        response = client.post(
            "/api/v1/process-image",
            files={"file": ("taj_mahal.jpg", BytesIO(_VALID_JPEG), "image/jpeg")},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["data"]["raw_caption"] == "A photo of the Taj Mahal"
    assert data["data"]["final_caption"] is not None
    assert "request_id" in data
    assert "metadata" in data
    assert "processing_times" in data["metadata"]
