from app.core.text import keywords
from app.modules.reading.reading_builder import (
    SourceArticle,
    build_version,
    score_piece,
    split_sentences,
)


def section(heading, words, path=None, level=2, topic_word="work", list_ratio=0.0):
    """A section of `words` words that mentions `topic_word` a few times."""
    sentence = f"Remote {topic_word} changes how people do their jobs every single day. "
    body = (sentence * (words // 11 + 1)).split()[:words]
    text = " ".join(body)
    return {
        "heading": heading,
        "path": path if path is not None else ([heading] if heading else []),
        "level": level,
        "paragraphs": [text],
        "words": len(body),
        "list_ratio": list_ratio,
    }


def article(rank, page_id, title, sections):
    return SourceArticle(rank=rank, lang="en", page_id=page_id, title=title, sections=sections)


TERMS = keywords("Remote work office culture")

PRIMARY = article(0, 1, "Remote work", [
    section(None, 300),
    section("History", 400),
    section("Potential benefits", 450),
    section("Potential drawbacks", 450),
    section("Statistics", 380),
    section("References", 500),
    section("See also", 200, list_ratio=0.9),
    section("Tiny", 20),
])
SECONDARY = article(1, 2, "Organizational culture", [
    section(None, 300, topic_word="culture"),
    section("Effects on performance", 420, topic_word="culture"),
    section("Criticism", 400, topic_word="culture"),
    section("Definitions", 350, topic_word="culture"),
])


def test_reference_tiny_and_list_sections_are_never_used():
    assert score_piece(PRIMARY.sections[5], 0, TERMS) is None  # References
    assert score_piece(PRIMARY.sections[6], 0, TERMS) is None  # list-like
    assert score_piece(PRIMARY.sections[7], 0, TERMS) is None  # < 40 words


def test_discussion_headings_score_higher():
    plain = score_piece(PRIMARY.sections[4], 0, TERMS)       # Statistics
    discussion = score_piece(PRIMARY.sections[2], 0, TERMS)  # Potential benefits
    assert discussion > plain


def test_first_version_opens_with_primary_lead_and_respects_budget():
    built = build_version([PRIMARY, SECONDARY], TERMS, set(), target_words=1500, min_words=600)
    assert built is not None
    assert built.content["sections"][0]["heading"] == "Remote work"
    assert built.unit_keys[0] == "en:1:0"
    assert 600 <= built.word_count <= 1500 + 150
    assert built.read_minutes == -(-built.word_count // 200)
    assert all("References" not in s["heading"] for s in built.content["sections"])
    # Secondary-article sections are labelled with their article.
    assert any(s["heading"].startswith("Organizational culture") for s in built.content["sections"])


def test_second_version_does_not_repeat_pieces():
    first = build_version([PRIMARY, SECONDARY], TERMS, set(), target_words=1500, min_words=600)
    second = build_version(
        [PRIMARY, SECONDARY], TERMS, set(first.unit_keys), target_words=1500, min_words=600
    )
    assert second is not None
    overlap = set(first.unit_keys) & set(second.unit_keys)
    reused_words = sum(
        len(" ".join(s["paragraphs"]).split())
        for key, s in zip(second.unit_keys, second.content["sections"])
        if key in overlap
    )
    assert reused_words / second.word_count <= 0.4


def test_returns_none_when_material_is_exhausted():
    first = build_version([PRIMARY, SECONDARY], TERMS, set(), target_words=3000, min_words=600)
    second = build_version(
        [PRIMARY, SECONDARY], TERMS, set(first.unit_keys), target_words=3000, min_words=600
    )
    used = set(first.unit_keys) | set(second.unit_keys if second else [])
    third = build_version([PRIMARY, SECONDARY], TERMS, used, target_words=3000, min_words=600)
    assert third is None


def test_key_points_and_summary():
    built = build_version([PRIMARY, SECONDARY], TERMS, set(), target_words=1500, min_words=600)
    points = built.content["keyPoints"]
    assert 1 <= len(points) <= 7
    assert all(6 <= len(p.split()) <= 35 for p in points)
    assert len(points) == len(set(points))
    assert built.content["summary"]


def test_no_single_section_dominates():
    huge = article(0, 3, "Nuclear power debate", [
        section(None, 300),
        section("Health effects", 2000),
        section("Costs", 400),
        section("Safety", 400),
    ])
    built = build_version([huge], TERMS, set(), target_words=2500, min_words=600)
    longest = max(len(" ".join(s["paragraphs"]).split()) for s in built.content["sections"])
    assert longest <= 2500 * 0.35 + 150


def test_split_sentences_keeps_abbreviations_together():
    text = "Many firms, e.g. Google, allow it. The U.S. leads. Others follow."
    assert split_sentences(text) == ["Many firms, e.g. Google, allow it.", "The U.S. leads.", "Others follow."]
