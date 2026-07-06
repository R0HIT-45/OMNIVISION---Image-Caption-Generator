from fastapi import APIRouter, UploadFile, File, Depends, Request
from app.schemas.schemas import OmniVisionResponse
from app.orchestrator.request_coordinator import RequestCoordinator, get_orchestrator
from app.exceptions.handlers import ValidationException
import logging

logger = logging.getLogger("omnivision")
router = APIRouter()

@router.post("/process-image", response_model=OmniVisionResponse)
async def process_image_route(
    request: Request,
    file: UploadFile = File(...),
    orchestrator: RequestCoordinator = Depends(get_orchestrator)
):
    request_id = getattr(request.state, "request_id", "unknown_id")
    
    if not file:
        raise ValidationException("No file provided.")
        
    logger.info(f"Received process-image request [ID: {request_id}] for file: {file.filename}")
    
    # The orchestrator is fully asynchronous and handles its own background threading
    response = await orchestrator.process(file, request_id)
    return response
