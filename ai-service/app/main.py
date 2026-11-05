import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.concurrency import run_in_threadpool

from app.api.routers.chat import router as chat_router
from app.api.routers.health import router as health_router
from app.api.routers.preference import router as preference_router
from app.api.routers.qdrant import router as qdrant_router
from app.api.routers.recommendation import router as recommendation_router
from app.core.config import settings
from app.core.device import resolve_device

logger = logging.getLogger(__name__)


def warmup() -> None:
    """Load the embedding model and touch Qdrant so the first user search is not slow.

    Failures are logged, never fatal: the service must still start if Qdrant is down.
    """
    started = time.perf_counter()
    try:
        from app.core.qdrant import get_qdrant_client
        from app.schemas.retrieval import MovieSearchRequest
        from app.services.retrieval import search_movies

        logger.info("Embedding device: %s", resolve_device(settings.embedding_device))
        get_qdrant_client().get_collection(settings.qdrant_collection)
        search_movies(MovieSearchRequest(query="warmup", mode="hybrid", limit=1))
        logger.info("Warmup finished in %.1fs", time.perf_counter() - started)
    except Exception:
        logger.exception("Warmup failed; the first request will load models lazily")


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.warmup_on_startup:
        await run_in_threadpool(warmup)
    yield

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

app.include_router(health_router)
app.include_router(qdrant_router)
app.include_router(chat_router)
app.include_router(preference_router)
app.include_router(recommendation_router)
