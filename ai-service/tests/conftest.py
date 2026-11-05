from app.core.config import settings

# Tests must not load BGE-M3 / hit Qdrant during app startup.
settings.warmup_on_startup = False
