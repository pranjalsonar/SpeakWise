"""Seed demo students and talk sessions so the admin dashboard has data.

Run from the backend folder after `alembic upgrade head`:
    .\\.venv\\Scripts\\python scripts/seed_demo_sessions.py

Creates ~24 students with emails ending in @demo.speakwise.com and ~12 weeks of
sessions (categories, durations, scores). Re-running replaces all
@demo.speakwise.com users and their sessions; other accounts are untouched.
Development only; refuses to run when ENVIRONMENT=production.
"""
import random
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import delete, func, select  # noqa: E402

from app.constants.roles import RoleId  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.models import TalkSession, TopicCategory, User  # noqa: E402
from app.modules.auth.auth_helpers import hash_password  # noqa: E402

DEMO_DOMAIN = "demo.speakwise.com"
DEMO_PASSWORD = "demo@123"

NAMES = [
    "Priya Sharma", "Arjun Mehta", "Mei Tanaka", "Hannah Weber", "Sara Okafor", "Lucas Moreau",
    "Aisha Khan", "Diego Alvarez", "Nina Patel", "Tom Becker", "Yuki Sato", "Fatima Zahra",
    "Rohan Gupta", "Emma Wilson", "Kwame Mensah", "Sofia Rossi", "Ishaan Rao", "Chloe Martin",
    "Omar Haddad", "Ananya Iyer", "Liam O'Brien", "Zara Ahmed", "Mateo Silva", "Kavya Nair",
]

# Category name -> (weight, topics). Weights give the dashboard's category split.
TOPICS = {
    "Technology": (28, [
        "Should AI tutors replace homework help?",
        "Are smartphones making us less focused?",
        "Self-driving cars: ready for city streets?",
        "Should coding be taught in every school?",
    ]),
    "Business": (24, [
        "The case for a four-day work week",
        "Remote work vs. office culture",
        "Is the gig economy good for workers?",
        "Should companies publish salaries openly?",
    ]),
    "Society": (19, [
        "Is social media making us lonelier?",
        "Should voting be compulsory?",
        "Are exams the best way to measure learning?",
    ]),
    "Environment": (16, [
        "Fast fashion and its environmental cost",
        "Should single-use plastics be banned?",
        "Can cities run fully on renewable energy?",
    ]),
    "Science": (13, [
        "CRISPR and the ethics of gene editing",
        "Space exploration: worth the cost?",
        "Should we bring back extinct species?",
    ]),
}

# Sessions per week, oldest first; the last entry is the current week (scaled by days elapsed).
SESSIONS_PER_WEEK = [8, 10, 9, 12, 14, 17, 16, 19, 22, 24, 27, 30]


def seed_demo_sessions() -> None:
    if settings.ENVIRONMENT == "production":
        sys.exit("Refusing to seed demo data in production.")

    rng = random.Random(42)
    now = datetime.now(timezone.utc)
    db = SessionLocal()

    try:
        removed = db.execute(delete(User).where(User.email.like(f"%@{DEMO_DOMAIN}"))).rowcount

        categories = {c.name: c.id for c in db.scalars(select(TopicCategory))}
        missing = set(TOPICS) - set(categories)
        if missing:
            sys.exit(f"Missing topic categories {missing}. Run `alembic upgrade head` first.")

        users = _create_users(db, rng, now)
        sessions = _create_sessions(rng, now, users, categories)
        db.add_all(sessions)
        db.commit()

        total = db.scalar(select(func.count()).select_from(TalkSession))
        print(f"removed {removed} old demo users (and their sessions)")
        print(f"created {len(users)} demo users (password: {DEMO_PASSWORD})")
        print(f"created {len(sessions)} demo sessions ({total} sessions in the database)")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def _create_users(db, rng: random.Random, now: datetime) -> list[User]:
    password_hash = hash_password(DEMO_PASSWORD)  # hashed once; bcrypt is slow on purpose
    users = []

    for index, name in enumerate(NAMES):
        # Most joined 2-5 months ago; the last few joined this month.
        days_ago = rng.randint(3, 25) if index >= len(NAMES) - 5 else rng.randint(60, 150)
        joined = now - timedelta(days=days_ago, hours=rng.randint(0, 23))
        email = f"{name.lower().replace(' ', '.').replace(chr(39), '')}@{DEMO_DOMAIN}"

        users.append(
            User(
                email=email,
                full_name=name,
                hashed_password=password_hash,
                role_id=RoleId.USER,
                is_active=rng.random() > 0.25,  # ~75% active
                created_at=joined,
                updated_at=joined,
            )
        )

    db.add_all(users)
    db.flush()  # assign ids
    return users


def _create_sessions(
    rng: random.Random, now: datetime, users: list[User], categories: dict[str, int]
) -> list[TalkSession]:
    names = list(TOPICS)
    weights = [TOPICS[name][0] for name in names]
    week_start = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    sessions = []

    for weeks_back, planned in enumerate(reversed(SESSIONS_PER_WEEK)):
        start = week_start - timedelta(weeks=weeks_back)
        # The current week is only partly over.
        span = min(timedelta(weeks=1), now - start)
        count = round(planned * span / timedelta(weeks=1)) if weeks_back == 0 else planned
        week_index = len(SESSIONS_PER_WEEK) - 1 - weeks_back  # 0 = oldest

        for _ in range(count):
            created = start + span * rng.random()
            eligible = [u for u in users if u.created_at <= created]
            if not eligible:
                continue

            category = rng.choices(names, weights)[0]
            minutes = rng.choices([1, 3, 5], [3, 5, 2])[0]
            # Scores improve a little each week.
            score = max(40.0, min(98.0, rng.gauss(64 + week_index * 1.2, 8)))

            sessions.append(
                TalkSession(
                    user_id=rng.choice(eligible).id,
                    topic_title=rng.choice(TOPICS[category][1]),
                    category_id=categories[category],
                    duration_seconds=int(minutes * 60 * rng.uniform(0.75, 1.0)),
                    score=Decimal(f"{score:.1f}"),
                    created_at=created,
                    updated_at=created,
                )
            )

    # The newest two are still being analysed (no score yet).
    for session in sorted(sessions, key=lambda s: s.created_at)[-2:]:
        session.score = None

    return sessions


if __name__ == "__main__":
    seed_demo_sessions()
