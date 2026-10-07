"""MediaPipe model files (MediaPipe >= 1.0 no longer bundles them).

    python -m app.analysis.vision.models      # download any that are missing
"""
import urllib.request
from pathlib import Path

MODELS_DIR = Path(__file__).resolve().parents[1] / "models"
_BASE = "https://storage.googleapis.com/mediapipe-models"

MODELS = {
    "face": ("face_landmarker.task",
             f"{_BASE}/face_landmarker/face_landmarker/float16/1/face_landmarker.task"),
    "pose": ("pose_landmarker_full.task",
             f"{_BASE}/pose_landmarker/pose_landmarker_full/float16/1/pose_landmarker_full.task"),
    "hand": ("hand_landmarker.task",
             f"{_BASE}/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"),
}


def model_path(kind: str) -> Path:
    """Path to a model file, downloading it on first use."""
    name, url = MODELS[kind]
    path = MODELS_DIR / name
    if not path.is_file():
        MODELS_DIR.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".part")
        print(f"downloading {name} ...")
        urllib.request.urlretrieve(url, tmp)
        tmp.replace(path)
    return path


if __name__ == "__main__":
    for kind in MODELS:
        print(model_path(kind))
