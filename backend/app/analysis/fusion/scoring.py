"""Rule-based, explainable scores (0-100).

Every sub-score is a weighted average of per-metric scores; each metric maps
linearly from "good" (100) to "bad" (0). Metrics that weren't measured are
dropped and the remaining weights renormalised. `drivers` lists how many points
each metric cost, which is what the feedback generator (phase 5) explains.

The targets are heuristics taken from public-speaking guidance (conversational
pace 120-160 wpm, <= ~1 filler/min is fluent, ...). They are meant to be tuned
or replaced by a trained model (see ml.py).
"""
from typing import Callable, Optional

from app.analysis.config import AnalysisConfig
from app.analysis.schemas import AudioMetrics, ScoreDriver, Scores, SubScore, VisionMetrics

# weight of each sub-score in the overall confidence score
OVERALL_WEIGHTS = {
    "fluency": 0.35, "eye_contact": 0.25, "delivery": 0.15,
    "composure": 0.15, "posture": 0.10,
}


def lin(value: float, good: float, bad: float) -> float:
    """100 at `good`, 0 at `bad`, linear in between (either direction), clamped."""
    t = (value - bad) / (good - bad)
    return 100.0 * min(1.0, max(0.0, t))


def band(value: float, lo_bad: float, lo_good: float, hi_good: float, hi_bad: float) -> float:
    """100 inside [lo_good, hi_good], falling to 0 at lo_bad / hi_bad."""
    if value < lo_good:
        return lin(value, lo_good, lo_bad)
    if value > hi_good:
        return lin(value, hi_good, hi_bad)
    return 100.0


Part = tuple[str, Optional[float], float, Callable[[float], float], str]
# (metric name, value or None, weight, value -> 0..100, target description)


def _combine(parts: list[Part]) -> Optional[SubScore]:
    avail = [p for p in parts if p[1] is not None]
    total_w = sum(p[2] for p in avail)
    if not avail or total_w <= 0:
        return None
    score, drivers = 0.0, []
    for metric, value, weight, fn, target in avail:
        s = fn(value)
        score += weight / total_w * s
        lost = weight / total_w * (100 - s)
        if lost >= 0.5:
            drivers.append(ScoreDriver(metric=metric, value=round(value, 2),
                                       target=target, points_lost=round(lost, 1)))
    drivers.sort(key=lambda d: -d.points_lost)
    return SubScore(score=round(score, 1), drivers=drivers)


def _rate(count: float, span_s: float, cfg: AnalysisConfig) -> float:
    return count / max(span_s, cfg.min_rate_span_s) * 60


def audio_rates(a: AudioMetrics, cfg: AnalysisConfig) -> dict[str, float]:
    span = a.speaking_span_s
    return {
        "filler_rate": _rate(a.filler_count, span, cfg),
        "repetition_rate": _rate(a.repetition_count, span, cfg),
        "pause_rate": _rate(a.pause_count, span, cfg),
        "long_pause_rate": _rate(a.long_pause_count, span, cfg),
        "hesitation_pause_rate": _rate(a.hesitation_pause_count, span, cfg),
    }


def score_audio(a: AudioMetrics, cfg: AnalysisConfig) -> tuple[SubScore, Optional[SubScore]]:
    r = audio_rates(a, cfg)
    fluency = _combine([
        ("fillers_per_min", r["filler_rate"], 0.35, lambda v: lin(v, 1, 10), "<= 1 per minute"),
        ("hesitation_pauses_per_min", r["hesitation_pause_rate"], 0.25,
         lambda v: lin(v, 1, 8), "<= 1 per minute"),
        ("long_pauses_per_min", r["long_pause_rate"], 0.20, lambda v: lin(v, 0, 3), "none"),
        ("repetitions_per_min", r["repetition_rate"], 0.10, lambda v: lin(v, 0, 4), "none"),
        ("silence_ratio", a.silence_ratio, 0.10, lambda v: lin(v, 0.15, 0.5), "<= 15% of speaking time"),
    ])
    delivery = _combine([
        ("words_per_min", a.wpm if a.word_count >= 10 else None, 0.6,
         lambda v: band(v, 90, 120, 160, 200), "120-160 wpm"),
        ("pitch_variation_semitones", a.pitch_std_semitones, 0.4,
         lambda v: lin(v, 3.0, 1.0), ">= 3 semitones (not monotone)"),
    ])
    return fluency, delivery


def score_vision(
    v: VisionMetrics, duration_s: float, cfg: AnalysisConfig, face_touches_per_min: float
) -> tuple[Optional[SubScore], Optional[SubScore], Optional[SubScore]]:
    reading_per_min = v.reading_notes_s / max(duration_s, cfg.min_rate_span_s) * 60
    eye = _combine([
        ("eye_contact_pct", v.eye_contact_pct, 0.8, lambda x: lin(x, 75, 25), ">= 75%"),
        ("reading_notes_s_per_min", reading_per_min if v.eye_contact_pct is not None else None,
         0.2, lambda x: lin(x, 0, 20), "none"),
    ])
    posture = _combine([
        ("slouch_pct", v.slouch_pct, 0.5, lambda x: lin(x, 5, 40), "<= 5% of time"),
        ("sway_pct", v.sway_pct, 0.3, lambda x: lin(x, 5, 40), "<= 5% of time"),
        ("lean_pct", v.lean_pct, 0.2, lambda x: lin(x, 5, 40), "<= 5% of time"),
    ])
    composure = _combine([
        ("fidget_pct", v.fidget_pct, 0.6, lambda x: lin(x, 5, 40), "<= 5% of time"),
        ("face_touches_per_min", face_touches_per_min if v.hands_visible_pct is not None else None,
         0.4, lambda x: lin(x, 0, 4), "none"),
    ])
    return eye, posture, composure


def overall(scores: Scores) -> Scores:
    used = {k: w for k, w in OVERALL_WEIGHTS.items() if getattr(scores, k) is not None}
    total = sum(used.values())
    if total:
        scores.weights_used = {k: round(w / total, 3) for k, w in used.items()}
        scores.overall = round(sum(getattr(scores, k).score * w for k, w in used.items()) / total, 1)
    return scores
