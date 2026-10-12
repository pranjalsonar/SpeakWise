"""Build a reading-material version from parsed Wikipedia articles. Pure functions, no I/O.

How a version is assembled (no LLM, deterministic):
1. Every section of every source article is a "piece", keyed "<lang>:<page_id>:<index>".
2. Pieces are scored: topic-keyword relevance, a bonus for discussion headings
   (benefits, criticism, impact...), a bonus for article leads, a penalty for lower-ranked
   articles. Reference/link sections, tiny sections and list-like sections are dropped.
3. A lead piece opens the version, then the best pieces fill up to the word target
   (the last piece is cut at a paragraph boundary). Pieces are shown in article order.
4. Pieces used by earlier versions of the topic (`used_keys`) are avoided; some may be
   reused to reach the minimum length, but at least `min_new_ratio` of words must be new.
"""
import math
import re
from dataclasses import dataclass, field
from typing import Any

from app.core.text import keyword_list, keywords

WORDS_PER_MINUTE = 200
MIN_PIECE_WORDS = 40
MAX_LIST_RATIO = 0.5
MAX_KEY_POINTS = 7
MAX_KEY_POINT_WORDS = 35
# No single section may take more than this share of the material, so it covers more ground.
MAX_PIECE_SHARE = 0.35

_EXCLUDED_HEADING = re.compile(
    r"^(references?|see also|external links|notes|further reading|bibliography|sources|"
    r"citations|footnotes|works cited|gallery|filmography|discography|awards( and nominations)?|"
    r"in popular culture|selected (works|publications)|publications|explanatory notes|"
    r"general( and cited)? (references|sources)|primary sources|secondary sources)$",
    re.IGNORECASE,
)
_DISCUSSION_HEADING = re.compile(
    r"benefit|advantage|disadvantage|drawback|criticism|critique|controvers|impact|effect|"
    r"ethic|debate|concern|risk|regulat|reception|challenge|argument|opposition|support|"
    r"limitation|future|outlook|issue|consequence|policy|response|pros|cons\b",
    re.IGNORECASE,
)
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"“‘(])")
_ABBREVIATIONS = ("e.g.", "i.e.", "U.S.", "U.K.", "Mr.", "Mrs.", "Dr.", "St.", "vs.", "etc.", "approx.", "No.")


@dataclass(frozen=True)
class SourceArticle:
    rank: int  # 0 = best source for the topic
    lang: str
    page_id: int
    title: str
    sections: list[dict[str, Any]]  # output of parser.parse_extract


@dataclass
class Piece:
    key: str
    article: SourceArticle
    index: int
    heading: str | None
    path: list[str]
    level: int
    paragraphs: list[str]
    words: int
    score: float

    @property
    def is_lead(self) -> bool:
        return self.heading is None


@dataclass
class BuiltMaterial:
    content: dict[str, Any]
    unit_keys: list[str]
    word_count: int
    read_minutes: int
    lang: str
    articles: list[SourceArticle] = field(default_factory=list)  # articles actually used


# ---- scoring ----

def score_piece(section: dict[str, Any], rank: int, topic_terms: set[str]) -> float | None:
    """Relevance score, or None if the section shouldn't be used at all."""
    path = section.get("path") or []
    if any(_EXCLUDED_HEADING.match(heading) for heading in path):
        return None
    if section["words"] < MIN_PIECE_WORDS or section.get("list_ratio", 0) > MAX_LIST_RATIO:
        return None

    heading_text = " ".join(path)
    heading_hits = len(topic_terms & keywords(heading_text))
    body_words = keyword_list(" ".join(section["paragraphs"]))
    body_hits = sum(1 for word in body_words if word in topic_terms)
    density = min(5.0, 100 * body_hits / max(1, section["words"]))

    score = 3.0 * heading_hits + density
    if section["heading"] is None:  # article lead
        score += 4.0 + (2.0 if rank == 0 else 0.0)
    if _DISCUSSION_HEADING.search(heading_text):
        score += 2.5
    score -= 0.8 * rank
    score -= 0.3 * max(0, section.get("level", 2) - 2)
    return score


def make_pieces(articles: list[SourceArticle], topic_terms: set[str]) -> list[Piece]:
    pieces = []
    for article in articles:
        for index, section in enumerate(article.sections):
            score = score_piece(section, article.rank, topic_terms)
            if score is None:
                continue
            pieces.append(
                Piece(
                    key=f"{article.lang}:{article.page_id}:{index}",
                    article=article,
                    index=index,
                    heading=section["heading"],
                    path=section.get("path") or [],
                    level=section.get("level", 2),
                    paragraphs=section["paragraphs"],
                    words=section["words"],
                    score=score,
                )
            )
    return pieces


# ---- assembly ----

def _fit(piece: Piece, remaining: int) -> list[str] | None:
    """Paragraphs of `piece` that fit in `remaining` words (cut at a paragraph boundary)."""
    if piece.words <= remaining:
        return piece.paragraphs
    kept, total = [], 0
    for paragraph in piece.paragraphs:
        words = len(paragraph.split())
        if kept and total + words > remaining:
            break
        kept.append(paragraph)
        total += words
    # A single huge first paragraph that blows the budget isn't worth including.
    return kept if total <= remaining + 150 else None


def build_version(
    articles: list[SourceArticle],
    topic_terms: set[str],
    used_keys: set[str],
    *,
    target_words: int = 2500,
    min_words: int = 800,
    min_new_ratio: float = 0.6,
) -> BuiltMaterial | None:
    """Assemble one version, or None if there isn't enough (new) material."""
    pieces = make_pieces(articles, topic_terms)
    by_score = sorted(pieces, key=lambda p: (-p.score, p.article.rank, p.index))
    fresh = [p for p in by_score if p.key not in used_keys]
    reused = [p for p in by_score if p.key in used_keys]
    max_reused_words = int(target_words * (1 - min_new_ratio))
    max_piece_words = int(target_words * MAX_PIECE_SHARE)

    chosen: dict[str, list[str]] = {}  # key -> paragraphs actually used
    chosen_pieces: list[Piece] = []
    totals = {"all": 0, "reused": 0}

    def add(piece: Piece, is_reused: bool) -> None:
        remaining = min(target_words - totals["all"], max_piece_words)
        if remaining < MIN_PIECE_WORDS or piece.key in chosen:
            return
        if is_reused:
            remaining = min(remaining, max_reused_words - totals["reused"])
            if remaining < MIN_PIECE_WORDS:
                return
        paragraphs = _fit(piece, remaining)
        if not paragraphs:
            return
        words = sum(len(p.split()) for p in paragraphs)
        chosen[piece.key] = paragraphs
        chosen_pieces.append(piece)
        totals["all"] += words
        if is_reused:
            totals["reused"] += words

    # 1. Open with a lead: a fresh one if possible, else the best lead overall.
    lead = next((p for p in fresh if p.is_lead), None)
    if lead:
        add(lead, is_reused=False)
    else:
        lead = next((p for p in reused if p.is_lead), None)
        if lead:
            add(lead, is_reused=True)

    # 2. Fill with the best fresh pieces, 3. top up with reused ones (capped).
    for piece in fresh:
        add(piece, is_reused=False)
    for piece in reused:
        add(piece, is_reused=True)

    total = totals["all"]
    if total < min_words or (total - totals["reused"]) / total < min_new_ratio:
        return None

    # Show pieces in reading order: lead first, then by article rank and section order.
    ordered = sorted(chosen_pieces, key=lambda p: (p is not lead, p.article.rank, p.index))
    primary = ordered[0].article
    sections = [
        {"heading": _display_heading(p, primary), "paragraphs": chosen[p.key]} for p in ordered
    ]
    used_articles = list({p.article.page_id: p.article for p in ordered}.values())

    return BuiltMaterial(
        content={
            "summary": _summary(chosen[ordered[0].key]),
            "keyPoints": _key_points([chosen[p.key] for p in ordered]),
            "sections": sections,
        },
        unit_keys=[p.key for p in ordered],
        word_count=total,
        read_minutes=max(1, math.ceil(total / WORDS_PER_MINUTE)),
        lang=primary.lang,
        articles=used_articles,
    )


# ---- presentation ----

def _display_heading(piece: Piece, primary: SourceArticle) -> str:
    """Short, readable headings.

    Main article: "Parent: Child" ("Potential benefits: Cost reduction").
    Other articles: "Article: Child" ("Homework: Criticism").
    """
    if piece.is_lead:
        return piece.article.title
    path = piece.path or [piece.heading or ""]
    if piece.article.page_id != primary.page_id:
        return f"{piece.article.title}: {path[-1]}"
    return ": ".join(path[-2:])


def split_sentences(text: str) -> list[str]:
    parts = _SENTENCE_SPLIT.split(text)
    sentences: list[str] = []
    for part in parts:
        # Re-join splits that happened after an abbreviation ("e.g. Something").
        if sentences and sentences[-1].endswith(_ABBREVIATIONS):
            sentences[-1] = f"{sentences[-1]} {part}"
        else:
            sentences.append(part)
    return [s.strip() for s in sentences if s.strip()]


def _summary(paragraphs: list[str], max_words: int = 70) -> str:
    sentences = split_sentences(" ".join(paragraphs[:2]))
    summary: list[str] = []
    for sentence in sentences:
        if summary and len(" ".join(summary + [sentence]).split()) > max_words:
            break
        summary.append(sentence)
    return " ".join(summary)


def _key_points(sections: list[list[str]]) -> list[str]:
    points: list[str] = []
    for paragraphs in sections:
        for sentence in split_sentences(paragraphs[0]) if paragraphs else []:
            words = len(sentence.split())
            if 6 <= words <= MAX_KEY_POINT_WORDS and sentence not in points:
                points.append(sentence)
                break
        if len(points) == MAX_KEY_POINTS:
            break
    return points
