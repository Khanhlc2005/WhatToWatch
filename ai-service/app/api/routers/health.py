from fastapi import APIRouter

from app.core.config import settings


router = APIRouter(
    prefix="/internal",
    tags=["Internal"],
)


@router.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
    }