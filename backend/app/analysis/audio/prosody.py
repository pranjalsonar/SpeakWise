"""Prosody: pitch variation and loudness variation (Praat via Parselmouth)."""
from typing import Optional

import numpy as np
import parselmouth


def analyze_prosody(
    audio: np.ndarray, rate: int, segments: list[tuple[float, float]]
) -> dict[str, Optional[float]]:
    """Pitch/intensity statistics over speech segments only.

    pitch_std_semitones is speaker-independent (std of 12*log2(f0/median)); a low
    value (< ~2) suggests a monotone delivery.
    """
    out: dict[str, Optional[float]] = {
        "pitch_mean_hz": None, "pitch_std_semitones": None, "intensity_std_db": None,
    }
    if not segments or len(audio) < rate:  # need ~1 s of audio
        return out

    sound = parselmouth.Sound(audio.astype(np.float64), sampling_frequency=rate)

    def in_speech(times: np.ndarray) -> np.ndarray:
        mask = np.zeros(times.shape, dtype=bool)
        for s, e in segments:
            mask |= (times >= s) & (times <= e)
        return mask

    pitch = sound.to_pitch(time_step=0.01, pitch_floor=75, pitch_ceiling=500)
    f0 = pitch.selected_array["frequency"]
    voiced = (f0 > 0) & in_speech(pitch.xs())
    if voiced.sum() >= 20:
        f = f0[voiced]
        out["pitch_mean_hz"] = round(float(f.mean()), 1)
        out["pitch_std_semitones"] = round(float(np.std(12 * np.log2(f / np.median(f)))), 2)

    intensity = sound.to_intensity(minimum_pitch=75, time_step=0.01)
    db = intensity.values[0]
    loud = in_speech(intensity.xs()) & np.isfinite(db)
    if loud.sum() >= 20:
        out["intensity_std_db"] = round(float(np.std(db[loud])), 2)
    return out
