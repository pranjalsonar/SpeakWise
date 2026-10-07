"""Pause detection and classification.

Primary source: silences between VAD speech segments (independent of the ASR,
so it still works when Whisper's word timestamps are loose). Secondary source:
gaps between ASR words that the VAD missed (e.g. low background noise that the
VAD labelled as speech).

Silence before the first word and after the last word is NOT a pause; it is
reported as start_delay_s.

Each pause event has meta:
    duration_s
    position   "sentence_boundary" | "clause_boundary" | "hesitation"
               (a pause mid-phrase is a hesitation; at a boundary it is a
               healthy rhetorical pause)
    filled     True if a filler (um/uh/...) sits next to the pause
    detected_by "vad" | "asr"
"""
from bisect import bisect_right

from app.analysis.config import AnalysisConfig
from app.analysis.schemas import Event, Word

_TOL = 0.2  # seconds of slack when matching a VAD gap to neighbouring words


def detect_pauses(
    words: list[Word],
    segments: list[tuple[float, float]],
    fillers: list[Event],
    cfg: AnalysisConfig,
) -> list[Event]:
    if not words:
        return []

    span_start, span_end = words[0].start, words[-1].end
    raw: list[tuple[float, float, str]] = []

    for (_, prev_end), (next_start, _) in zip(segments, segments[1:]):
        if prev_end >= span_start - _TOL and next_start <= span_end + _TOL:
            raw.append((prev_end, next_start, "vad"))

    for a, b in zip(words, words[1:]):
        if b.start - a.end >= cfg.pause_min_s:
            raw.append((a.end, b.start, "asr"))

    # keep VAD gaps; add ASR gaps only if they don't overlap one
    vad_gaps = [(s, e) for s, e, src in raw if src == "vad"]
    merged = list(raw[: len(vad_gaps)])
    for s, e, src in raw[len(vad_gaps):]:
        if not any(s < ve and e > vs for vs, ve in vad_gaps):
            merged.append((s, e, src))
    merged.sort()

    ends = [w.end for w in words]
    events: list[Event] = []
    for start, end, src in merged:
        duration = end - start
        if duration < cfg.pause_min_s:
            continue
        idx = bisect_right(ends, start + _TOL) - 1  # last word ending at/before the pause
        prev_text = words[idx].text.rstrip() if idx >= 0 else ""
        if prev_text[-1:] in (".", "?", "!"):
            position = "sentence_boundary"
        elif prev_text[-1:] in (",", ";", ":"):
            position = "clause_boundary"
        else:
            position = "hesitation"
        filled = any(f.end >= start - _TOL and f.start <= end + _TOL for f in fillers)
        events.append(
            Event(
                type="long_pause" if duration >= cfg.long_pause_s else "pause",
                source="audio",
                start=round(start, 3),
                end=round(end, 3),
                meta={
                    "duration_s": round(duration, 3),
                    "position": position,
                    "filled": filled,
                    "detected_by": src,
                },
            )
        )
    return events
