"""Run analysis phases from the command line.

    cd backend
    python -m app.analysis.cli preprocess path/to/video.mp4 [--run-id demo]   # phase 1
    python -m app.analysis.cli audio demo                                     # phase 2
    python -m app.analysis.cli vision demo [--debug]                          # phase 3
    python -m app.analysis.cli report demo                                    # phase 4
    python -m app.analysis.cli feedback demo [--topic "Climate change"]       # phase 5
    python -m app.analysis.cli analyze path/to/video.mp4 [--run-id demo]      # phases 1-5

`demo` is a run id (or a run directory path) created by `preprocess`.

Phase 5 is fully offline unless SPEAKWISE_LLM_API_KEY and SPEAKWISE_LLM_MODEL are set
(see app/analysis/feedback/llm.py); then the transcript is sent to that provider.
"""
import argparse
import sys
from pathlib import Path

from app.analysis.config import DEFAULT_CONFIG
from app.analysis.preprocess import PreprocessError, preprocess_video


def _resolve_run_dir(value: str) -> Path:
    path = Path(value)
    return path if path.is_dir() else DEFAULT_CONFIG.runs_dir / value


def cmd_preprocess(video: str, run_id: str | None) -> Path:
    result = preprocess_video(video, run_id=run_id)
    m = result.metadata
    print(f"run dir : {result.run_dir}")
    print(f"duration: {m.duration_s}s  ({m.width}x{m.height})")
    print(f"audio   : {result.audio_path.name}  {m.audio_sample_rate} Hz mono, {m.audio_duration_s}s")
    print(f"frames  : {m.frame_count} @ {m.frame_fps} fps")
    return result.run_dir


def cmd_audio(run_dir: Path) -> None:
    from app.analysis.audio.pipeline import OUTPUT_FILE, analyze_audio

    result = analyze_audio(run_dir)
    m = result.metrics
    if not result.words:
        print("warning: no speech detected in this run (silent or non-speech audio).")
    print(f"transcript : {result.transcript}\n")
    print(f"words {m.word_count} | {m.wpm} wpm | speaking {m.speaking_span_s}s "
          f"(starts at {m.start_delay_s}s) | whisper '{result.asr_model}'")
    print(f"fillers    : {m.filler_count} ({m.fillers_per_min}/min) {m.filler_breakdown}")
    print(f"repetitions: {m.repetition_count}")
    print(f"pauses     : {m.pause_count} (long: {m.long_pause_count}, "
          f"hesitation: {m.hesitation_pause_count}, avg {m.avg_pause_s}s, "
          f"silence {m.silence_ratio:.0%})")
    print(f"prosody    : pitch {m.pitch_mean_hz} Hz, std {m.pitch_std_semitones} st, "
          f"loudness std {m.intensity_std_db} dB")
    print(f"\nsaved {run_dir / OUTPUT_FILE}")


def cmd_vision(run_dir: Path, debug: bool) -> None:
    from app.analysis.vision.pipeline import OUTPUT_FILE, analyze_vision

    result = analyze_vision(run_dir, debug_video=debug)
    m = result.metrics
    print(f"baseline   : {result.baseline}")
    print(f"face seen  : {m.face_visible_pct}% of {m.frames} frames (lost {m.face_lost_s}s)")
    print(f"eye contact: {m.eye_contact_pct}%  | look-aways {m.look_away_count} "
          f"({m.look_away_total_s}s, longest {m.longest_look_away_s}s, "
          f"reading notes {m.reading_notes_s}s)")
    print(f"posture    : slouch {m.slouch_pct}% ({m.slouch_count}x), lean {m.lean_pct}%, "
          f"sway {m.sway_pct}%")
    print(f"hands      : visible {m.hands_visible_pct}%, face touches {m.face_touch_count}, "
          f"fidget {m.fidget_pct}%")
    print(f"head motion: {m.head_motion_deg_s} deg/s")
    print(f"\nsaved {run_dir / OUTPUT_FILE}" + ("  + debug_vision.mp4" if debug else ""))


def cmd_report(run_dir: Path) -> None:
    from app.analysis.fusion.pipeline import OUTPUT_FILE, generate_report

    r = generate_report(run_dir)
    s = r.scores
    print(f"events     : {len(r.events)} on the timeline ({r.duration_s}s, {len(r.segments)} segments)")
    for name in ("fluency", "delivery", "eye_contact", "posture", "composure"):
        sub = getattr(s, name)
        if sub is None:
            print(f"{name:11s}: n/a")
            continue
        why = ", ".join(f"{d.metric}={d.value} (-{d.points_lost})" for d in sub.drivers[:3])
        print(f"{name:11s}: {sub.score:5.1f}   {why}")
    print(f"OVERALL    : {s.overall}  (weights {s.weights_used})")
    if s.ml_overall is not None:
        print(f"ML score   : {s.ml_overall}  ({s.ml_model})")
    for c in r.clusters:
        print(f"struggle   : {c.start}-{c.end}s  {c.counts}  while {c.concurrent_video or 'no body-language events'}")
    for w in r.warnings:
        print(f"warning    : {w}")
    print(f"\nsaved {run_dir / OUTPUT_FILE}")


def cmd_feedback(run_dir: Path, topic: str | None, key_points: list[str] | None) -> None:
    from app.analysis.feedback.pipeline import OUTPUT_FILE, generate_final

    final = generate_final(run_dir, topic=topic, key_points=key_points)
    fb = final.feedback
    print(f"generator  : {fb.generator}\n")
    print(fb.summary)
    for s in fb.strengths:
        print(f"  + {s}")
    for i, issue in enumerate(fb.issues, 1):
        print(f"\n{i}. {issue.title}  [{issue.severity}, -{issue.impact} pts]")
        for e in issue.evidence:
            print(f"   - {e}")
        print(f"   Advice: {issue.advice}")
        if issue.drill:
            print(f"   Drill : {issue.drill}")
    print("\nNext session:")
    for g in fb.practice_plan:
        print(f"  * {g}")
    v = fb.vocabulary
    if v.lexical_diversity is not None:
        print(f"\nvocabulary : diversity {v.lexical_diversity} ({v.diversity_label})")
    for w in v.overused:
        print(f'  overused "{w.word}" x{w.count} -> {", ".join(w.alternatives[:3])}')
    for w in v.filler_alternatives:
        print(f'  filler "{w.word}" x{w.count} -> {w.alternatives[0]}')
    if v.topic_coverage:
        print(f"  topic coverage: {v.topic_coverage['pct']}% (missed: {v.topic_coverage['missed']})")
    print(f"\nsaved {run_dir / OUTPUT_FILE}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="app.analysis.cli")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("preprocess", help="Phase 1: extract audio + frames")
    p.add_argument("video")
    p.add_argument("--run-id", default=None)

    p = sub.add_parser("audio", help="Phase 2: transcript, fillers, pauses, prosody")
    p.add_argument("run", help="run id or run directory from phase 1")

    p = sub.add_parser("vision", help="Phase 3: eye contact, posture, hands")
    p.add_argument("run", help="run id or run directory from phase 1")
    p.add_argument("--debug", action="store_true", help="also write debug_vision.mp4")

    p = sub.add_parser("report", help="Phase 4: unified timeline + scores")
    p.add_argument("run", help="run id or run directory (needs phase 2 and/or 3 done)")

    p = sub.add_parser("feedback", help="Phase 5: advice, vocabulary, practice plan")
    p.add_argument("run", help="run id or run directory (phases 2-4 done)")
    p.add_argument("--topic", default=None)
    p.add_argument("--key-point", action="append", dest="key_points",
                   help="a key point the talk should cover (repeatable)")

    p = sub.add_parser("analyze", help="Run phases 1-5 on a video")
    p.add_argument("video")
    p.add_argument("--run-id", default=None)
    p.add_argument("--topic", default=None)
    p.add_argument("--key-point", action="append", dest="key_points")
    p.add_argument("--debug", action="store_true", help="also write debug_vision.mp4")

    args = parser.parse_args(argv)

    try:
        if args.command == "preprocess":
            cmd_preprocess(args.video, args.run_id)
        elif args.command == "audio":
            cmd_audio(_resolve_run_dir(args.run))
        elif args.command == "vision":
            cmd_vision(_resolve_run_dir(args.run), args.debug)
        elif args.command == "report":
            cmd_report(_resolve_run_dir(args.run))
        elif args.command == "feedback":
            cmd_feedback(_resolve_run_dir(args.run), args.topic, args.key_points)
        elif args.command == "analyze":
            run_dir = cmd_preprocess(args.video, args.run_id)
            print("\n=== audio ===")
            cmd_audio(run_dir)
            print("\n=== vision ===")
            cmd_vision(run_dir, args.debug)
            print("\n=== report ===")
            cmd_report(run_dir)
            print("\n=== feedback ===")
            cmd_feedback(run_dir, args.topic, args.key_points)
    except (PreprocessError, ValueError, FileNotFoundError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
