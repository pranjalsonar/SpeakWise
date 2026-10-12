"""process_session: the single entry point a desktop app (or the notebook) calls.

    from speakwise.pipeline import process_session
    report = process_session("talk.mp4", topic, reading_material, speaking_duration=180)
    report.to_json()                     # validated JSON
    report.model_dump()                  # plain dict

Error handling: process_session always returns a SessionReport. Problems are recorded in
`errors` (with module and stage) and the affected sections get status failed/unavailable;
the remaining modules still run. Only invalid arguments raise (ValueError).
Temporary media are deleted at the end unless config.keep_artifacts is True, also when the
run is interrupted.
"""
from __future__ import annotations

import hashlib
import threading
import time
import traceback
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

import psutil

from speakwise import __version__
from speakwise.audio_metrics import analyze_audio, vad_segments
from speakwise.config import PipelineConfig
from speakwise.context_matching import evaluate_context
from speakwise.environment import gpu_info, inspect_environment
from speakwise.media_preprocessing import PreprocessError, preprocess_mp4
from speakwise.report_aggregation import build_suggestions, collect_warnings
from speakwise.schemas import (AudioAnalysis, ContextEvaluation, ErrorRecord, InputValidation, Metric, Preprocessing,
                               ProcessingMetadata, SessionMetadata, SessionReport, Status, Transcription, VideoAnalysis)


class _PeakMemory:
    """Samples this process's RSS every 0.2 s to record the peak."""

    def __init__(self):
        self.peak = 0
        self._stop = threading.Event()
        self._proc = psutil.Process()
        self._t = threading.Thread(target=self._run, daemon=True)

    def _run(self):
        while not self._stop.is_set():
            self.peak = max(self.peak, self._proc.memory_info().rss)
            self._stop.wait(0.2)

    def __enter__(self):
        self._t.start()
        return self

    def __exit__(self, *exc):
        self._stop.set()
        self._t.join(timeout=1)


def _blank(status: Status, reason: str):
    m = lambda u: Metric.missing(u, reason, status if status != Status.ok else Status.unavailable)  # noqa: E731
    audio = AudioAnalysis(status=status, speaking_time_s=m("seconds"), speech_span_s=m("seconds"),
                          words_per_minute=m("words_per_minute"), warnings=[reason])
    video = VideoAnalysis(status=status, frames_analyzed=m("count"), usable_frame_pct=m("percent"),
                          face_visible_pct=m("percent"), head_toward_camera_pct=m("percent"),
                          camera_directed_gaze_pct=m("percent"), warnings=[reason])
    return audio, video


def _blank_context(cfg: PipelineConfig, status: Status, reason: str) -> ContextEvaluation:
    from speakwise.context_matching import RUBRIC_VERSION

    m = lambda u: Metric.missing(u, reason, status)  # noqa: E731
    return ContextEvaluation(status=status, rubric_version=RUBRIC_VERSION, topic_relevance=m("score_0_100"),
                             key_point_coverage_raw=m("percent"), key_point_coverage_adjusted=m("percent"),
                             context_alignment=m("score_0_100"), provisional_threshold=cfg.ctx_threshold,
                             warnings=[reason])


def process_session(
    mp4_path: str | Path,
    topic: str,
    reading_material: str,
    speaking_duration: Optional[float] = None,
    config: Optional[PipelineConfig | dict] = None,
    *,
    key_points: Optional[list[str]] = None,
    save: bool = True,
    transcriber: Optional[Callable] = None,
    video_analyzer: Optional[Callable] = None,
    embedder: Any = "auto",
    nli: Any = "auto",
) -> SessionReport:
    """Analyse one recording against its topic and the exact reading material.

    transcriber / video_analyzer / embedder / nli let tests inject documented test doubles;
    leave them at their defaults for real analysis."""
    if not isinstance(topic, str) or not isinstance(reading_material, str):
        raise ValueError("topic and reading_material must be strings")
    cfg = PipelineConfig.from_dict(config) if isinstance(config, dict) else (config or PipelineConfig())
    cfg.validate()
    t_start = time.perf_counter()
    timings: dict[str, float] = {}
    errors: list[ErrorRecord] = []
    env = inspect_environment(str(cfg.work_dir) if cfg.work_dir else None)
    session_id = f"{datetime.now():%Y%m%d-%H%M%S}-{uuid.uuid4().hex[:6]}"
    meta = SessionMetadata(
        session_id=session_id, created_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        pipeline_version=__version__, input_file=Path(mp4_path).name, topic=topic,
        reading_material_sha256=hashlib.sha256(reading_material.encode("utf-8")).hexdigest(),
        reading_material_words=len(reading_material.split()), speaking_duration_selected_s=speaking_duration)

    def fail(module: str, stage: str, exc: BaseException, recoverable: bool = True) -> None:
        errors.append(ErrorRecord(module=module, stage=stage, type=type(exc).__name__,
                                  message=str(exc)[:500] or traceback.format_exc(limit=1)[-300:], recoverable=recoverable))

    transcription = Transcription(status=Status.skipped, warnings=["Transcription did not run."])
    audio_a, video_a = _blank(Status.skipped, "module not run")
    context = _blank_context(cfg, Status.skipped, "module not run")
    prep = None
    models_used: dict[str, Any] = {}

    with _PeakMemory() as mem:
        try:
            # ---------------------------------------------------- 1. preprocessing
            t = time.perf_counter()
            try:
                prep = preprocess_mp4(mp4_path, cfg, speaking_duration)
                validation, preprocessing = prep.validation, prep.preprocessing
                errors += prep.errors
            except PreprocessError as exc:
                fail("preprocessing", "validation", exc, recoverable=False)
                validation = InputValidation(status=Status.failed, warnings=[str(exc)])
                preprocessing = Preprocessing(status=Status.failed, warnings=[str(exc)])
            timings["preprocessing"] = round(time.perf_counter() - t, 2)

            audio_ok = prep is not None and prep.audio_usable and "audio" in cfg.enabled_modules
            video_ok = prep is not None and prep.video_usable and "video" in cfg.enabled_modules

            # ------------------------------------------- 2. transcription + audio
            if not audio_ok:
                reason = ("disabled in configuration" if "audio" not in cfg.enabled_modules
                          else "no usable audio (see input_validation)")
                st = Status.skipped if "audio" not in cfg.enabled_modules else Status.unavailable
                transcription = Transcription(status=st, warnings=[f"Not transcribed: {reason}."])
                audio_a, _ = _blank(st, f"Audio analysis not run: {reason}.")
            else:
                audio, rate = prep.load_audio()
                t = time.perf_counter()
                try:
                    if transcriber is not None:
                        transcription = transcriber(audio, rate, cfg, env)
                    else:
                        from speakwise.audio_transcription import release_models, transcribe

                        transcription = transcribe(audio, rate, cfg, env)
                        release_models()  # free ASR memory before the vision/context models load
                    models_used["asr"] = transcription.model
                except Exception as exc:  # noqa: BLE001
                    fail("transcription", "speech_recognition", exc)
                    transcription = Transcription(status=Status.failed, warnings=[f"Speech recognition failed: {exc}"])
                timings["transcription"] = round(time.perf_counter() - t, 2)

                t = time.perf_counter()
                try:
                    speech = vad_segments(audio, rate, cfg)
                    audio_a = analyze_audio(audio, rate, transcription, prep.audio_duration_s or 0.0, cfg, speech=speech)
                    if transcription.status == Status.failed:
                        audio_a.warnings.append("Transcript unavailable: only signal-level measures are valid.")
                except Exception as exc:  # noqa: BLE001
                    fail("audio_analysis", "metrics", exc)
                    audio_a, _ = _blank(Status.failed, f"Audio analysis failed: {exc}")
                timings["audio_analysis"] = round(time.perf_counter() - t, 2)
                del audio

            # --------------------------------------------------------- 3. video
            if not video_ok:
                reason = ("disabled in configuration" if "video" not in cfg.enabled_modules
                          else "no usable video (see input_validation)")
                st = Status.skipped if "video" not in cfg.enabled_modules else Status.unavailable
                _, video_a = _blank(st, f"Video analysis not run: {reason}.")
            else:
                t = time.perf_counter()
                try:
                    from speakwise.video_analysis import analyze_video

                    video_a = analyze_video(prep, cfg, video_analyzer)
                    models_used["video"] = video_a.model
                except Exception as exc:  # noqa: BLE001
                    fail("video_analysis", "landmarks", exc)
                    _, video_a = _blank(Status.failed, f"Video analysis failed: {exc}")
                timings["video_analysis"] = round(time.perf_counter() - t, 2)

            # ------------------------------------------------------- 4. context
            if "context" not in cfg.enabled_modules:
                context = _blank_context(cfg, Status.skipped, "Context evaluation disabled in configuration.")
            elif transcription.status in (Status.failed, Status.skipped) or (transcription.status == Status.unavailable and not transcription.words):
                context = _blank_context(cfg, Status.unavailable,
                                         "Context evaluation needs a transcript; none is available.")
            else:
                t = time.perf_counter()
                try:
                    context = evaluate_context(topic, reading_material, transcription, cfg,
                                               speaking_duration_s=speaking_duration, key_points=key_points,
                                               embedder=embedder, nli=nli)
                    models_used["context"] = {"embedder": context.method.get("embedder"), "nli": context.method.get("nli")}
                except Exception as exc:  # noqa: BLE001
                    fail("context_evaluation", "evaluate", exc)
                    context = _blank_context(cfg, Status.failed, f"Context evaluation failed: {exc}")
                timings["context_evaluation"] = round(time.perf_counter() - t, 2)
        finally:
            if prep is not None:
                prep.workspace.cleanup()  # also on errors and KeyboardInterrupt

    gpus = gpu_info()
    report = SessionReport(
        session_metadata=meta, input_validation=validation, preprocessing=preprocessing,
        transcription=transcription, audio_analysis=audio_a, video_analysis=video_a, context_evaluation=context,
        processing_metadata=ProcessingMetadata(
            environment=env, config=cfg.to_dict(), models=models_used, timings_s=timings,
            peak_rss_mb=round(mem.peak / 2**20, 1), gpu_memory_mb=gpus[0]["memory_used_mb"] if gpus else None,
            total_time_s=round(time.perf_counter() - t_start, 2)),
        errors=errors)
    report.improvement_suggestions = build_suggestions(report, cfg.ctx_threshold)
    report.warnings = collect_warnings(report)
    report = SessionReport.model_validate(report.model_dump())  # final validation of the whole contract
    if save:
        save_report(report, cfg.output_dir)
    return report


def save_report(report: SessionReport, output_dir: str | Path) -> Path:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"report_{report.session_metadata.session_id}.json"
    path.write_text(report.to_json(), encoding="utf-8")
    return path
