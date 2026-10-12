"""Audio-metric tests on hand-built word lists and synthetic signals (no ASR model needed).

The audio is synthetic: 'speech' is a loud tone, silence is near-zero noise. These tests
check the logic (counting, thresholds, denominators, statuses), not real-speech accuracy.
"""
import numpy as np
import pytest

from speakwise.audio_metrics import (analyze_audio, detect_fillers, detect_pauses, detect_repetitions,
                                     audio_quality)
from speakwise.audio_transcription import build_transcription
from speakwise.config import PipelineConfig
from speakwise.schemas import Status, WordToken

RATE = 16000
CFG = PipelineConfig()


def W(spec, prob=0.95):
    """spec: (text, start, end) or (text, start, end, probability)."""
    return [WordToken(text=x[0], start=x[1], end=x[2], probability=x[3] if len(x) > 3 else prob) for x in spec]


def signal(duration, speech, level=0.3, noise=0.001, seed=0):
    rng = np.random.default_rng(seed)
    a = rng.normal(0, noise, int(duration * RATE)).astype(np.float32)
    t = np.arange(len(a)) / RATE
    for s, e in speech:
        m = (t >= s) & (t < e)
        a[m] += (level * np.sin(2 * np.pi * 220 * t[m])).astype(np.float32)
    return a


# ------------------------------------------------------------------ fillers
def labels(evs):
    return [(e.details["kind"], e.details["label"]) for e in evs]


def test_fillers_kinds_and_context():
    words = W([("So", 0, .2), ("um,", .3, .5), ("you", .6, .7), ("know", .7, .9), ("uhh", 1.0, 1.3),
               ("I", 1.4, 1.5), ("like", 1.5, 1.7), ("pizza.", 1.7, 2.0),
               ("It", 2.1, 2.2), ("was,", 2.2, 2.4), ("like,", 2.5, 2.7), ("huge.", 2.8, 3.1),
               ("Basically", 3.2, 3.6), ("a", 3.7, 3.8), ("kind", 3.8, 4.0), ("of", 4.0, 4.1), ("tree.", 4.1, 4.5)])
    got = labels(detect_fillers(words, CFG))
    assert ("non_lexical", "um") in got and ("non_lexical", "uh") in got
    assert ("phrase", "you know") in got and ("contextual", "like") in got
    assert ("lexical", "basically") in got
    assert sum(1 for _, l in got if l == "like") == 1  # "I like pizza" is not a filler
    assert ("phrase", "kind of") not in got  # "a kind of tree" is literal
    assert ("contextual", "so") not in got  # sentence-initial without comma/pause


# -------------------------------------------------------------- repetitions
def test_repetition_categories():
    words = W([("the", 0, .2), ("the", .2, .4), ("cat", .4, .7), ("is", .8, .9),
               ("very", 1.0, 1.2), ("very", 1.2, 1.4), ("big.", 1.4, 1.7),
               ("in", 2.0, 2.1), ("the", 2.1, 2.2), ("in", 2.3, 2.4), ("the", 2.4, 2.5), ("park", 2.5, 2.9),
               ("I", 3.0, 3.1), ("I", 3.1, 3.2), ("I", 3.2, 3.3), ("think.", 3.3, 3.6),
               ("Done.", 4.0, 4.3), ("Done.", 4.4, 4.7),
               ("um", 5.0, 5.2), ("um", 5.2, 5.4), ("ok", 5.5, 5.7)])
    evs = detect_repetitions(words, detect_fillers(words, CFG), CFG)
    by = {(e.type, e.details.get("word") or e.details.get("phrase")) for e in evs}
    assert ("word_repetition", "the") in by
    assert ("possible_emphasis", "very") in by
    assert ("phrase_repetition", "in the") in by
    triple = next(e for e in evs if e.details.get("word") == "i")
    assert triple.details["times"] == 3
    assert not any(e.details.get("word") == "done" for e in evs)  # sentence break between them
    assert not any(e.details.get("word") == "um" for e in evs)  # fillers are counted as fillers


# ------------------------------------------------------------------- pauses
def test_pauses_short_long_boundaries_and_rates():
    speech = [(1.0, 3.0), (3.6, 6.0), (8.5, 10.0)]  # gaps: 0.6 s (short), 2.5 s (long)
    words = W([("Hello", 1.0, 1.5), ("everyone.", 1.6, 3.0), ("Today", 3.6, 4.0), ("we", 4.1, 6.0),
               ("talk.", 8.5, 10.0)])
    audio = signal(12.0, speech)
    q = audio_quality(audio, RATE, speech, CFG)
    pa = detect_pauses(words, speech, [], audio, RATE, q.speech_rms_dbfs.value, 12.0, CFG)
    assert (pa.short_pauses.value, pa.long_pauses.value) == (1, 1)
    assert pa.longest_pause_s.value == pytest.approx(2.5, abs=0.01)
    assert pa.leading_silence_s.value == pytest.approx(1.0) and pa.trailing_silence_s.value == pytest.approx(2.0)
    assert pa.events[0].details["position"] == "sentence_boundary"
    assert pa.events[1].details["position"] == "mid_sentence"
    assert pa.pauses_per_minute.value == pytest.approx(2 / (9.0 / 60), rel=1e-3)
    assert "speech span 9.0s" in pa.pauses_per_minute.denominator


def test_loud_gap_is_uncertain_not_a_pause():
    speech = [(0.5, 2.0), (4.0, 6.0)]
    audio = signal(7.0, speech + [(2.0, 4.0)])  # the 'gap' is as loud as speech (VAD missed it)
    words = W([("a", .5, 2.0), ("b", 4.0, 6.0)])
    pa = detect_pauses(words, speech, [], audio, RATE, -13.0, 7.0, CFG)
    assert pa.long_pauses.value == 0 and pa.uncertain_gaps.value == 1
    assert pa.status == Status.warning


# ------------------------------------------------------------- full analysis
def test_analyze_audio_rates_clarity_and_quality():
    speech = [(0.5, 3.0), (3.5, 6.5), (7.0, 9.0), (9.6, 10.1)]
    words = W([("We", .5, .8), ("um", .9, 1.2), ("should", 1.3, 1.8), ("act", 1.9, 3.0),
               ("now", 3.5, 4.0), ("mumble", 4.1, 4.5, .2), ("mumble", 4.6, 5.0, .3), ("words", 5.1, 6.5, .1)])
    audio = signal(11.0, speech)
    tr = build_transcription(words, [], CFG)
    aa = analyze_audio(audio, RATE, tr, 11.0, CFG, speech=speech)
    assert aa.fillers.total.value == 1
    span = 6.5 - 0.5
    assert aa.fillers.per_minute.value == pytest.approx(1 / (span / 60), rel=1e-3)
    assert aa.fillers.per_100_words.value == pytest.approx(100 / 7, rel=1e-3)
    assert aa.words_per_minute.value == pytest.approx(7 / (span / 60), rel=1e-3)
    types = [s.type for s in aa.clarity.segments]
    assert "low_confidence_words" in types and "untranscribed_speech" in types  # 7.0-9.0 has no words
    assert aa.fillers.possible_untranscribed_hesitations.value == 1  # 0.5 s voiced bit at 9.6 s
    assert aa.audio_quality.snr_estimate_db.value > 30
    assert aa.status == Status.warning


def test_valid_zero_vs_missing():
    speech = [(0.5, 2.0)]
    audio = signal(3.0, speech)
    clean = analyze_audio(audio, RATE, build_transcription(W([("Hello", .5, 1.0), ("there.", 1.1, 2.0)]), [], CFG),
                          3.0, CFG, speech=speech)
    assert clean.fillers.total.value == 0 and clean.fillers.total.status.has_value  # a valid zero

    empty = analyze_audio(signal(3.0, []), RATE, build_transcription([], [], CFG), 3.0, CFG, speech=[])
    assert empty.status == Status.unavailable
    assert empty.fillers.total.value is None and empty.fillers.total.status == Status.unavailable
    assert empty.pauses.long_pauses.value is None


def test_quiet_and_clipped_recordings_are_flagged():
    speech = [(0.2, 2.8)]
    quiet = audio_quality(signal(3.0, speech, level=0.005, noise=0.0005), RATE, speech, CFG)
    assert any("quiet" in w for w in quiet.warnings)
    clipped = audio_quality(np.clip(signal(3.0, speech, level=1.5), -1, 1), RATE, speech, CFG)
    assert any("clips" in w for w in clipped.warnings)
