from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.utils.logger import setup_logger
from app.utils.exceptions import FraudDetectionException
import traceback

logger = setup_logger(__name__)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Custom middleware for error handling"""

    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except FraudDetectionException as exc:
            logger.error(f"FraudDetectionException: {str(exc)}")
            return JSONResponse(
                status_code=400,
                content={
                    "detail": str(exc),
                    "type": exc.__class__.__name__,
                },
            )
        except Exception as exc:
            logger.error(f"Unhandled exception: {str(exc)}\n{traceback.format_exc()}")
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "Internal server error",
                    "type": "InternalServerError",
                },
            )
