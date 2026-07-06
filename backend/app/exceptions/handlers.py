from fastapi import Request
from fastapi.responses import JSONResponse

class OmniVisionBaseException(Exception):
    """Base exception for all OmniVision errors."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

class CriticalAIException(OmniVisionBaseException):
    """Raised when a core AI model fails critically (e.g., OOM, failed to load)."""
    pass

class NonCriticalAIException(OmniVisionBaseException):
    """Raised when a non-critical AI model fails (e.g., Translation timeout)."""
    pass

class ValidationException(OmniVisionBaseException):
    """Raised for invalid input files or payloads."""
    pass

async def omnivision_exception_handler(request: Request, exc: OmniVisionBaseException):
    if isinstance(exc, CriticalAIException):
        status_code = 500
    elif isinstance(exc, ValidationException):
        status_code = 422
    else:
        status_code = 500

    return JSONResponse(
        status_code=status_code,
        content={
            "error": exc.__class__.__name__,
            "message": exc.message
        }
    )

def register_exception_handlers(app):
    app.add_exception_handler(OmniVisionBaseException, omnivision_exception_handler)
