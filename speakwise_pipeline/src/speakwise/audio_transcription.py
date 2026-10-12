"""Speech-to-text with word timestamps and confidence (faster-whisper / CTranslate2).

Model, device and precision are chosen from the detected hardware (environment.choose_asr).
The transcript is treated as an estimate: every word keeps its probability, and every
segment keeps Whisper's avg_logprob / no_speech_prob / compression_ratio.

Known limitations (documented in the report):
  * Whisper is trained to produce clean text and often drops "um"/"uh".
  * Accuracy on Indian English must be measured on real recordings; it is not assumed.
"""
from __future__ import annotations

import gc
import time
from typing import Any, Optional, Protocol

import numpy as np

from speakwise.config import PipelineConfig
from speakwise.environment import ASR_CPU_RAM_GB, choose_asr, preload_cuda12_libs
from speakwise.schemas import Metric, Status, Transcription, TranscriptSegment, WordToken

_MODEL_CACHE: dict[tuple, Any] = {}


class TranscriberFn(Protocol):
    def __call__(self, audio: np.ndarray, rate: int, cfg: PipelineConfig, env: dict) -> Transcription: ...


class ASRError(Exception):
    pass


def load_model(name: str, device: str, compute_type: str, cpu_threads: int = 0):
    key = (name, device, compute_type, cpu_threads)
    if key not in _MODEL_CACHE:
        from faster_whisper import WhisperModel

        try:
            _MODEL_CACHE[key] = WhisperModel(name, device=device, compute_type=compute_type,
                                             cpu_threads=cpu_threads)
        except (RuntimeError, MemoryError, ValueError, OSError) as exc:
            msg = str(exc)
            if "alloc" in msg.lower() or isinstance(exc, MemoryError):
                raise ASRError(f"Not enough memory to load Whisper '{name}' on {device}. "
                               "Choose a smaller model or free memory.") from exc
            raise ASRError(f"Could not load Whisper '{name}' on {device}: {msg[:200]}") from exc
    return _MODEL_CACHE[key]


def release_models() -> None:
    _MODEL_CACHE.clear()
    gc.collect()


def transcribe(audio: np.ndarray, rate: int, cfg: PipelineConfig, env: dict) -> Transcription:
    """Raises ASRError if the model can't be loaded or decoding fails."""
    if rate != 16000:
        raise ASRError(f"Whisper needs 16 kHz audio, got {rate} Hz.")
    choice = choose_asr(cfg.asr_model, cfg.asr_device, cfg.asr_compute_type, env)
    try:
        return _transcribe_with(audio, rate, cfg, choice, [])
    except ASRError as exc:
        if choice["device"] != "cuda" or cfg.asr_device == "cuda":
            raise
        # GPU path failed (e.g. missing CUDA libraries): retry on CPU and say so in the report
        cpu = choose_asr(cfg.asr_model, "cpu", "auto", env)
        if cfg.asr_model == "auto" and cpu["model"] == "small" and env.get("ram_available_gb", 0) < ASR_CPU_RAM_GB["small"]:
            cpu["model"] = "base"
        note = f"GPU speech recognition failed ({str(exc)[:120]}); fell back to CPU '{cpu['model']}'."
        return _transcribe_with(audio, rate, cfg, cpu, [note])


def _transcribe_with(audio: np.ndarray, rate: int, cfg: PipelineConfig, choice: dict, notes: list[str]) -> Transcription:
    if choice["device"] == "cuda":
        choice["cuda12_libs_preloaded"] = preload_cuda12_libs()
    t0 = time.perf_counter()
    model = load_model(choice["model"], choice["device"], choice["compute_type"], cfg.asr_cpu_threads)
    load_s = time.perf_counter() - t0

    t1 = time.perf_counter()
    try:
        seg_iter, info = model.transcribe(
            audio, language=cfg.language, word_timestamps=True, vad_filter=True,
            beam_size=cfg.asr_beam_size, condition_on_previous_text=False,
            initial_prompt=cfg.asr_initial_prompt or None)
        words: list[WordToken] = []
        segments: list[TranscriptSegment] = []
        for s in seg_iter:  # decoding happens while iterating
            segments.append(TranscriptSegment(
                start=round(s.start, 3), end=round(s.end, 3), text=s.text.strip(),
                avg_logprob=round(s.avg_logprob, 3), no_speech_prob=round(s.no_speech_prob, 3),
                compression_ratio=round(s.compression_ratio, 3)))
            for w in s.words or []:
                if w.word.strip():
                    words.append(WordToken(text=w.word.strip(), start=round(w.start, 3), end=round(w.end, 3),
                                           probability=round(w.probability, 3)))
    except (RuntimeError, MemoryError) as exc:
        _MODEL_CACHE.clear()
        raise ASRError(f"Speech recognition failed: {str(exc)[:200]}") from exc
    decode_s = time.perf_counter() - t1

    t = build_transcription(words, segments, cfg, model_info={
        **choice, "beam_size": cfg.asr_beam_size, "vad_filter": True, "word_timestamps": True,
        "initial_prompt": "verbatim-style prompt to keep fillers" if cfg.asr_initial_prompt else None,
        "load_time_s": round(load_s, 2), "decode_time_s": round(decode_s, 2),
        "realtime_factor": round(decode_s / max(len(audio) / rate, 1e-6), 3)},
        language=info.language, language_probability=round(info.language_probability, 3))
    if notes:
        t.warnings = notes + t.warnings
        t.status = Status.warning
    return t


def build_transcription(words: list[WordToken], segments: list[TranscriptSegment], cfg: PipelineConfig,
                        model_info: Optional[dict] = None, language: Optional[str] = None,
                        language_probability: Optional[float] = None) -> Transcription:
    """Assemble the Transcription section from words (also used for test doubles)."""
    warnings, limitations = [], [
        "Whisper tends to omit hesitation sounds such as 'um' and 'uh'; filler counts can be too low.",
        "Recognition accuracy for Indian English has not been measured on SpeakWise recordings yet.",
    ]
    t = Transcription(status=Status.ok, model=model_info or {}, language=language,
                      language_probability=language_probability, words=words, segments=segments,
                      text=" ".join(w.text for w in words), limitations=limitations)
    if not words:
        t.status = Status.unavailable
        t.warnings = ["No speech was recognised."]
        t.word_count = Metric.measured(0, "count", note="no words recognised")
        return t
    probs = np.array([w.probability for w in words if w.probability is not None])
    low = float((probs < cfg.low_confidence_word_prob).mean() * 100) if probs.size else None
    t.word_count = Metric.measured(len(words), "count", note="all recognised tokens, fillers included")
    if probs.size:
        t.mean_word_probability = Metric.measured(float(probs.mean()), "ratio",
                                                  note="Whisper word probability; not a calibrated accuracy")
        t.low_confidence_word_pct = Metric.measured(low, "percent", denominator=f"{probs.size} recognised words",
                                                    note=f"probability < {cfg.low_confidence_word_prob}")
        if probs.mean() < cfg.ctx_low_asr_conf or low > 25:
            warnings.append("Many words were recognised with low confidence; transcript-based results "
                            "(fillers, repetitions, context) are less reliable.")
    if language and cfg.language is None and language != "en":
        warnings.append(f"Detected language '{language}'; only English is supported in this version.")
    t.warnings = warnings
    t.status = Status.warning if warnings else Status.ok
    return t
