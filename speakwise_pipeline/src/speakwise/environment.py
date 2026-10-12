"""Inspect the runtime (Colab or local) and choose model settings from what is actually there."""
from __future__ import annotations

import importlib
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Optional

LIBRARIES = ["numpy", "pydantic", "faster_whisper", "ctranslate2", "mediapipe", "onnxruntime",
             "tokenizers", "huggingface_hub", "cv2", "torch", "psutil"]


def _version(name: str) -> Optional[str]:
    try:
        mod = importlib.import_module(name)
        return getattr(mod, "__version__", "installed")
    except Exception:  # noqa: BLE001 - absence is the information we want
        return None


def gpu_info() -> list[dict[str, Any]]:
    """GPUs reported by nvidia-smi (empty list when there is none)."""
    if not shutil.which("nvidia-smi"):
        return []
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,memory.used,memory.free",
             "--format=csv,noheader,nounits"], capture_output=True, text=True, timeout=10).stdout
    except (OSError, subprocess.SubprocessError):
        return []
    gpus = []
    for line in out.strip().splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) == 4:
            gpus.append({"name": parts[0], "memory_total_mb": float(parts[1]),
                         "memory_used_mb": float(parts[2]), "memory_free_mb": float(parts[3])})
    return gpus


def cuda_available_for_asr() -> bool:
    try:
        import ctranslate2

        return ctranslate2.get_cuda_device_count() > 0
    except Exception:  # noqa: BLE001
        return False


def ffmpeg_version() -> Optional[str]:
    exe = shutil.which("ffmpeg")
    if not exe:
        return None
    try:
        first = subprocess.run([exe, "-version"], capture_output=True, text=True, timeout=10).stdout.splitlines()[0]
        return first.replace("ffmpeg version ", "").split(" ")[0]
    except (OSError, subprocess.SubprocessError, IndexError):
        return "unknown"


def inspect_environment(work_dir: Optional[str] = None) -> dict[str, Any]:
    import psutil

    vm = psutil.virtual_memory()
    disk_path = Path(work_dir or os.getcwd()).resolve()
    while not disk_path.exists() and disk_path != disk_path.parent:  # work dir may not exist yet
        disk_path = disk_path.parent
    du = shutil.disk_usage(disk_path)
    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "in_colab": "google.colab" in sys.modules or os.path.exists("/content"),
        "cpu_count": os.cpu_count(),
        "ram_total_gb": round(vm.total / 2**30, 2),
        "ram_available_gb": round(vm.available / 2**30, 2),
        "disk_free_gb": round(du.free / 2**30, 1),
        "gpus": gpu_info(),
        "cuda_for_asr": cuda_available_for_asr(),
        "ffmpeg": ffmpeg_version(),
        "ffprobe": bool(shutil.which("ffprobe")),
        "libraries": {name: _version(name) for name in LIBRARIES},
    }


# Free RAM (GB) a CPU/int8 Whisper model needs, measured on an 8 GB laptop (see README).
ASR_CPU_RAM_GB = {"tiny": 0.6, "base": 1.0, "small": 2.0, "medium": 4.5, "large-v3-turbo": 5.0}


def choose_asr(model: str, device: str, compute_type: str, env: dict[str, Any]) -> dict[str, str]:
    """Resolve 'auto' settings into a concrete (model, device, compute_type) with the reason."""
    use_cuda = env.get("cuda_for_asr", False) if device == "auto" else device == "cuda"
    dev = "cuda" if use_cuda else "cpu"
    ctype = compute_type if compute_type != "auto" else ("float16" if dev == "cuda" else "int8")
    if model != "auto":
        return {"model": model, "device": dev, "compute_type": ctype, "reason": "set in config"}
    if dev == "cuda":
        return {"model": "small", "device": dev, "compute_type": ctype,
                "reason": "GPU detected: 'small' is the measured baseline; try 'large-v3-turbo' explicitly"}
    ram = env.get("ram_available_gb", 0)
    for name in ("small", "base", "tiny"):
        if ram >= ASR_CPU_RAM_GB[name]:
            return {"model": name, "device": dev, "compute_type": ctype,
                    "reason": f"CPU only, {ram} GB RAM available: largest of small/base/tiny that fits"}
    return {"model": "tiny", "device": dev, "compute_type": ctype,
            "reason": f"CPU only and only {ram} GB RAM available: 'tiny' may still fail to load"}


def preload_cuda12_libs() -> int:
    """Load pip-installed CUDA 12 cuBLAS/cuDNN (packages nvidia-cublas-cu12, nvidia-cudnn-cu12)
    into this process so CTranslate2 finds them. Needed when the system CUDA is newer (e.g.
    Colab with CUDA 13). Returns the number of libraries loaded (0 if the packages are absent)."""
    import ctypes
    import glob

    loaded = 0
    for pkg in ("nvidia.cublas", "nvidia.cudnn"):
        try:
            mod = importlib.import_module(pkg)
        except ImportError:
            continue
        for d in getattr(mod, "__path__", []):
            for so in sorted(glob.glob(os.path.join(d, "lib", "lib*.so*"))):
                try:
                    ctypes.CDLL(so, mode=ctypes.RTLD_GLOBAL)
                    loaded += 1
                except OSError:
                    pass
    return loaded
