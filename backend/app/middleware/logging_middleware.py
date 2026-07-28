import logging
import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("omnivision")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        start_time = time.time()
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={"request_id": request_id, "phase": "request_start", "success": True},
        )

        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            latency_ms = round(process_time * 1000, 2)

            logger.info(
                f"Request completed: {request.method} {request.url.path} - Status: {response.status_code}",
                extra={
                    "request_id": request_id,
                    "phase": "request_end",
                    "latency_ms": latency_ms,
                    "success": True,
                },
            )

            response.headers["X-Request-ID"] = request_id
            return response

        except Exception as e:
            process_time = time.time() - start_time
            latency_ms = round(process_time * 1000, 2)
            logger.error(
                f"Request failed: {request.method} {request.url.path} - Error: {str(e)}",
                extra={
                    "request_id": request_id,
                    "phase": "request_end",
                    "latency_ms": latency_ms,
                    "success": False,
                },
            )
            raise e
