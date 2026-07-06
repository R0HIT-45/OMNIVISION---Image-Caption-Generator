"""Image validation and upload utilities."""

import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile

from backend.utils.config import settings

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/jpg"}


def validate_upload(file: UploadFile) -> None:
    """Validate uploaded file type and size."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    extension = Path(file.filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{extension}'. Allowed: JPG, JPEG, PNG.",
        )

    if file.content_type and file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported content type '{file.content_type}'.",
        )


async def save_upload(file: UploadFile) -> Path:
    """Validate and persist an uploaded image; return saved path."""
    validate_upload(file)

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    if len(content) > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File exceeds maximum size of {settings.max_upload_size_mb} MB.",
        )

    extension = Path(file.filename).suffix.lower()
    saved_name = f"{uuid.uuid4()}{extension}"
    saved_path = settings.upload_path / saved_name

    saved_path.write_bytes(content)
    return saved_path
