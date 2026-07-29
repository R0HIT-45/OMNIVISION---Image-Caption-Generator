"""Tests for the Request Coordinator (Pipeline Orchestrator).

Verifies that the pipeline stages execute in correct order,
graceful degradation works, and timing is tracked.
"""

import time
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from backend.app.schemas.schemas import ProcessingContext


class TestProcessingContext:
    """Test the ProcessingContext schema."""

    def test_default_values(self):
        """Context initializes with safe defaults."""
        ctx = ProcessingContext(request_id="test-123")

        assert ctx.request_id == "test-123"
        assert ctx.validated is False
        assert ctx.grounding_applied is False
        assert ctx.translations == {}
        assert ctx.audio_paths == {}
        assert ctx.errors == []

    def test_timing_fields(self):
        """Context tracks per-stage timing."""
        ctx = ProcessingContext(request_id="test-123")
        ctx.caption_time = 1.5
        ctx.retrieval_time = 0.1

        assert ctx.caption_time == 1.5
        assert ctx.retrieval_time == 0.1


class TestPipelineOrdering:
    """Test that pipeline stages execute in the correct order."""

    @pytest.mark.asyncio
    async def test_pipeline_stages_called_in_order(self):
        """Verify the 6 pipeline stages execute sequentially."""
        call_order = []

        with patch("backend.app.orchestrator.request_coordinator.ImageService") as mock_img, \
             patch("backend.app.orchestrator.request_coordinator.CaptionService") as mock_cap, \
             patch("backend.app.orchestrator.request_coordinator.EmbeddingService") as mock_emb, \
             patch("backend.app.orchestrator.request_coordinator.RetrievalService") as mock_ret, \
             patch("backend.app.orchestrator.request_coordinator.GroundingService") as mock_grd, \
             patch("backend.app.orchestrator.request_coordinator.TranslationService") as mock_trn, \
             patch("backend.app.orchestrator.request_coordinator.TTSService") as mock_tts, \
             patch("backend.app.orchestrator.request_coordinator.ResponseBuilder") as mock_rpb:

            # Track calls
            mock_img_inst = MagicMock()
            mock_img_inst.validate_and_preprocess = AsyncMock(return_value=MagicMock())
            mock_img.return_value = mock_img_inst

            mock_cap_inst = MagicMock()
            mock_cap_inst.generate.side_effect = lambda img, detailed=False, request_id="": (call_order.append("caption") or "caption result")
            mock_cap.return_value = mock_cap_inst

            mock_emb_inst = MagicMock()
            mock_emb_inst.generate_embedding.side_effect = lambda img, request_id="": (call_order.append("embedding") or [0.1] * 512)
            mock_emb.return_value = mock_emb_inst

            mock_ret_inst = MagicMock()
            mock_ret_inst.search.side_effect = lambda vec, k=1: (call_order.append("retrieval") or [])
            mock_ret.return_value = mock_ret_inst

            mock_grd_inst = MagicMock()
            mock_grd_inst.evaluate_and_ground.side_effect = lambda cap, entries: (call_order.append("grounding") or {
                "final_caption": cap, "grounding_applied": False,
                "top_entity": None, "top_fact": None, "top_score": 0.0
            })
            mock_grd.return_value = mock_grd_inst

            mock_trn_inst = MagicMock()
            mock_trn_inst.translate.side_effect = lambda text: (call_order.append("translation") or {})
            mock_trn.return_value = mock_trn_inst

            mock_tts_inst = MagicMock()
            mock_tts_inst.generate.side_effect = lambda texts, request_id: (call_order.append("tts") or {})
            mock_tts.return_value = mock_tts_inst

            mock_rpb_inst = MagicMock()
            mock_rpb_inst.build_success.return_value = {"status": "success"}
            mock_rpb.return_value = mock_rpb_inst

            from backend.app.orchestrator.request_coordinator import RequestCoordinator
            coordinator = RequestCoordinator()

            mock_file = MagicMock()
            mock_file.content_type = "image/jpeg"

            await coordinator.process(mock_file, "test-req-001")

            # Verify order: caption and embedding are vision stage, then retrieval, grounding, translation, tts
            assert call_order[0] == "caption"
            assert call_order[1] == "embedding"
            assert call_order[2] == "retrieval"
            assert call_order[3] == "grounding"
            assert call_order[4] == "translation"
            assert call_order[5] == "tts"

    @pytest.mark.asyncio
    async def test_translation_failure_does_not_crash_pipeline(self):
        """If translation fails, pipeline continues with TTS using English only."""
        with patch("backend.app.orchestrator.request_coordinator.ImageService") as mock_img, \
             patch("backend.app.orchestrator.request_coordinator.CaptionService") as mock_cap, \
             patch("backend.app.orchestrator.request_coordinator.EmbeddingService") as mock_emb, \
             patch("backend.app.orchestrator.request_coordinator.RetrievalService") as mock_ret, \
             patch("backend.app.orchestrator.request_coordinator.GroundingService") as mock_grd, \
             patch("backend.app.orchestrator.request_coordinator.TranslationService") as mock_trn, \
             patch("backend.app.orchestrator.request_coordinator.TTSService") as mock_tts, \
             patch("backend.app.orchestrator.request_coordinator.ResponseBuilder") as mock_rpb:

            mock_img_inst = MagicMock()
            mock_img_inst.validate_and_preprocess = AsyncMock(return_value=MagicMock())
            mock_img.return_value = mock_img_inst

            mock_cap_inst = MagicMock()
            mock_cap_inst.generate.return_value = "A test caption"
            mock_cap.return_value = mock_cap_inst

            mock_emb_inst = MagicMock()
            mock_emb_inst.generate_embedding.return_value = [0.1] * 512
            mock_emb.return_value = mock_emb_inst

            mock_ret_inst = MagicMock()
            mock_ret_inst.search.return_value = []
            mock_ret.return_value = mock_ret_inst

            mock_grd_inst = MagicMock()
            mock_grd_inst.evaluate_and_ground.return_value = {
                "final_caption": "A test caption", "grounding_applied": False,
                "top_entity": None, "top_fact": None, "top_score": 0.0
            }
            mock_grd.return_value = mock_grd_inst

            # Translation FAILS
            from backend.app.exceptions.handlers import TranslationException
            mock_trn_inst = MagicMock()
            mock_trn_inst.translate.side_effect = TranslationException("Model unavailable")
            mock_trn.return_value = mock_trn_inst

            mock_tts_inst = MagicMock()
            mock_tts_inst.generate.return_value = {}
            mock_tts.return_value = mock_tts_inst

            mock_rpb_inst = MagicMock()
            mock_rpb_inst.build_success.return_value = {"status": "success", "data": {}}
            mock_rpb.return_value = mock_rpb_inst

            from backend.app.orchestrator.request_coordinator import RequestCoordinator
            coordinator = RequestCoordinator()

            mock_file = MagicMock()
            mock_file.content_type = "image/jpeg"

            # Should NOT raise — translation failure is graceful
            result = await coordinator.process(mock_file, "test-req-002")
            assert result is not None
