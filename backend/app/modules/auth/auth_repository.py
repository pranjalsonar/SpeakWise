from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import User


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(
        select(User).options(joinedload(User.role)).where(User.email == email.strip().lower())
    )


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.scalar(select(User).options(joinedload(User.role)).where(User.id == user_id))
