from app.routers.fraud_detection import router as fraud_router
from app.routers.health import router as health_router
from app.routers.transactions import router as transactions_router

__all__ = ["fraud_router", "health_router", "transactions_router"]
