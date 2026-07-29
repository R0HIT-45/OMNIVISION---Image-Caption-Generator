"""Enterprise API endpoint tests for OmniVision v1.0.

Tests the /api/v1/process-image endpoint and health check.
All AI services are mocked — no model loading required.
"""

from io import BytesIO
from unittest.mock import patch, MagicMock, AsyncMock

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from backend.app.main import app

client = TestClient(app)

_VALID_JPEG = BytesIO()
Image.new("RGB", (1, 1), color="red").save(_VALID_JPEG, "JPEG")
_VALID_JPEG = _VALID_JPEG.getvalue()


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


def test_process_image_full_pipeline():
    """Full pipeline returns complete OmniVisionResponse."""
    import backend.app.orchestrator.request_coordinator as rc_mod

    # Reset singleton so new coordinator uses mocked services
    rc_mod._coordinator = None
    coordinator_module = "backend.app.orchestrator.request_coordinator"

    with (
        patch(f"{coordinator_module}.CaptionService") as mock_caption_cls,
        patch(f"{coordinator_module}.EmbeddingService") as mock_embedding_cls,
        patch(f"{coordinator_module}.RetrievalService") as mock_retrieval_cls,
        patch(f"{coordinator_module}.GroundingService") as mock_grounding_cls,
        patch(f"{coordinator_module}.TranslationService") as mock_translation_cls,
        patch(f"{coordinator_module}.TTSService") as mock_tts_cls,
        patch(f"{coordinator_module}.ImageService") as mock_image_cls,
    ):
        mock_image_inst = MagicMock()
        mock_image_inst.validate_and_preprocess = AsyncMock(return_value=MagicMock())
        mock_image_cls.return_value = mock_image_inst

        mock_caption_inst = MagicMock()
        mock_caption_inst.generate.return_value = "A photo of the Taj Mahal"
        mock_caption_cls.return_value = mock_caption_inst

        mock_embedding_inst = MagicMock()
        mock_embedding_inst.generate_embedding.return_value = [0.1] * 512
        mock_embedding_cls.return_value = mock_embedding_inst

        mock_retrieval_inst = MagicMock()
        mock_retrieval_inst.search.return_value = [
            {"entity": "Taj Mahal", "fact": "Built in 1632 by Shah Jahan", "score": 0.85}
        ]
        mock_retrieval_cls.return_value = mock_retrieval_inst

        mock_grounding_inst = MagicMock()
        mock_grounding_inst.evaluate_and_ground.return_value = {
            "final_caption": "A photo of the Taj Mahal Context: Built in 1632 by Shah Jahan",
            "grounding_applied": True,
            "top_entity": "Taj Mahal",
            "top_fact": "Built in 1632 by Shah Jahan",
            "top_score": 0.85,
        }
        mock_grounding_cls.return_value = mock_grounding_inst

        mock_translation_inst = MagicMock()
        mock_translation_inst.translate.return_value = {
            "hindi": "ताज महल की एक तस्वीर",
            "telugu": "తాజ్ మహల్ యొక్క ఫోటో",
        }
        mock_translation_cls.return_value = mock_translation_inst

        mock_tts_inst = MagicMock()
        mock_tts_inst.generate.return_value = {
            "english": "/static/audio/test_en.wav",
            "hindi": "/static/audio/test_hi.wav",
        }
        mock_tts_cls.return_value = mock_tts_inst

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
