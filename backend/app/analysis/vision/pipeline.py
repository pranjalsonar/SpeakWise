"""Phase 3 entry point: run_dir (from phase 1) -> vision_analysis.json."""
from pathlib import Path

from app.analysis.config import DEFAULT_CONFIG, AnalysisConfig
from app.analysis.preprocess import PreprocessResult, load_run
from app.analysis.schemas import VisionAnalysis
from app.analysis.vision.behaviors import analyze_behaviors
from app.analysis.vision.landmarks import extract_features, save_features_csv

OUTPUT_FILE = "vision_analysis.json"
FEATURES_FILE = "vision_features.csv"


def analyze_vision(
    run: str | Path | PreprocessResult,
    cfg: AnalysisConfig = DEFAULT_CONFIG,
    debug_video: bool = False,
) -> VisionAnalysis:
    if not isinstance(run, PreprocessResult):
        run = load_run(run)
    m = run.metadata

    table = extract_features(run.frames_dir, Path(m.frames_pattern).name, m.frame_count, m.frame_fps)
    save_features_csv(table, run.run_dir / FEATURES_FILE)

    events, metrics, baseline = analyze_behaviors(table, m.frame_fps, cfg)
    result = VisionAnalysis(run_id=m.run_id, baseline=baseline, events=events, metrics=metrics)
    (run.run_dir / OUTPUT_FILE).write_text(result.model_dump_json(indent=2), encoding="utf-8")

    if debug_video:
        from app.analysis.vision.debug import render_debug_video

        render_debug_video(run, table, events, baseline, cfg)
    return result
