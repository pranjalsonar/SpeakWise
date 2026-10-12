from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models import User


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(
        select(User).options(joinedload(User.role)).where(User.email == email.strip().lower())
    )


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.scalar(select(User).options(joinedload(User.role)).where(User.id == user_id))


def record_login(db: Session, user: User) -> None:
    user.last_login_at = func.now()
    db.commit()
    db.refresh(user)
