"""Optional learned confidence model.

The rule-based score (scoring.py) is the default. Once you have sessions rated
by humans, train a model on the report feature vectors and drop it in
models/confidence_model.joblib; the report then also carries `ml_overall`.

    labels.csv:   run_id,score        (score = human confidence rating, 0-100;
                                       one row per run that has session_report.json)
    python -m app.analysis.fusion.ml train labels.csv

Needs scikit-learn + joblib (pip install scikit-learn joblib). Not imported
unless a model file exists or you train.
"""
import csv
import sys
from pathlib import Path
from typing import Optional

from app.analysis.config import DEFAULT_CONFIG
from app.analysis.schemas import AudioMetrics, SessionReport, VisionMetrics

MODEL_PATH = Path(__file__).resolve().parents[1] / "models" / "confidence_model.joblib"

FEATURE_NAMES = [
    "filler_rate", "repetition_rate", "pause_rate", "long_pause_rate", "hesitation_pause_rate",
    "silence_ratio", "wpm", "pitch_std_semitones", "intensity_std_db",
    "eye_contact_pct", "look_away_rate", "reading_notes_frac", "face_visible_pct",
    "slouch_pct", "lean_pct", "sway_pct", "fidget_pct", "face_touch_rate", "head_motion_deg_s",
]


def feature_vector(
    audio: Optional[AudioMetrics], vision: Optional[VisionMetrics],
    rates: dict[str, float], duration_s: float,
) -> dict[str, Optional[float]]:
    """Flat, fixed-order features (None = not measured)."""
    f: dict[str, Optional[float]] = {k: None for k in FEATURE_NAMES}
    per_min = 60 / max(duration_s, DEFAULT_CONFIG.min_rate_span_s)
    if audio:
        f.update(rates)
        f.update(silence_ratio=audio.silence_ratio, wpm=audio.wpm,
                 pitch_std_semitones=audio.pitch_std_semitones,
                 intensity_std_db=audio.intensity_std_db)
    if vision:
        f.update(
            eye_contact_pct=vision.eye_contact_pct, face_visible_pct=vision.face_visible_pct,
            look_away_rate=vision.look_away_count * per_min,
            reading_notes_frac=vision.reading_notes_s / max(duration_s, 1.0),
            slouch_pct=vision.slouch_pct, lean_pct=vision.lean_pct, sway_pct=vision.sway_pct,
            fidget_pct=vision.fidget_pct, face_touch_rate=vision.face_touch_count * per_min,
            head_motion_deg_s=vision.head_motion_deg_s,
        )
    return f


def predict(
    features: dict[str, Optional[float]], path: Path = MODEL_PATH
) -> tuple[Optional[float], Optional[str]]:
    """(score, model name) or (None, None) if no trained model is available."""
    if not path.is_file():
        return None, None
    import joblib  # lazy: only needed when a model exists

    bundle = joblib.load(path)
    names = bundle["features"]
    row = [[float("nan") if features.get(n) is None else features[n] for n in names]]
    score = float(bundle["pipeline"].predict(row)[0])
    return round(min(100.0, max(0.0, score)), 1), bundle.get("name", "confidence_model")


def train(
    labels_csv: str, runs_dir: Path = DEFAULT_CONFIG.runs_dir, out: Path = MODEL_PATH
) -> dict:
    import joblib
    import numpy as np
    from sklearn.ensemble import GradientBoostingRegressor
    from sklearn.impute import SimpleImputer
    from sklearn.linear_model import Ridge
    from sklearn.model_selection import LeaveOneOut, cross_val_predict
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    X, y = [], []
    with open(labels_csv, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            report = SessionReport.model_validate_json(
                (runs_dir / row["run_id"] / "session_report.json").read_text(encoding="utf-8"))
            X.append([np.nan if report.features.get(n) is None else report.features[n]
                      for n in FEATURE_NAMES])
            y.append(float(row["score"]))
    X, y = np.array(X), np.array(y)
    if len(y) < 10:
        print(f"warning: only {len(y)} labelled sessions; results will be unreliable")

    candidates = {
        "ridge": make_pipeline(SimpleImputer(strategy="median"), StandardScaler(),
                               Ridge(alpha=5.0)),
        "gbr": make_pipeline(SimpleImputer(strategy="median"),
                             GradientBoostingRegressor(n_estimators=150, max_depth=2,
                                                       learning_rate=0.05, random_state=0)),
    }
    maes = {}
    for name, pipe in candidates.items():
        pred = cross_val_predict(pipe, X, y, cv=LeaveOneOut())
        maes[name] = float(np.mean(np.abs(pred - y)))
        print(f"{name:6s} leave-one-out MAE = {maes[name]:.1f} points")
    best = min(maes, key=maes.get)
    baseline = float(np.mean(np.abs(y - np.median(y))))
    print(f"baseline (always predict the median) MAE = {baseline:.1f}")

    pipe = candidates[best].fit(X, y)
    out.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"pipeline": pipe, "features": FEATURE_NAMES, "name": f"{best}-n{len(y)}",
                 "cv_mae": maes[best]}, out)
    print(f"saved {best} model to {out}")
    return {"best": best, "maes": maes, "baseline_mae": baseline}


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "train":
        train(sys.argv[2])
    else:
        print(__doc__)
