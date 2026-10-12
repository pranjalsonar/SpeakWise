"""Unified timeline views over the merged audio + video events."""
from collections import Counter

from app.analysis.config import AnalysisConfig
from app.analysis.schemas import DisfluencyCluster, Event, Segment, Word


def overlap(a0: float, a1: float, b0: float, b1: float) -> float:
    return max(0.0, min(a1, b1) - max(a0, b0))


def is_disfluency(e: Event) -> bool:
    return e.type in ("filler", "repetition", "long_pause") or (
        e.type == "pause" and e.meta.get("position") == "hesitation"
    )


def _label(e: Event) -> str:
    if e.type == "filler":
        return e.meta.get("label", "filler")
    if e.type == "pause":
        return "hesitation_pause"
    return e.type


# ---------------------------------------------------------------- segments

def build_segments(
    events: list[Event], words: list[Word], duration: float,
    has_audio: bool, has_video: bool, cfg: AnalysisConfig,
) -> list[Segment]:
    edges = [0.0]
    while edges[-1] + cfg.segment_s < duration:
        edges.append(edges[-1] + cfg.segment_s)
    edges.append(duration)
    if len(edges) > 2 and edges[-1] - edges[-2] < 5.0:  # fold a tiny tail into the last window
        edges.pop(-2)

    filler_starts = {e.start for e in events if e.type == "filler"}
    segments = []
    for a, b in zip(edges, edges[1:]):
        length = b - a

        def in_window(e: Event) -> bool:
            return a <= e.start < b

        def seconds(type_: str) -> float:
            return round(sum(overlap(a, b, e.start, e.end)
                             for e in events if e.type == type_), 2)

        seg = Segment(start=round(a, 2), end=round(b, 2))
        if has_audio:
            spoken = [w for w in words if a <= w.start < b and w.start not in filler_starts]
            seg.words_per_min = round(len(spoken) / length * 60, 1) if length > 0 else None
            seg.fillers = sum(e.type == "filler" and in_window(e) for e in events)
            seg.repetitions = sum(e.type == "repetition" and in_window(e) for e in events)
            seg.pauses = sum(e.type in ("pause", "long_pause") and in_window(e) for e in events)
            seg.long_pauses = sum(e.type == "long_pause" and in_window(e) for e in events)
        if has_video:
            away, lost = seconds("look_away"), seconds("face_lost")
            seen = length - lost
            seg.look_away_s = away
            seg.eye_contact_pct = round(100 * (1 - away / seen), 1) if seen > 1.0 else None
            seg.slouch_s = seconds("slouch")
            seg.fidget_s = seconds("fidget")
            seg.face_touches = sum(e.type == "face_touch" and in_window(e) for e in events)
        segments.append(seg)
    return segments


# ---------------------------------------------------------------- clusters

def build_clusters(events: list[Event], cfg: AnalysisConfig) -> list[DisfluencyCluster]:
    dis = sorted((e for e in events if e.source == "audio" and is_disfluency(e)),
                 key=lambda e: e.start)
    groups: list[list[Event]] = []
    for e in dis:
        if groups and e.start - max(x.end for x in groups[-1]) <= cfg.cluster_gap_s:
            groups[-1].append(e)
        else:
            groups.append([e])

    video = [e for e in events if e.source == "video"]
    clusters = []
    for g in groups:
        if len(g) < cfg.cluster_min_events:
            continue
        start, end = g[0].start, max(x.end for x in g)
        concurrent = Counter(v.type for v in video
                             if overlap(start - 0.5, end + 0.5, v.start, v.end) > 0)
        clusters.append(DisfluencyCluster(
            start=round(start, 2), end=round(end, 2),
            counts=dict(Counter(_label(e) for e in g)),
            concurrent_video=dict(concurrent),
        ))
    return clusters


# ------------------------------------------------------------ correlations

def co_occurrence(
    audio_events: list[Event], video_events: list[Event], duration: float, pad: float = 0.5
) -> dict:
    """How often audio events coincide with a video behaviour, versus how much of
    the session that behaviour covers anyway (the chance level)."""
    hits = sum(
        any(overlap(a.start - pad, a.end + pad, v.start, v.end) > 0 for v in video_events)
        for a in audio_events
    )
    covered = sum(v.end - v.start for v in video_events)
    return {
        "events": len(audio_events),
        "overlapping": hits,
        "fraction": round(hits / len(audio_events), 2) if audio_events else None,
        "baseline_fraction": round(min(covered / duration, 1.0), 2) if duration > 0 else None,
    }


def build_correlations(events: list[Event], duration: float) -> dict:
    by = lambda t: [e for e in events if e.type == t]  # noqa: E731
    away = by("look_away") + by("face_lost")
    pauses = by("pause") + by("long_pause")
    hesitations = [e for e in pauses if e.meta.get("position") == "hesitation"] + by("long_pause")
    disfluent = [e for e in events if e.source == "audio" and is_disfluency(e)]
    return {
        "fillers_vs_look_away": co_occurrence(by("filler"), away, duration),
        "hesitations_vs_look_away": co_occurrence(hesitations, away, duration),
        "disfluencies_vs_slouch": co_occurrence(disfluent, by("slouch"), duration),
        "disfluencies_vs_face_touch": co_occurrence(disfluent, by("face_touch"), duration),
        "disfluencies_vs_fidget": co_occurrence(disfluent, by("fidget"), duration),
    }
