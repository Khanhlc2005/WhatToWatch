from fastapi import FastAPI

from app.api.routers.chat import router as chat_router
from app.api.routers.health import router as health_router
from app.api.routers.qdrant import router as qdrant_router
from app.api.routers.preference import router as preference_router
from app.api.routers.recommendation import router as recommendation_router
from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
)

app.include_router(health_router)
app.include_router(qdrant_router)
app.include_router(chat_router)
app.include_router(preference_router)
app.include_router(recommendation_router)
