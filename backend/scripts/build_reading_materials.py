"""Pre-build reading material so users get it instantly (version 1 for each topic).

Run from the backend folder:
    .\\.venv\\Scripts\\python scripts/build_reading_materials.py              # all curated topics without a version
    .\\.venv\\Scripts\\python scripts/build_reading_materials.py 3 7          # specific topic ids
    .\\.venv\\Scripts\\python scripts/build_reading_materials.py 3 --preview  # also print the material

Topics that already have a version are skipped (versions never change once built).
"""
import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select  # noqa: E402

from app.db.session import SessionLocal  # noqa: E402
from app.models import ReadingMaterial, Topic  # noqa: E402
from app.modules.reading import reading_repository  # noqa: E402
from app.modules.reading.reading_service import build_next_version  # noqa: E402
from app.modules.topics import topics_repository  # noqa: E402


def preview(material: ReadingMaterial) -> None:
    content = material.content
    print(f"\n  summary: {content['summary']}")
    print("  key points:")
    for point in content["keyPoints"]:
        print(f"    - {point}")
    print("  sections:")
    for section in content["sections"]:
        words = sum(len(p.split()) for p in section["paragraphs"])
        print(f"    [{words:>4} words] {section['heading']}")
    print("  sources:", ", ".join(f"{s.title} ({s.lang})" for s in material.sources))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("topic_ids", nargs="*", type=int)
    parser.add_argument("--preview", action="store_true")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        if args.topic_ids:
            ids = args.topic_ids
        else:
            has_version = select(ReadingMaterial.topic_id)
            ids = list(db.scalars(
                select(Topic.id).where(Topic.source == "curated", Topic.is_active.is_(True), Topic.id.not_in(has_version)).order_by(Topic.id)
            ))

        for topic_id in ids:
            topic = topics_repository.get_topic(db, topic_id)
            if topic is None:
                print(f"topic {topic_id}: not found")
                continue
            versions = reading_repository.list_versions(db, topic_id)
            started = time.perf_counter()
            material = versions[0] if versions else build_next_version(db, topic)
            took = time.perf_counter() - started
            if material is None:
                print(f"topic {topic_id}: could not build material ({topic.title})")
                continue
            material = reading_repository.get_material(db, material.id)
            state = "exists" if versions else f"built in {took:.1f}s"
            print(
                f"topic {topic_id}: v{material.version_no} {state} | {material.word_count} words, "
                f"{material.read_minutes} min, lang={material.lang} | {topic.title}"
            )
            if args.preview:
                preview(material)
    finally:
        db.close()


if __name__ == "__main__":
    main()
