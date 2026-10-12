"""Seed the curated topic bank, each topic backed by hand-picked Wikipedia articles.

Run from the backend folder after `alembic upgrade head`:
    .\\.venv\\Scripts\\python scripts/seed_topics.py

Safe to re-run: topics are matched by their normalized title and updated in place.
Every article title is checked against Wikipedia (one batched request); redirects are
stored as their canonical title and missing/disambiguation titles are reported and skipped.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select  # noqa: E402

from app.constants.difficulty import Difficulty  # noqa: E402
from app.core.text import normalize_topic  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.integrations.wikipedia.client import get_wikipedia_client  # noqa: E402
from app.models import Topic, TopicCategory, TopicWikiSource  # noqa: E402

B, I, A = Difficulty.BEGINNER, Difficulty.INTERMEDIATE, Difficulty.ADVANCED

# (title, teaser, category, difficulty, [Wikipedia articles, best first])
TOPICS = [
    # Technology
    ("Should AI tutors replace homework help?",
     "AI can explain anything at 2 a.m. Does that make homework help better, or just easier?",
     "Technology", I, ["Intelligent tutoring system", "Artificial intelligence in education", "Homework"]),
    ("Are smartphones making us less focused?",
     "We check our phones constantly. Is our attention paying the price?",
     "Technology", B, ["Problematic smartphone use", "Attention span", "Smartphone"]),
    ("Self-driving cars: ready for city streets?",
     "Robotaxis are already on some roads. Are they safe enough to go everywhere?",
     "Technology", I, ["Self-driving car", "Vehicular automation"]),
    ("Should coding be taught in every school?",
     "Some call programming the new literacy. Should every student learn it?",
     "Technology", B, ["Computer science education", "Computer programming"]),
    ("Should governments regulate artificial intelligence?",
     "AI is moving fast. Who should set the rules, and how strict should they be?",
     "Technology", A, ["Regulation of artificial intelligence", "Ethics of artificial intelligence", "AI safety"]),
    ("Is social media good for democracy?",
     "It gives everyone a voice, and spreads misinformation. Which wins?",
     "Technology", A, ["Social media use in politics", "Misinformation"]),
    # Business
    ("The case for a four-day work week",
     "Trials report happier staff and steady output. Can every industry make it work?",
     "Business", I, ["Four-day workweek", "Workweek and weekend"]),
    ("Remote work vs. office culture",
     "Flexibility against face time: what really makes teams work?",
     "Business", B, ["Remote work", "Organizational culture"]),
    ("Is the gig economy good for workers?",
     "Freedom to choose your hours, or work without security?",
     "Business", I, ["Gig worker", "Temporary work"]),
    ("Should companies publish salaries openly?",
     "Pay transparency could close pay gaps, or create new tensions at work.",
     "Business", A, ["Pay transparency", "Gender pay gap"]),
    ("Universal basic income: good idea or not?",
     "Cash for everyone, no strings attached. Safety net or disincentive to work?",
     "Business", A, ["Universal basic income", "Negative income tax"]),
    ("Is cryptocurrency the future of money?",
     "Digital coins promise freedom from banks. Are they money, or speculation?",
     "Business", I, ["Cryptocurrency", "Bitcoin"]),
    # Society
    ("Is social media making us lonelier?",
     "More connected than ever, yet loneliness is rising. Is the feed to blame?",
     "Society", B, ["Loneliness", "Digital media use and mental health"]),
    ("Should voting be compulsory?",
     "Some countries fine people who don't vote. Would it make democracy stronger?",
     "Society", I, ["Compulsory voting", "Voter turnout"]),
    ("Are exams the best way to measure learning?",
     "Tests are fair and simple to compare, but do they measure what matters?",
     "Society", I, ["Standardized test", "Educational assessment"]),
    ("Should college education be free?",
     "Free tuition could open doors. Who should pay for it?",
     "Society", I, ["Free education", "Student debt"]),
    ("Should junk food ads aimed at children be banned?",
     "Ads shape what children want to eat. Should they be off-limits?",
     "Society", I, ["Advertising to children", "Childhood obesity"]),
    ("Should homework be banned in primary school?",
     "Extra practice or lost playtime? Young students may not need homework at all.",
     "Society", B, ["Homework", "Primary education"]),
    # Environment
    ("Fast fashion and its environmental cost",
     "Cheap clothes, fast trends, and a planet paying the difference.",
     "Environment", B, ["Fast fashion", "Environmental impact of fashion"]),
    ("Should single-use plastics be banned?",
     "Bans cut waste, but are the alternatives really better?",
     "Environment", B, ["Plastic pollution", "Phase-out of lightweight plastic bags"]),
    ("Can cities run fully on renewable energy?",
     "Some cities aim for 100% renewables. Is it realistic everywhere?",
     "Environment", I, ["100% renewable energy", "Renewable energy"]),
    ("Is nuclear power the answer to climate change?",
     "Low-carbon and reliable, but costly and controversial.",
     "Environment", A, ["Nuclear power debate", "Nuclear power"]),
    ("Should meat be taxed to protect the planet?",
     "Livestock has a big climate footprint. Would a meat tax help?",
     "Environment", A, ["Meat tax", "Environmental impact of meat production"]),
    ("Electric cars: are they really greener?",
     "No exhaust, but what about batteries and electricity from coal?",
     "Environment", I, ["Electric car", "Environmental aspects of the electric car"]),
    # Science
    ("CRISPR and the ethics of gene editing",
     "We can now edit genes precisely. Where should the line be drawn?",
     "Science", A, ["CRISPR gene editing", "Human germline engineering", "Genome editing"]),
    ("Space exploration: worth the cost?",
     "Billions for rockets while problems remain on Earth. Is it worth it?",
     "Science", I, ["Space exploration", "Space colonization"]),
    ("Should we bring back extinct species?",
     "Science may soon revive the woolly mammoth. Should it?",
     "Science", I, ["De-extinction", "Extinction"]),
    ("Should vaccines be mandatory?",
     "Public health against personal choice: where's the balance?",
     "Science", I, ["Vaccination policy", "Vaccine hesitancy"]),
    ("Is animal testing ever justified?",
     "Medical progress or animal suffering? The trade-offs are hard.",
     "Science", I, ["Animal testing", "Alternatives to animal testing"]),
    ("Should humans try to live on Mars?",
     "A backup planet or an expensive dream?",
     "Science", B, ["Colonization of Mars", "Human mission to Mars"]),
]


def seed_topics() -> None:
    db = SessionLocal()
    client = get_wikipedia_client()

    try:
        categories = {c.name: c.id for c in db.scalars(select(TopicCategory))}
        all_titles = sorted({t for *_, titles in TOPICS for t in titles})
        infos = client.page_info("en", all_titles)

        problems = []
        created = updated = 0
        for title, teaser, category, difficulty, wiki_titles in TOPICS:
            canonical: list[str] = []
            for wiki_title in wiki_titles:
                info = infos.get(wiki_title)
                if info is None:
                    problems.append(f"missing article {wiki_title!r} ({title})")
                elif info.is_disambiguation:
                    problems.append(f"disambiguation page {wiki_title!r} ({title})")
                elif info.title not in canonical:
                    canonical.append(info.title)
            if not canonical:
                problems.append(f"SKIPPED topic with no valid articles: {title}")
                continue

            key = normalize_topic(title).key
            # Match by title first, so changes to the normalization rules update the key
            # instead of creating a duplicate topic.
            topic = db.scalar(select(Topic).where(Topic.source == "curated", Topic.title == title))
            topic = topic or db.scalar(select(Topic).where(Topic.normalized_key == key))
            if topic is None:
                topic = Topic(normalized_key=key, source="curated")
                db.add(topic)
                created += 1
            else:
                updated += 1

            topic.normalized_key = key
            topic.title = title
            topic.teaser = teaser
            topic.category_id = categories[category]
            topic.difficulty = difficulty
            topic.is_active = True

            current = [s.page_title for s in sorted(topic.wiki_sources, key=lambda s: s.rank) if s.lang == "en"]
            if current != canonical:
                topic.wiki_sources.clear()
                db.flush()
                topic.wiki_sources.extend(
                    TopicWikiSource(rank=rank, lang="en", page_title=t) for rank, t in enumerate(canonical)
                )

        db.commit()
        print(f"topics: {created} created, {updated} updated ({len(all_titles)} articles checked)")
        for problem in problems:
            print("  !", problem)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_topics()
