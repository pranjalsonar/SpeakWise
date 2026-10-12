from datetime import datetime
from typing import Any

from sqlalchemy import func, select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session, selectinload, undefer

from app.models import ReadingMaterial, TalkSession, WikiArticle

# Namespace for pg_advisory_xact_lock(namespace, topic_id): one builder per topic at a time.
_BUILD_LOCK_NAMESPACE = 7301


def lock_topic_for_build(db: Session, topic_id: int) -> None:
    """Block until no other transaction is building reading material for this topic.

    Released automatically at commit/rollback.
    """
    db.execute(text("SELECT pg_advisory_xact_lock(:ns, :id)"), {"ns": _BUILD_LOCK_NAMESPACE, "id": topic_id})


# ---- reading materials ----

def list_versions(db: Session, topic_id: int) -> list[ReadingMaterial]:
    """All versions of a topic (content not loaded), oldest first."""
    return list(
        db.scalars(
            select(ReadingMaterial)
            .where(ReadingMaterial.topic_id == topic_id)
            .order_by(ReadingMaterial.version_no)
        )
    )


def get_material(db: Session, material_id: int) -> ReadingMaterial | None:
    return db.scalar(
        select(ReadingMaterial)
        .options(undefer(ReadingMaterial.content), selectinload(ReadingMaterial.sources))
        .where(ReadingMaterial.id == material_id)
    )


def recorded_versions(db: Session, user_id: int, topic_id: int) -> dict[int, datetime]:
    """{reading_material_id: when this user last recorded a talk with it} for the topic."""
    rows = db.execute(
        select(TalkSession.reading_material_id, func.max(TalkSession.created_at))
        .join(ReadingMaterial, ReadingMaterial.id == TalkSession.reading_material_id)
        .where(TalkSession.user_id == user_id, ReadingMaterial.topic_id == topic_id)
        .group_by(TalkSession.reading_material_id)
    ).all()
    return {material_id: last for material_id, last in rows}


def add_material(db: Session, material: ReadingMaterial) -> ReadingMaterial:
    db.add(material)
    db.flush()
    return material


# ---- wiki article cache ----

def get_article_by_title(db: Session, lang: str, title: str) -> WikiArticle | None:
    return db.scalar(
        select(WikiArticle)
        .options(undefer(WikiArticle.sections))
        .where(WikiArticle.lang == lang, WikiArticle.title == title)
    )


def get_article(db: Session, lang: str, page_id: int) -> WikiArticle | None:
    return db.scalar(
        select(WikiArticle)
        .options(undefer(WikiArticle.sections))
        .where(WikiArticle.lang == lang, WikiArticle.page_id == page_id)
    )


def upsert_article(db: Session, values: dict[str, Any]) -> WikiArticle:
    """Insert or refresh a cached article (unique on lang + page_id)."""
    statement = insert(WikiArticle).values(**values, fetched_at=func.now())
    statement = statement.on_conflict_do_update(
        index_elements=[WikiArticle.lang, WikiArticle.page_id],
        set_={
            "title": statement.excluded.title,
            "revision_id": statement.excluded.revision_id,
            "url": statement.excluded.url,
            "description": statement.excluded.description,
            "sections": statement.excluded.sections,
            "word_count": statement.excluded.word_count,
            "fetched_at": func.now(),
        },
    )
    db.execute(statement)
    # populate_existing: refresh the object if this session already holds the old row.
    return db.scalar(
        select(WikiArticle)
        .options(undefer(WikiArticle.sections))
        .where(WikiArticle.lang == values["lang"], WikiArticle.page_id == values["page_id"])
        .execution_options(populate_existing=True)
    )


def touch_article(db: Session, article: WikiArticle) -> None:
    """Mark a cached article as checked now (its revision hasn't changed)."""
    article.fetched_at = func.now()
    db.flush()
