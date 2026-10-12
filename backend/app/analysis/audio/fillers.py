"""Filler-word and repetition detection (rule-based baseline).

Kinds of filler (stored in event.meta["kind"]):
    non_lexical  um, uh, er, hmm ...       always a filler
    lexical      basically, actually ...   always flagged (speaking-style fillers)
    phrase       you know, I mean, you see
    contextual   like, so, well, right, okay - only when set off by a comma or
                 by pauses on both sides ("it was, like, huge"), so that
                 "I like pizza" is not counted.

Known limitation: Whisper tends to drop um/uh from transcripts; the verbatim
prompt in config helps only partly. A BERT disfluency tagger / audio filler
classifier is the planned upgrade.
"""
import re

from app.analysis.config import AnalysisConfig
from app.analysis.schemas import Event, Word

_NON_LEXICAL = re.compile(r"^(u+h*m+|u+h+|e+r+m*|a+h+|h+m+|m{2,})$")
LEXICAL = {"basically", "actually", "literally", "obviously", "honestly"}
PHRASES = [("you", "know"), ("i", "mean"), ("you", "see")]
AMBIGUOUS = {"like", "so", "well", "right", "okay"}
# Repeating these is normal emphasis, not a stumble.
REPEAT_OK = {"very", "so", "no", "really", "bye", "ha", "yes"}

_EDGE = re.compile(r"^\W+|\W+$")
_COLLAPSE = re.compile(r"(.)\1+")


def normalize(text: str) -> str:
    return _EDGE.sub("", text.lower())


def _canonical(norm: str) -> str:
    return _COLLAPSE.sub(r"\1", norm)  # umm -> um, hmmm -> hm


def _event(kind: str, label: str, words: list[Word]) -> Event:
    return Event(
        type="filler",
        source="audio",
        start=words[0].start,
        end=words[-1].end,
        confidence=min(w.probability for w in words),
        meta={"kind": kind, "label": label, "text": " ".join(w.text for w in words)},
    )


def detect_fillers(words: list[Word], cfg: AnalysisConfig) -> list[Event]:
    norms = [normalize(w.text) for w in words]
    events: list[Event] = []
    i = 0
    while i < len(words):
        n = norms[i]

        # multi-word phrases first
        phrase = next(
            (p for p in PHRASES
             if tuple(norms[i:i + len(p)]) == p),
            None,
        )
        if phrase:
            span = words[i:i + len(phrase)]
            events.append(_event("phrase", " ".join(phrase), span))
            i += len(phrase)
            continue

        if _NON_LEXICAL.match(n):
            events.append(_event("non_lexical", _canonical(n), [words[i]]))
        elif n in LEXICAL:
            events.append(_event("lexical", n, [words[i]]))
        elif n in AMBIGUOUS and _is_set_off(words, i, cfg):
            events.append(_event("contextual", n, [words[i]]))
        i += 1
    return events


def _is_set_off(words: list[Word], i: int, cfg: AnalysisConfig) -> bool:
    w = words[i]
    if w.text.rstrip().endswith(","):
        return True
    if i > 0 and words[i - 1].text.rstrip().endswith(","):
        return True
    if 0 < i < len(words) - 1:
        before = w.start - words[i - 1].end
        after = words[i + 1].start - w.end
        return before >= cfg.ambiguous_gap_s and after >= cfg.ambiguous_gap_s
    return False


def detect_repetitions(
    words: list[Word], fillers: list[Event], cfg: AnalysisConfig
) -> list[Event]:
    """Immediate word repeats ("the the cat"), a common stumble. Repeated fillers
    ("um um") are already counted as fillers and skipped."""
    filler_starts = {e.start for e in fillers}
    events: list[Event] = []
    for a, b in zip(words, words[1:]):
        na, nb = normalize(a.text), normalize(b.text)
        if not na or na != nb or na in REPEAT_OK:
            continue
        if a.start in filler_starts or b.start in filler_starts:
            continue
        if a.text.rstrip()[-1] in ".?!;:":  # sentence break between them
            continue
        if b.start - a.end > cfg.repetition_max_gap_s:
            continue
        events.append(
            Event(
                type="repetition", source="audio", start=a.start, end=b.end,
                confidence=min(a.probability, b.probability), meta={"text": na},
            )
        )
    return events
