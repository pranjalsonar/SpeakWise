"""Model registry: where each model comes from, its size, licence, and local path.

    python -m speakwise.models            # list status
    python -m speakwise.models download       # fetch the models the default config needs
    python -m speakwise.models download all   # also the NLI candidates used by compare_nli_models.py

Whisper weights are managed by faster-whisper (Hugging Face cache) and are not listed here.
"""
from __future__ import annotations

import shutil
import sys
import urllib.request
from pathlib import Path
from typing import Optional

from speakwise.config import PipelineConfig

_MP = "https://storage.googleapis.com/mediapipe-models"

REGISTRY = {
    "all-MiniLM-L6-v2": {
        "source": "huggingface", "repo": "Xenova/all-MiniLM-L6-v2", "license": "Apache-2.0", "size_mb": 23,
        "files": ["onnx/model_quantized.onnx", "tokenizer.json", "config.json"],
        "main": "onnx/model_quantized.onnx", "purpose": "sentence embeddings (context relevance, retrieval)"},
    # NLI candidates, compared in Colab with scripts/compare_nli_models.py (README "Results").
    # Default: nli-deberta-v3-base-q8 (best accuracy, no false inconsistency flags on the seed set).
    "nli-deberta-v3-base-q8": {
        "source": "huggingface", "repo": "cross-encoder/nli-deberta-v3-base", "license": "Apache-2.0", "size_mb": 253,
        "files": ["onnx/model_quint8_avx2.onnx", "tokenizer.json", "config.json"],
        "main": "onnx/model_quint8_avx2.onnx", "purpose": "NLI, base size, 8-bit (default)"},
    "nli-deberta-v3-small-q8": {
        "source": "huggingface", "repo": "cross-encoder/nli-deberta-v3-small", "license": "Apache-2.0", "size_mb": 182,
        "files": ["onnx/model_quint8_avx2.onnx", "tokenizer.json", "config.json"],
        "main": "onnx/model_quint8_avx2.onnx", "purpose": "NLI, small size, 8-bit (candidate)"},
    "nli-deberta-v3-xsmall-q8": {
        "source": "huggingface", "repo": "cross-encoder/nli-deberta-v3-xsmall", "license": "Apache-2.0", "size_mb": 96,
        "files": ["onnx/model_quint8_avx2.onnx", "tokenizer.json", "config.json"],
        "main": "onnx/model_quint8_avx2.onnx", "purpose": "NLI, 8-bit quantized (candidate)"},
    "nli-deberta-v3-xsmall": {
        "source": "huggingface", "repo": "cross-encoder/nli-deberta-v3-xsmall", "license": "Apache-2.0", "size_mb": 293,
        "files": ["onnx/model.onnx", "tokenizer.json", "config.json"],
        "main": "onnx/model.onnx", "purpose": "NLI, full precision (candidate)"},
    "deberta-v3-xsmall-binary-nli": {
        "source": "huggingface", "repo": "MoritzLaurer/DeBERTa-v3-xsmall-mnli-fever-anli-ling-binary",
        "license": "MIT", "size_mb": 293, "files": ["onnx/model.onnx", "tokenizer.json", "config.json"],
        "main": "onnx/model.onnx", "purpose": "NLI entailment vs not, more training data (candidate; no contradiction class)"},
    "face_landmarker": {
        "source": "url", "license": "Apache-2.0", "size_mb": 3.8,
        "url": f"{_MP}/face_landmarker/face_landmarker/float16/1/face_landmarker.task",
        "main": "face_landmarker.task", "purpose": "face, head pose and iris landmarks"},
    "pose_landmarker_lite": {
        "source": "url", "license": "Apache-2.0", "size_mb": 5.8,
        "url": f"{_MP}/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task",
        "main": "pose_landmarker_lite.task", "purpose": "shoulder landmarks (posture, movement)"},
}


def model_dir(name: str, cfg: Optional[PipelineConfig] = None) -> Path:
    return (cfg or PipelineConfig()).models_dir / name


def model_path(name: str, cfg: Optional[PipelineConfig] = None) -> Path:
    return model_dir(name, cfg) / REGISTRY[name]["main"]


def is_available(name: str, cfg: Optional[PipelineConfig] = None) -> bool:
    return model_path(name, cfg).is_file()


class ModelUnavailable(Exception):
    pass


def ensure(name: str, cfg: Optional[PipelineConfig] = None) -> Path:
    """Return the model's main file, downloading it first if missing and downloads are allowed."""
    if name not in REGISTRY:
        raise ModelUnavailable(f"Unknown model '{name}'. Known: {sorted(REGISTRY)}")
    spec = REGISTRY[name]
    path = model_path(name, cfg)
    if path.is_file():
        return path
    if cfg is not None and not cfg.allow_downloads:
        raise ModelUnavailable(f"Model '{name}' is not downloaded and downloads are disabled "
                               f"(run: python -m speakwise.models download).")
    d = model_dir(name, cfg)
    d.mkdir(parents=True, exist_ok=True)
    print(f"downloading {name} (~{spec['size_mb']} MB, {spec['license']}) ...", flush=True)
    if spec["source"] == "huggingface":
        from huggingface_hub import hf_hub_download

        for f in spec["files"]:
            hf_hub_download(spec["repo"], f, local_dir=str(d))
    else:
        tmp = path.with_suffix(".part")
        urllib.request.urlretrieve(spec["url"], tmp)
        shutil.move(str(tmp), str(path))
    return path


def status(cfg: Optional[PipelineConfig] = None) -> dict[str, dict]:
    return {n: {"available": is_available(n, cfg), "license": s["license"], "size_mb": s["size_mb"],
                "purpose": s["purpose"]} for n, s in REGISTRY.items()}


def defaults(cfg: Optional[PipelineConfig] = None) -> list[str]:
    """Models the default configuration needs."""
    cfg = cfg or PipelineConfig()
    return [cfg.embed_model, cfg.nli_model, "face_landmarker", "pose_landmarker_lite"]


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "download":
        for n in (list(REGISTRY) if sys.argv[2:3] == ["all"] else defaults()):
            ensure(n)
    for n, s in status().items():
        print(f"{'OK ' if s['available'] else '-- '} {n:24s} {s['size_mb']:>5} MB  {s['license']:10s} {s['purpose']}")
