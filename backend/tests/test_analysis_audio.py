"""Unit tests for phase 2 logic on synthetic word lists (no models needed)."""
from app.analysis.audio.fillers import detect_fillers, detect_repetitions
from app.analysis.audio.pauses import detect_pauses
from app.analysis.audio.pipeline import build_metrics
from app.analysis.config import DEFAULT_CONFIG as CFG
from app.analysis.schemas import Word


def make_words(spec):
    """spec: list of (text, start, end)."""
    return [Word(text=t, start=s, end=e) for t, s, e in spec]


def test_non_lexical_and_phrase_fillers():
    words = make_words([("So", 0, .2), ("um,", .3, .5), ("you", .6, .7), ("know", .7, .9),
                        ("uhh", 1.0, 1.3), ("it", 1.4, 1.5), ("works.", 1.5, 1.9)])
    labels = [(e.meta["kind"], e.meta["label"]) for e in detect_fillers(words, CFG)]
    assert ("non_lexical", "um") in labels
    assert ("non_lexical", "uh") in labels
    assert ("phrase", "you know") in labels
    assert len(labels) == 3  # "So" at sentence start with no gaps is not a filler


def test_like_only_counts_when_set_off():
    verb = make_words([("I", 0, .1), ("like", .1, .3), ("pizza", .3, .7)])
    assert detect_fillers(verb, CFG) == []

    filler = make_words([("it", 0, .1), ("was,", .1, .4), ("like,", .5, .7), ("huge", .8, 1.1)])
    assert [e.meta["label"] for e in detect_fillers(filler, CFG)] == ["like"]

    paused = make_words([("it", 0, .1), ("was", .1, .4), ("like", 1.0, 1.2), ("huge", 1.9, 2.3)])
    assert [e.meta["label"] for e in detect_fillers(paused, CFG)] == ["like"]


def test_repetitions_skip_fillers_and_emphasis():
    words = make_words([("the", 0, .2), ("the", .2, .4), ("cat", .4, .8),
                        ("very", .9, 1.1), ("very", 1.1, 1.3), ("um", 1.4, 1.6), ("um", 1.6, 1.8)])
    fillers = detect_fillers(words, CFG)
    reps = detect_repetitions(words, fillers, CFG)
    assert [r.meta["text"] for r in reps] == ["the"]


def test_pause_classification_and_edges():
    words = make_words([("Hello.", 1.0, 1.4),          # leading silence 0-1.0 is not a pause
                        ("Today,", 2.0, 2.4),          # 0.6 s after a sentence -> boundary
                        ("we", 3.0, 3.1),              # 0.6 s after a comma -> clause boundary
                        ("talk", 6.0, 6.4)])           # 2.9 s mid-phrase -> long hesitation
    segments = [(1.0, 1.4), (2.0, 2.4), (3.0, 3.1), (6.0, 6.4)]
    pauses = detect_pauses(words, segments, [], CFG)

    assert [p.type for p in pauses] == ["pause", "pause", "long_pause"]
    assert [p.meta["position"] for p in pauses] == [
        "sentence_boundary", "clause_boundary", "hesitation"]
    assert pauses[2].meta["duration_s"] == 2.9


def test_filled_pause_and_asr_fallback():
    words = make_words([("so", 0, .2), ("um", 1.0, 1.3), ("yes", 2.0, 2.3)])
    fillers = detect_fillers(words, CFG)
    # VAD saw one continuous segment, but ASR words are 0.8 s / 0.7 s apart
    pauses = detect_pauses(words, [(0.0, 2.3)], fillers, CFG)
    assert len(pauses) == 2
    assert all(p.meta["detected_by"] == "asr" and p.meta["filled"] for p in pauses)


def test_metrics_exclude_fillers_from_wpm():
    words = make_words([("um", 0, .5), ("hello", .5, 1.0), ("there", 1.0, 1.5)] * 1)
    fillers = detect_fillers(words, CFG)
    m = build_metrics(words, fillers, [], [], 3.0, {})
    assert m.word_count == 2 and m.filler_count == 1
    assert m.wpm == 80.0  # 2 words / 1.5 s
    assert m.filler_breakdown == {"um": 1}
