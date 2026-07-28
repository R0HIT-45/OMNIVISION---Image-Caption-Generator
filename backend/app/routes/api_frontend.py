import logging

from fastapi import APIRouter, Depends, File, Request, UploadFile

from backend.app.orchestrator.frontend_transformer import transform_to_process_result
from backend.app.orchestrator.request_coordinator import RequestCoordinator, get_orchestrator
from backend.app.schemas.schemas import ProcessResult

logger = logging.getLogger("omnivision")
router = APIRouter()


@router.post("/process", response_model=ProcessResult)
async def process_image(
    request: Request,
    image: UploadFile = File(...),
    orchestrator: RequestCoordinator = Depends(get_orchestrator),
):
    request_id = getattr(request.state, "request_id", "unknown")
    logger.info(
        "POST /api/v1/process",
        extra={"request_id": request_id, "file": image.filename},
    )
    response = await orchestrator.process(image, request_id)
    return transform_to_process_result(response)
