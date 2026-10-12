"""Aggregation: improvement suggestions and the top-level warning list.

Suggestions are rule-based and evidence-grounded: each rule fires only when its metrics were
actually measured (status ok/warning), cites the numbers and timestamps it used, and lists
the report paths it relied on. There is deliberately no overall "confidence" score.
"""
from __future__ import annotations

from typing import Optional

from speakwise.schemas import Issue, Metric, SessionReport, Status, Suggestion

# Rule thresholds (heuristics from public-speaking guidance; tune with real data)
FILLERS_PER_MIN = 3.0
REPEATS_PER_100_WORDS = 2.0
LONG_PAUSES = 2
MID_SENTENCE_PAUSES_PER_MIN = 4.0
FAST_WPM, SLOW_WPM = 175.0, 95.0
GAZE_PCT = 50.0
HEAD_LOWERED_PCT = 25.0
UNCLEAR_SEGMENTS = 2


def _ok(m: Optional[Metric]) -> bool:
    return m is not None and m.status.has_value


def _mmss(t: float) -> str:
    return f"{int(t // 60)}:{int(t % 60):02d}"


def build_suggestions(r: SessionReport, provisional_threshold: float) -> list[Suggestion]:
    out: list[Suggestion] = []
    aa, va, ce, tr = r.audio_analysis, r.video_analysis, r.context_evaluation, r.transcription
    asr_certainty = "estimate" if tr.status == Status.warning else "measured"

    # ---- fluency: fillers
    f = aa.fillers
    if f and _ok(f.per_minute) and f.per_minute.value >= FILLERS_PER_MIN and f.total.value >= 3:
        top = ", ".join(f'"{k}" x{v}' for k, v in list(f.by_type.items())[:3])
        out.append(Suggestion(
            id="reduce_fillers", area="fluency", title="Replace filler words with short silent pauses",
            suggestion="When you need a moment to think, close your mouth and pause instead of saying a filler. "
                       "Target your most frequent filler first.",
            evidence=[f"{int(f.total.value)} fillers ({f.per_minute.value:.1f} per minute; {f.per_minute.denominator})",
                      f"Most frequent: {top}"],
            based_on=["audio_analysis.fillers.per_minute", "audio_analysis.fillers.by_type"],
            moments=[e.start for e in f.events[:5]], certainty=asr_certainty))

    # ---- fluency: repetitions
    rp = aa.repetitions
    if rp and _ok(rp.per_100_words) and rp.per_100_words.value >= REPEATS_PER_100_WORDS:
        ev = [e for e in rp.events if e.type in ("word_repetition", "phrase_repetition")]
        out.append(Suggestion(
            id="avoid_restarts", area="fluency", title="Avoid restarting words and phrases",
            suggestion="Decide the first few words of a sentence before you start it; if you stumble, pause and "
                       "continue rather than repeating.",
            evidence=[f"{len(ev)} accidental repetitions ({rp.per_100_words.value:.1f} per 100 words)"]
                     + [f'"{e.text}" at {_mmss(e.start)}' for e in ev[:3]],
            based_on=["audio_analysis.repetitions.per_100_words"], moments=[e.start for e in ev[:5]],
            certainty=asr_certainty))

    # ---- pauses
    pa = aa.pauses
    if pa and _ok(pa.long_pauses) and pa.status != Status.unavailable:
        mid = [e for e in pa.events if e.details.get("position") == "mid_sentence"]
        span_min = (aa.speech_span_s.value or 0) / 60 if _ok(aa.speech_span_s) else 0
        if pa.long_pauses.value >= LONG_PAUSES:
            longs = [e for e in pa.events if e.type == "long_pause"]
            out.append(Suggestion(
                id="long_pauses", area="pauses", title="Shorten long silences",
                suggestion="Long silences often mean losing the thread. Keep short keyword notes and use a bridge "
                           "phrase (\"The key point here is...\") to restart within two seconds.",
                evidence=[f"{int(pa.long_pauses.value)} pauses of {pa.thresholds['long_pause_min_s']:.0f}s or more; "
                          f"longest {pa.longest_pause_s.value:.1f}s"],
                based_on=["audio_analysis.pauses.long_pauses"], moments=[e.start for e in longs[:5]], certainty="measured"))
        elif span_min > 0 and len(mid) / span_min >= MID_SENTENCE_PAUSES_PER_MIN:
            out.append(Suggestion(
                id="pause_placement", area="pauses", title="Pause at the end of ideas, not mid-sentence",
                suggestion="Finish the sentence, then pause. Pauses at sentence ends sound deliberate; pauses inside "
                           "a phrase sound like hesitation.",
                evidence=[f"{len(mid)} pauses inside sentences ({len(mid) / span_min:.1f} per minute)"],
                based_on=["audio_analysis.pauses.events"], moments=[e.start for e in mid[:5]], certainty=asr_certainty))

    # ---- pace
    wpm = aa.words_per_minute
    if _ok(wpm):
        if wpm.value > FAST_WPM:
            out.append(Suggestion(id="pace_fast", area="pace", title="Slow down slightly",
                                  suggestion="Aim for roughly 120-160 words per minute; breathe at each full stop.",
                                  evidence=[f"{wpm.value:.0f} words per minute"], based_on=["audio_analysis.words_per_minute"],
                                  certainty=asr_certainty))
        elif wpm.value < SLOW_WPM and not (pa and _ok(pa.long_pauses) and pa.long_pauses.value >= LONG_PAUSES):
            out.append(Suggestion(id="pace_slow", area="pace", title="Keep a steadier pace",
                                  suggestion="Rehearse key terms beforehand so they come easily; aim for 120-160 words per minute.",
                                  evidence=[f"{wpm.value:.0f} words per minute"], based_on=["audio_analysis.words_per_minute"],
                                  certainty=asr_certainty))

    # ---- clarity and recording quality
    cl, q = aa.clarity, aa.audio_quality
    if cl and _ok(cl.unclear_segments) and cl.unclear_segments.value >= UNCLEAR_SEGMENTS:
        causes = {s.details.get("likely_cause", "") for s in cl.segments}
        out.append(Suggestion(
            id="clarity", area="clarity", title="Some passages were hard to recognise",
            suggestion="Speak a little more slowly and fully finish word endings in these passages, and check that "
                       "the microphone is close and the room is quiet.",
            evidence=[f"{int(cl.unclear_segments.value)} unclear segments ({cl.unclear_speech_s.value:.1f}s)",
                      "Likely causes: " + "; ".join(sorted(c for c in causes if c))],
            based_on=["audio_analysis.clarity"], moments=[s.start for s in cl.segments[:5]], certainty="estimate"))
    if q and q.warnings:
        out.append(Suggestion(id="audio_setup", area="recording", title="Improve the audio recording",
                              suggestion="Record closer to the microphone in a quiet room, and keep input volume below clipping.",
                              evidence=list(q.warnings), based_on=["audio_analysis.audio_quality"], certainty="measured"))

    # ---- camera / gaze / posture
    if va.status == Status.unavailable or (_ok(va.usable_frame_pct) and va.usable_frame_pct.value < 70):
        out.append(Suggestion(
            id="camera_setup", area="recording", title="Adjust the camera so your face is clearly visible",
            suggestion="Place the camera at eye level, face a light source, and keep your head and shoulders in frame. "
                       "Visual feedback could not be measured reliably.",
            evidence=[w for w in va.warnings][:2] or ["Few frames had a usable face."],
            based_on=["video_analysis.usable_frame_pct"], certainty="measured"))
    elif _ok(va.camera_directed_gaze_pct) and va.camera_directed_gaze_pct.value < GAZE_PCT:
        out.append(Suggestion(
            id="gaze", area="gaze", title="Look toward the camera more often",
            suggestion="On video, eye contact means looking at the lens. Glance at notes briefly between ideas and "
                       "return to the camera.",
            evidence=[f"Estimated camera-directed gaze {va.camera_directed_gaze_pct.value:.0f}% "
                      f"({va.camera_directed_gaze_pct.denominator})"],
            based_on=["video_analysis.camera_directed_gaze_pct"], moments=[e.start for e in va.looking_away_events[:5]],
            certainty="estimate"))
    hl = va.posture.get("head_lowered_pct")
    if _ok(hl) and hl.value >= HEAD_LOWERED_PCT:
        out.append(Suggestion(
            id="posture", area="posture", title="Keep your head up",
            suggestion="Raise the camera or your notes to eye level so you don't look down for long periods.",
            evidence=[f"Head lowered toward the shoulders {hl.value:.0f}% of the time (relative to your own median)"],
            based_on=["video_analysis.posture.head_lowered_pct"], moments=[e.start for e in va.posture_events[:5]],
            certainty="estimate"))

    # ---- content
    if ce.status not in (Status.unavailable, Status.failed, Status.skipped):
        if _ok(ce.topic_relevance) and ce.topic_relevance.value < provisional_threshold:
            out.append(Suggestion(
                id="stay_on_topic", area="content", title="Tie more of the talk to the topic and reading",
                suggestion="Link each point back to the topic, and use examples from the reading material.",
                evidence=[f"Topic relevance {ce.topic_relevance.value:.0f}/100 (provisional target {provisional_threshold:.0f})"]
                         + [f'Off-topic at {_mmss(s.start)}: "{(s.text or "")[:80]}"' for s in ce.off_topic_segments[:2] if s.details.get("timestamps")],
                based_on=["context_evaluation.topic_relevance", "context_evaluation.off_topic_segments"],
                moments=[s.start for s in ce.off_topic_segments[:5] if s.details.get("timestamps")], certainty="estimate"))
        if _ok(ce.key_point_coverage_adjusted) and ce.key_point_coverage_adjusted.value < 50:
            missed = [k.text for k in ce.key_points if not k.covered][:3]
            out.append(Suggestion(
                id="cover_key_points", area="content", title="Cover more of the main points",
                suggestion="Plan two or three main points from the reading before you start speaking.",
                evidence=[f"Key-point coverage {ce.key_point_coverage_adjusted.value:.0f}% of what is expected for this "
                          f"duration"] + [f"Not covered: {m}" for m in missed],
                based_on=["context_evaluation.key_point_coverage_adjusted", "context_evaluation.key_points"],
                certainty="estimate"))
        inc = [c for c in ce.claims if c.label == "potentially_inconsistent"]
        if inc:
            out.append(Suggestion(
                id="check_facts", area="content", title="Re-check statements against the reading",
                suggestion="These statements may differ from the reading material. Compare them with the source.",
                evidence=[f'"{c.text[:100]}" vs. material: "{(c.evidence or "")[:100]}"' for c in inc[:3]],
                based_on=["context_evaluation.claims"], moments=[c.start for c in inc if c.start is not None][:5],
                certainty="estimate"))
    return out


def collect_warnings(r: SessionReport) -> list[Issue]:
    issues: list[Issue] = []
    sections = {
        "input_validation": r.input_validation, "preprocessing": r.preprocessing, "transcription": r.transcription,
        "audio_analysis": r.audio_analysis, "audio_analysis.fillers": r.audio_analysis.fillers,
        "audio_analysis.repetitions": r.audio_analysis.repetitions, "audio_analysis.pauses": r.audio_analysis.pauses,
        "audio_analysis.clarity": r.audio_analysis.clarity, "audio_analysis.audio_quality": r.audio_analysis.audio_quality,
        "video_analysis": r.video_analysis, "context_evaluation": r.context_evaluation}
    seen = set()
    for name, sec in sections.items():
        if sec is None:
            continue
        for w in sec.warnings:
            if (name, w) not in seen:
                seen.add((name, w))
                issues.append(Issue(module=name, code=f"{name.split('.')[-1]}_warning", message=w))
    return issues
