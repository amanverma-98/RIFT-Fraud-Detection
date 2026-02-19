from fastapi import APIRouter
from app.models.schemas import HealthCheckResponse
from app.config import get_settings

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """
    Health check endpoint

    Returns application status and version
    """
    settings = get_settings()
    return HealthCheckResponse(
        status="healthy",
        version=settings.app_version,
        app_name=settings.app_name,
    )


@router.get("/")
async def root():
    """Root endpoint"""
    settings = get_settings()
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
    }
