from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.middleware.auth_middleware import get_current_user
from app.middleware.jwt_handler import TokenPayload
from app.modules.reading import reading_service
from app.modules.reading.reading_schemas import ReadingMaterialResponse

router = APIRouter(prefix="/topics", tags=["Reading material"])


@router.get("/{topic_id}/reading-material", response_model=ReadingMaterialResponse)
def get_reading_material(
    topic_id: int,
    current_user: TokenPayload = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Reading material for the Prepare step: a version this user hasn't recorded a talk with.

    Stable until the user records (reloading returns the same version). Send `id` back when
    the talk session is saved, so this version isn't served to them again.
    """
    return reading_service.get_reading_material(db, current_user, topic_id)
