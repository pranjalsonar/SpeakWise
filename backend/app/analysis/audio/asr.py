"""Speech recognition with word-level timestamps (faster-whisper)."""
from functools import lru_cache

import numpy as np

from app.analysis.config import AnalysisConfig
from app.analysis.schemas import Word


@lru_cache(maxsize=2)
def _load_model(size: str, device: str, compute_type: str):
    from faster_whisper import WhisperModel  # heavy import, keep lazy

    return WhisperModel(size, device=device, compute_type=compute_type)


# Largest-first, with the free RAM (GB) each model needs on CPU/int8 (measured on
# an 8 GB dev laptop; faster-whisper's native memory is not released after an
# allocation failure, so we choose up front instead of retrying).
_NEEDS_GB = {"medium": 3.5, "small": 1.6, "base": 1.0, "tiny": 0.5}


def release_models() -> None:
    """Drop the cached Whisper model so its memory can be reused (e.g. by the vision phase)."""
    import gc

    _load_model.cache_clear()
    gc.collect()


def pick_model(requested: str) -> str:
    """The requested model, or the largest smaller one that fits in free RAM."""
    import psutil

    if requested not in _NEEDS_GB:
        return requested  # custom/unknown name: trust the caller
    free_gb = psutil.virtual_memory().available / 1024**3
    sizes = list(_NEEDS_GB)
    for name in sizes[sizes.index(requested):]:
        if _NEEDS_GB[name] <= free_gb:
            if name != requested:
                print(f"warning: {free_gb:.1f} GB RAM free; using whisper '{name}' "
                      f"instead of '{requested}'")
            return name
    return sizes[-1]  # nothing fits: try the smallest and let it fail loudly


def transcribe(audio: np.ndarray, cfg: AnalysisConfig) -> tuple[list[Word], str | None, str]:
    """Return (words, detected_language, model_used).

    vad_filter=True stops Whisper hallucinating text over silence; timestamps
    are mapped back to the original timeline by faster-whisper.
    condition_on_previous_text=False avoids repetition loops on long audio.
    """
    name = pick_model(cfg.whisper_model)
    model = _load_model(name, cfg.whisper_device, cfg.whisper_compute_type)
    segments, info = model.transcribe(
        audio,
        language=cfg.language,
        word_timestamps=True,
        vad_filter=True,
        beam_size=5,
        condition_on_previous_text=False,
        initial_prompt=cfg.asr_initial_prompt or None,
    )
    words: list[Word] = []
    for seg in segments:  # generator: decoding happens here
        for w in seg.words or []:
            text = w.word.strip()
            if text:
                words.append(
                    Word(text=text, start=round(w.start, 3), end=round(w.end, 3),
                         probability=round(w.probability, 3))
                )
    return words, info.language, name
