import logging

from fastapi import APIRouter, HTTPException

from app.schemas.preference import PreferenceResponse, PreferenceSnapshot
from app.services.preference import rebuild_preference

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/internal/preferences", tags=["Preferences"])


@router.put("/snapshot", response_model=PreferenceResponse)
def replace_preference(snapshot: PreferenceSnapshot) -> PreferenceResponse:
    try:
        return rebuild_preference(snapshot)
    except Exception as exc:
        logger.exception("Preference rebuild failed")
        raise HTTPException(status_code=503, detail="Preference update is unavailable") from exc
