"""Seed demo accounts (one admin, one regular user).

Run from the backend folder after `alembic upgrade head`:
    .\\.venv\\Scripts\\python scripts/seed_demo_users.py

Idempotent: existing demo users are updated back to the values below.
Development only; refuses to run when ENVIRONMENT=production.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select  # noqa: E402

from app.constants.roles import RoleId  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.models import User  # noqa: E402
from app.modules.auth.auth_helpers import hash_password  # noqa: E402

DEMO_USERS = [
    {
        "email": "admin@speakwise.com",
        "password": "admin@123",
        "full_name": "Admin",
        "role_id": RoleId.ADMIN,
    },
    {
        "email": "raj@gmail.com",
        "password": "raj@123",
        "full_name": "Raj",
        "role_id": RoleId.USER,
    },
]


def seed_demo_users() -> None:
    if settings.ENVIRONMENT == "production":
        sys.exit("Refusing to seed demo users in production.")

    db = SessionLocal()

    try:
        for demo in DEMO_USERS:
            user = db.scalar(select(User).where(User.email == demo["email"]))
            action = "updated"

            if user is None:
                user = User(email=demo["email"])
                db.add(user)
                action = "created"

            user.full_name = demo["full_name"]
            user.role_id = demo["role_id"]
            user.hashed_password = hash_password(demo["password"])
            user.is_active = True

            print(f"{action}: {demo['email']} ({RoleId(demo['role_id']).name.lower()})")

        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_users()
