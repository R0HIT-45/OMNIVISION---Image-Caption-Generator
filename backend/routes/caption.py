"""Caption generation API routes — Phase 2 dual caption mode."""

import logging
import time

from fastapi import APIRouter, File, HTTPException, UploadFile

from backend.models.schemas import CaptionResponse
from backend.services.blip_service import caption_service
from backend.utils.config import PROJECT_ROOT
from backend.utils.image_utils import save_upload

logger = logging.getLogger(__name__)

router = APIRouter(tags=["caption"])


@router.post("/caption", response_model=CaptionResponse)
async def caption_image(file: UploadFile = File(...)) -> CaptionResponse:
    """Upload an image and generate short + detailed captions."""
    start = time.perf_counter()

    try:
        saved_path = await save_upload(file)
        captions = caption_service.generate_captions(saved_path)
    except HTTPException:
        raise
    except FileNotFoundError as exc:
        logger.error("Image file error: %s", exc)
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Caption generation failed")
        raise HTTPException(
            status_code=500,
            detail=f"Caption generation failed: {exc}",
        ) from exc

    processing_time = time.perf_counter() - start
    relative_path = saved_path.relative_to(PROJECT_ROOT).as_posix()

    return CaptionResponse(
        short_caption=captions["short_caption"],
        detailed_caption=captions["detailed_caption"],
        image_path=relative_path,
        processing_time=round(processing_time, 2),
    )
"""Caption generation API routes — Phase 2 dual caption mode."""

import logging
import time

from fastapi import APIRouter, File, HTTPException, UploadFile

from backend.models.schemas import CaptionResponse
from backend.services.blip_service import caption_service
from backend.utils.config import PROJECT_ROOT
from backend.utils.image_utils import save_upload

logger = logging.getLogger(__name__)

router = APIRouter(tags=["caption"])


@router.post("/caption", response_model=CaptionResponse)
async def caption_image(file: UploadFile = File(...)) -> CaptionResponse:
    """Upload an image and generate short + detailed captions."""
    start = time.perf_counter()

    try:
        saved_path = await save_upload(file)
        captions = caption_service.generate_captions(saved_path)
    except HTTPException:
        raise
    except FileNotFoundError as exc:
        logger.error("Image file error: %s", exc)
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Caption generation failed")
        raise HTTPException(
            status_code=500,
            detail=f"Caption generation failed: {exc}",
        ) from exc

    processing_time = time.perf_counter() - start
    relative_path = saved_path.relative_to(PROJECT_ROOT).as_posix()

    return CaptionResponse(
        short_caption=captions["short_caption"],
        detailed_caption=captions["detailed_caption"],
        image_path=relative_path,
        processing_time=round(processing_time, 2),
    )
"""Caption generation API routes."""

import logging
import time

from fastapi import APIRouter, File, HTTPException, UploadFile

from backend.models.schemas import CaptionResponse
from backend.services.blip_service import blip_service
from backend.utils.config import PROJECT_ROOT
from backend.utils.image_utils import save_upload

logger = logging.getLogger(__name__)

router = APIRouter(tags=["caption"])


@router.post("/caption", response_model=CaptionResponse)
async def caption_image(file: UploadFile = File(...)) -> CaptionResponse:
    """Upload an image and generate an English caption using BLIP-2."""
    start = time.perf_counter()

    try:
        saved_path = await save_upload(file)
        caption = blip_service.generate_caption(saved_path)
    except HTTPException:
        raise
    except FileNotFoundError as exc:
        logger.error("Image file error: %s", exc)
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Caption generation failed")
        raise HTTPException(
            status_code=500,
            detail=f"Caption generation failed: {exc}",
        ) from exc

    processing_time = time.perf_counter() - start
    relative_path = saved_path.relative_to(PROJECT_ROOT).as_posix()

    return CaptionResponse(
        caption=caption,
        image_path=relative_path,
        processing_time_seconds=round(processing_time, 2),
    )
