from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.middleware.error_handler import ErrorHandlingMiddleware
from app.routers import fraud_router, health_router, transactions_router
from app.utils.logger import setup_logger

# Initialize logger
logger = setup_logger(__name__)

# Initialize FastAPI app
settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    description="Production-ready fraud detection system using graph analysis",
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_credentials,
    allow_methods=settings.cors_methods,
    allow_headers=settings.cors_headers,
)

# Add error handling middleware
app.add_middleware(ErrorHandlingMiddleware)


# Include routers
app.include_router(health_router)
app.include_router(fraud_router)
app.include_router(transactions_router)


@app.on_event("startup")
async def startup_event():
    """Execute on application startup"""
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"Log level: {settings.log_level}")


@app.on_event("shutdown")
async def shutdown_event():
    """Execute on application shutdown"""
    logger.info(f"Shutting down {settings.app_name}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower(),
    )
