import logging

from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger("omnivision")


class OmniVisionException(Exception):
    """Base exception for all OmniVision errors."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class ValidationException(OmniVisionException):
    """Raised for invalid input (HTTP 400)."""

    pass


class UnsupportedMediaTypeException(OmniVisionException):
    """Raised when file format is not supported (HTTP 415)."""

    pass


class ModelLoadException(OmniVisionException):
    """Raised when an AI model fails to load or runs out of memory (HTTP 503)."""

    pass


class RetrievalException(OmniVisionException):
    """Raised when the FAISS retrieval pipeline fails (HTTP 500)."""

    pass


class TranslationException(OmniVisionException):
    """Raised when the IndicTrans2 translation fails (HTTP 500)."""

    pass


class TTSException(OmniVisionException):
    """Raised when the XTTS audio synthesis fails (HTTP 500)."""

    pass


class CriticalAIException(OmniVisionException):
    """Raised for general critical AI failures (HTTP 500)."""

    pass


async def omnivision_exception_handler(request: Request, exc: OmniVisionException):
    # Log the exception explicitly before responding
    logger.error(f"API Exception: {exc.__class__.__name__} - {exc.message}")

    if isinstance(exc, ValidationException):
        status_code = 400
    elif isinstance(exc, UnsupportedMediaTypeException):
        status_code = 415
    elif isinstance(exc, ModelLoadException):
        status_code = 503
    elif isinstance(
        exc, (RetrievalException, TranslationException, TTSException, CriticalAIException)
    ):
        status_code = 500
    else:
        status_code = 500

    return JSONResponse(
        status_code=status_code, content={"error": exc.__class__.__name__, "message": exc.message}
    )


def register_exception_handlers(app):
    app.add_exception_handler(OmniVisionException, omnivision_exception_handler)
