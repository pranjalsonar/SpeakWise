"""Phase 4 entry point: audio_analysis.json + vision_analysis.json -> session_report.json."""
from pathlib import Path
from typing import Optional

from app.analysis.audio.pipeline import OUTPUT_FILE as AUDIO_FILE
from app.analysis.config import DEFAULT_CONFIG, AnalysisConfig
from app.analysis.fusion import ml, scoring, timeline
from app.analysis.preprocess import PreprocessError, load_run
from app.analysis.schemas import AudioAnalysis, Scores, SessionReport, VisionAnalysis
from app.analysis.vision.pipeline import OUTPUT_FILE as VISION_FILE

OUTPUT_FILE = "session_report.json"


def build_report(
    run_id: str,
    duration_s: float,
    audio: Optional[AudioAnalysis],
    vision: Optional[VisionAnalysis],
    cfg: AnalysisConfig = DEFAULT_CONFIG,
    model_path: Path = ml.MODEL_PATH,
) -> SessionReport:
    """Pure function (no file I/O besides an optional ML model), easy to test."""
    if audio is None and vision is None:
        raise ValueError("Need at least one of audio / vision analysis.")

    events = sorted((audio.events if audio else []) + (vision.events if vision else []),
                    key=lambda e: (e.start, e.end))
    warnings: list[str] = []
    scores = Scores()
    rates: dict[str, float] = {}

    if audio:
        a = audio.metrics
        rates = scoring.audio_rates(a, cfg)
        scores.fluency, scores.delivery = scoring.score_audio(a, cfg)
        if a.word_count == 0:
            warnings.append("No speech was detected; audio scores are not meaningful.")
        elif audio.asr_model in ("tiny", "base"):
            warnings.append(
                f"Transcribed with the small '{audio.asr_model}' model: filler words (um/uh) "
                "may be under-counted. Use a larger model when RAM allows.")
        if a.word_count >= 50 and a.filler_count == 0:
            warnings.append("No fillers found in a long speech; Whisper may have removed "
                            "them from the transcript, so the count could be too low.")
        if 0 < a.word_count and a.speaking_span_s < cfg.min_rate_span_s:
            warnings.append("Very short speech; per-minute rates are less reliable.")

    if vision:
        v = vision.metrics
        per_min = v.face_touch_count / max(duration_s, cfg.min_rate_span_s) * 60
        scores.eye_contact, scores.posture, scores.composure = scoring.score_vision(
            v, duration_s, cfg, per_min)
        if v.face_visible_pct < 70:
            warnings.append(f"Face visible in only {v.face_visible_pct}% of frames; "
                            "body-language results are unreliable.")
        if vision.baseline.get("source") != "calibration":
            warnings.append("No usable calibration at the start; the baseline is the median "
                            "of the whole video, so posture/gaze are relative to the average.")
    if audio is None:
        warnings.append("Audio analysis missing; speech scores omitted.")
    if vision is None:
        warnings.append("Vision analysis missing; body-language scores omitted.")

    scoring.overall(scores)
    features = ml.feature_vector(audio.metrics if audio else None,
                                 vision.metrics if vision else None, rates, duration_s)
    scores.ml_overall, scores.ml_model = ml.predict(features, model_path)

    return SessionReport(
        run_id=run_id,
        duration_s=duration_s,
        transcript=audio.transcript if audio else None,
        events=events,
        audio=audio.metrics if audio else None,
        vision=vision.metrics if vision else None,
        segments=timeline.build_segments(events, audio.words if audio else [], duration_s,
                                         audio is not None, vision is not None, cfg),
        clusters=timeline.build_clusters(events, cfg),
        correlations=timeline.build_correlations(events, duration_s),
        scores=scores,
        features=features,
        warnings=warnings,
    )


def generate_report(run_dir: str | Path, cfg: AnalysisConfig = DEFAULT_CONFIG) -> SessionReport:
    """Read the phase 2/3 outputs from a run directory and write session_report.json."""
    run = load_run(run_dir)
    audio_path, vision_path = run.run_dir / AUDIO_FILE, run.run_dir / VISION_FILE
    audio = (AudioAnalysis.model_validate_json(audio_path.read_text(encoding="utf-8"))
             if audio_path.is_file() else None)
    vision = (VisionAnalysis.model_validate_json(vision_path.read_text(encoding="utf-8"))
              if vision_path.is_file() else None)
    if audio is None and vision is None:
        raise PreprocessError("Run phase 2 (audio) and/or phase 3 (vision) first.")

    report = build_report(run.metadata.run_id, run.metadata.duration_s, audio, vision, cfg)
    (run.run_dir / OUTPUT_FILE).write_text(report.model_dump_json(indent=2), encoding="utf-8")
    return report
