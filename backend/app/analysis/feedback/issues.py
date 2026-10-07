"""SessionReport -> ranked list of issues with evidence and timestamps.

Issues come from the score drivers (fusion/scoring.py), so they are ordered by
how many points of the overall score each one costs. The text here contains only
facts taken from the report (numbers, times); advice comes from the knowledge base.
"""
from collections import Counter
from typing import Callable

from app.analysis.schemas import Event, Issue, Scores, SessionReport

# score-driver metric -> issue id
DRIVER_TO_ISSUE = {
    "fillers_per_min": "filler_words",
    "hesitation_pauses_per_min": "hesitation_pauses",
    "long_pauses_per_min": "long_pauses",
    "repetitions_per_min": "repetitions",
    "pitch_variation_semitones": "monotone",
    "eye_contact_pct": "low_eye_contact",
    "reading_notes_s_per_min": "reading_notes",
    "slouch_pct": "slouching",
    "lean_pct": "leaning",
    "sway_pct": "swaying",
    "fidget_pct": "fidgeting",
    "face_touches_per_min": "face_touching",
}  # words_per_min and silence_ratio are handled separately

TITLES = {
    "filler_words": "Filler words",
    "hesitation_pauses": "Hesitation pauses in the middle of sentences",
    "long_pauses": "Long pauses",
    "repetitions": "Repeated words and restarts",
    "pace_fast": "Speaking too fast",
    "pace_slow": "Speaking too slowly",
    "monotone": "Flat, monotone delivery",
    "low_eye_contact": "Eye contact with the camera",
    "reading_notes": "Reading from notes",
    "slouching": "Slouching",
    "leaning": "Leaning to one side",
    "swaying": "Swaying or rocking",
    "fidgeting": "Restless hands",
    "face_touching": "Touching your face",
}

MIN_IMPACT = 1.0  # ignore anything costing less than this many overall points
MAX_ISSUES = 6
MAX_MOMENTS = 5


def plural(n: int, word: str) -> str:
    return f"{n} {word}" if n == 1 else f"{n} {word}s"


def mmss(t: float) -> str:
    return f"{int(t // 60)}:{int(t % 60):02d}"


def _events(report: SessionReport, type_: str) -> list[Event]:
    return [e for e in report.events if e.type == type_]


def _hesitations(report: SessionReport) -> list[Event]:
    return [e for e in _events(report, "pause") if e.meta.get("position") == "hesitation"]


def _moments(events: list[Event], limit: int = MAX_MOMENTS, longest: bool = False):
    chosen = sorted(events, key=lambda e: e.start - e.end)[:limit] if longest else events[:limit]
    return sorted((round(e.start, 1), round(e.end, 1)) for e in chosen)


def _at(events: list[Event], limit: int = 3) -> str:
    return ", ".join(mmss(e.start) for e in events[:limit])


# Each builder: (report) -> (evidence list, moments list)
def _fillers(r: SessionReport):
    ev = _events(r, "filler")
    breakdown = ", ".join(f"\"{k}\" x{v}" for k, v in list(r.audio.filler_breakdown.items())[:4])
    rate = r.features.get("filler_rate") or 0.0
    evidence = [f"{plural(r.audio.filler_count, 'filler word')} ({rate:.1f} per minute; aim for 1 or fewer)."]
    if breakdown:
        evidence.append(f"Most frequent: {breakdown}.")
    if ev:
        evidence.append(f"For example at {_at(ev)}.")
    return evidence, _moments(ev)


def _hesitation(r: SessionReport):
    ev = _hesitations(r)
    return ([f"{plural(len(ev), 'pause')} in the middle of a sentence, for example at {_at(ev)}."]
            if ev else [f"{plural(r.audio.hesitation_pause_count, 'mid-sentence pause')}."]), _moments(ev)


def _long_pauses(r: SessionReport):
    ev = _events(r, "long_pause")
    if not ev:
        return [f"{plural(r.audio.long_pause_count, 'pause')} of 2 seconds or more."], []
    longest = max(ev, key=lambda e: e.end - e.start)
    return ([f"{plural(len(ev), 'pause')} of 2 seconds or more; the longest was "
             f"{longest.end - longest.start:.1f} s at {mmss(longest.start)}."], _moments(ev, longest=True))


def _repetitions(r: SessionReport):
    ev = _events(r, "repetition")
    words = Counter(e.meta.get("text", "") for e in ev)
    listed = ", ".join(f"\"{w}\"" for w, _ in words.most_common(3) if w)
    return ([f"{plural(len(ev), 'repeated word')} or restart" + ("s" if len(ev) != 1 else "")
             + (f" (e.g. {listed})." if listed else ".")],
            _moments(ev))


def _pace(r: SessionReport):
    return [f"Your pace was {r.audio.wpm:.0f} words per minute (comfortable range: 120 to 160)."], []


def _monotone(r: SessionReport):
    return [f"Pitch varied by only {r.audio.pitch_std_semitones} semitones (aim for 3 or more)."], []


def _eye(r: SessionReport):
    ev = _events(r, "look_away")
    dirs = Counter(e.meta.get("direction", "?") for e in ev)
    evidence = [f"You looked at the camera {r.vision.eye_contact_pct}% of the time (aim for 75% or more)."]
    if ev:
        longest = max(ev, key=lambda e: e.end - e.start)
        evidence.append(f"{plural(len(ev), 'look-away')}; the longest was {longest.end - longest.start:.1f} s "
                        f"at {mmss(longest.start)}. Most often looking {dirs.most_common(1)[0][0]}.")
    return evidence, _moments(ev, longest=True)


def _reading(r: SessionReport):
    ev = [e for e in _events(r, "look_away") if e.meta.get("reading_notes")]
    return ([f"You spent {r.vision.reading_notes_s:.0f} s looking down for 2 seconds or more at a time, "
             f"for example at {_at(ev)}."] if ev else
            [f"{r.vision.reading_notes_s:.0f} s spent looking down."]), _moments(ev)


def _timed(type_: str, label: str, pct_attr: str):
    def build(r: SessionReport):
        ev = _events(r, type_)
        pct = getattr(r.vision, pct_attr)
        return ([f"{label} for {pct}% of the time across {len(ev)} stretch(es), "
                 f"for example at {_at(ev)}."] if ev else [f"{label} for {pct}% of the time."]), _moments(ev)
    return build


def _face_touch(r: SessionReport):
    ev = _events(r, "face_touch")
    return ([f"Your hand went to your face {plural(len(ev), 'time')}, for example at {_at(ev)}."]
            if ev else [f"{r.vision.face_touch_count} face touches."]), _moments(ev)


BUILDERS: dict[str, Callable] = {
    "filler_words": _fillers, "hesitation_pauses": _hesitation, "long_pauses": _long_pauses,
    "repetitions": _repetitions, "pace_fast": _pace, "pace_slow": _pace, "monotone": _monotone,
    "low_eye_contact": _eye, "reading_notes": _reading,
    "slouching": _timed("slouch", "You were slouched", "slouch_pct"),
    "leaning": _timed("lean", "Your shoulders were tilted", "lean_pct"),
    "swaying": _timed("sway", "You were swaying", "sway_pct"),
    "fidgeting": _timed("fidget", "Your hands were restless", "fidget_pct"),
    "face_touching": _face_touch,
}


def _severity(impact: float) -> str:
    return "high" if impact >= 8 else "medium" if impact >= 3 else "low"


def detect_issues(report: SessionReport) -> list[Issue]:
    scores: Scores = report.scores
    issues: list[Issue] = []
    for sub_name in ("fluency", "delivery", "eye_contact", "posture", "composure"):
        sub = getattr(scores, sub_name)
        weight = scores.weights_used.get(sub_name, 0.0)
        if sub is None:
            continue
        for d in sub.drivers:
            if d.metric == "words_per_min":
                issue_id = "pace_slow" if d.value < 120 else "pace_fast"
            else:
                issue_id = DRIVER_TO_ISSUE.get(d.metric)
            if issue_id is None:
                continue
            impact = d.points_lost * weight
            if impact < MIN_IMPACT:
                continue
            evidence, moments = BUILDERS[issue_id](report)
            issues.append(Issue(id=issue_id, title=TITLES[issue_id], impact=round(impact, 1),
                                severity=_severity(impact), evidence=evidence, moments=moments))
    issues.sort(key=lambda i: -i.impact)
    return issues[:MAX_ISSUES]


def detect_strengths(report: SessionReport) -> list[str]:
    s, out = report.scores, []
    if s.fluency and s.fluency.score >= 80 and report.audio:
        out.append(f"Fluent delivery: only {report.audio.filler_count} filler word(s) and "
                   f"{report.audio.long_pause_count} long pause(s).")
    if s.delivery and s.delivery.score >= 80 and report.audio:
        out.append(f"Good pace and vocal variety ({report.audio.wpm:.0f} words per minute).")
    if s.eye_contact and s.eye_contact.score >= 80 and report.vision:
        out.append(f"Strong eye contact: {report.vision.eye_contact_pct}% of the time on the camera.")
    if s.posture and s.posture.score >= 85:
        out.append("Steady, upright posture throughout.")
    if s.composure and s.composure.score >= 85:
        out.append("Calm, controlled hands with little fidgeting.")
    return out
