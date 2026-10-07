"""Vocabulary feedback: lexical diversity, overused words, filler alternatives,
and (optionally) coverage of the topic's key points."""
import re
from collections import Counter
from typing import Optional

from app.analysis.feedback.retriever import vocabulary_data
from app.analysis.schemas import VocabularyFeedback, WordSuggestion

_WORD = re.compile(r"[a-z']+")
STOPWORDS = set("""
a about above after again against all am an and any are as at be because been before being below
between both but by can could did do does doing down during each few for from further had has have
having he her here hers him his how i if in into is it its itself just me more most my myself no nor
not of off on once only or other our ours out over own same she should so some such than that the
their them then there these they this those through to too under until up us was we were what when
where which while who whom why will with would you your yours yeah okay also like um uh er hmm
will would shall may might must one two going
""".split())
MIN_OVERUSED_COUNT = 4  # a content word must appear this often to count as overused


def content_words(text: str) -> list[str]:
    return [w for w in _WORD.findall(text.lower()) if w not in STOPWORDS and len(w) > 2]


def mattr(tokens: list[str], window: int = 50) -> Optional[float]:
    """Moving-average type-token ratio: lexical diversity that doesn't depend on length."""
    if len(tokens) < window:
        return round(len(set(tokens)) / len(tokens), 3) if len(tokens) >= 20 else None
    ratios = [len(set(tokens[i:i + window])) / window for i in range(len(tokens) - window + 1)]
    return round(sum(ratios) / len(ratios), 3)


def diversity_label(value: float) -> str:
    return "varied" if value >= 0.72 else "moderate" if value >= 0.62 else "repetitive"


def _stem(word: str) -> str:
    for suffix in ("ing", "ed", "es", "s", "ly"):
        if word.endswith(suffix) and len(word) - len(suffix) >= 4:
            return word[: -len(suffix)]
    return word


def topic_coverage(transcript: str, key_points: list[str]) -> dict:
    """A key point counts as covered if at least half of its content words (stemmed)
    appear in the transcript. Lexical, so paraphrases may be missed."""
    spoken = {_stem(w) for w in content_words(transcript)}
    covered, missed = [], []
    for point in key_points:
        stems = {_stem(w) for w in content_words(point)}
        hit = bool(stems) and len(stems & spoken) / len(stems) >= 0.5
        (covered if hit else missed).append(point)
    total = len(key_points)
    return {"covered": covered, "missed": missed,
            "pct": round(100 * len(covered) / total, 1) if total else None}


def analyze_vocabulary(
    transcript: str,
    filler_breakdown: dict[str, int],
    key_points: Optional[list[str]] = None,
) -> VocabularyFeedback:
    data = vocabulary_data()
    tokens = content_words(transcript)
    diversity = mattr(tokens)

    overused = []
    for word, count in Counter(tokens).most_common(25):
        if count < MIN_OVERUSED_COUNT:
            break
        alts = data["synonyms"].get(word)
        if alts:
            overused.append(WordSuggestion(word=word, count=count, alternatives=alts))
        if len(overused) == 5:
            break

    fillers = [
        WordSuggestion(word=f, count=c, alternatives=data["filler_alternatives"][f])
        for f, c in filler_breakdown.items() if f in data["filler_alternatives"]
    ]
    return VocabularyFeedback(
        lexical_diversity=diversity,
        diversity_label=diversity_label(diversity) if diversity is not None else None,
        overused=overused,
        filler_alternatives=fillers,
        topic_coverage=topic_coverage(transcript, key_points) if key_points else None,
    )
