"""Voice activity detection using the Silero VAD bundled with faster-whisper
(ONNX, CPU, no torch needed)."""
import wave
from pathlib import Path

import numpy as np
from faster_whisper.vad import VadOptions, get_speech_timestamps

from app.analysis.config import AnalysisConfig


def load_wav(path: str | Path) -> tuple[np.ndarray, int]:
    """Read a 16-bit mono PCM WAV (as written by phase 1) as float32 in [-1, 1]."""
    with wave.open(str(path), "rb") as w:
        if w.getsampwidth() != 2 or w.getnchannels() != 1:
            raise ValueError("Expected 16-bit mono WAV (run phase 1 first).")
        rate = w.getframerate()
        raw = w.readframes(w.getnframes())
    return np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0, rate


def speech_segments(
    audio: np.ndarray, rate: int, cfg: AnalysisConfig
) -> list[tuple[float, float]]:
    """Speech intervals in seconds.

    Tuned for *pause measurement*: tiny padding and a short min-silence, so the
    gap between consecutive segments is (almost) the real silence. The ASR runs
    its own, more generous VAD (see asr.py).
    """
    opts = VadOptions(
        threshold=cfg.pause_vad_threshold,
        min_silence_duration_ms=int(cfg.pause_min_s * 1000),
        min_speech_duration_ms=100,
        speech_pad_ms=30,
    )
    chunks = get_speech_timestamps(audio, opts, sampling_rate=rate)
    return [(c["start"] / rate, c["end"] / rate) for c in chunks]
