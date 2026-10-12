"""Single entry point for the whole pipeline (the seam for a future API route).

    from app.analysis.service import analyze_recording
    final = analyze_recording("/path/to/upload.webm", topic="Climate change")

Integration notes (see docs/ANALYSIS_INTEGRATION.md):
  * It is synchronous and CPU/RAM heavy (about 1-3 minutes for a 5-minute video), so
    a route should run it in a background task and return a job id to poll.
  * It does not touch the database; persistence.py maps the result onto your tables.
"""
from pathlib import Path
from typing import Optional

from app.analysis.audio.asr import release_models
from app.analysis.audio.pipeline import analyze_audio
from app.analysis.config import DEFAULT_CONFIG, AnalysisConfig
from app.analysis.feedback.llm import LLMClient
from app.analysis.feedback.pipeline import _FROM_ENV, generate_final
from app.analysis.fusion.pipeline import generate_report
from app.analysis.preprocess import preprocess_video
from app.analysis.schemas import FinalReport
from app.analysis.vision.pipeline import analyze_vision


def analyze_recording(
    video_path: str | Path,
    topic: Optional[str] = None,
    key_points: Optional[list[str]] = None,
    run_id: Optional[str] = None,
    llm: Optional[LLMClient] | object = _FROM_ENV,
    debug_video: bool = False,
    cfg: AnalysisConfig = DEFAULT_CONFIG,
) -> FinalReport:
    """Run phases 1-5 on one recording and return (and save) the final report.

    Raises PreprocessError for unreadable/too-long/silent input.
    Audio and vision run one after the other to keep peak memory low; they are
    independent, so they can be moved to parallel workers later.
    """
    run = preprocess_video(video_path, run_id=run_id, cfg=cfg)
    analyze_audio(run, cfg)
    release_models()  # free the speech model's RAM before the vision phase starts
    analyze_vision(run, cfg, debug_video=debug_video)
    generate_report(run.run_dir, cfg)
    return generate_final(run.run_dir, topic=topic, key_points=key_points, llm=llm, cfg=cfg)
