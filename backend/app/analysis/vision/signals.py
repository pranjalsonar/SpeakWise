"""Signal helpers: per-frame values -> clean, countable events.

Raw per-frame detections jitter (one blink would become a "look away"), so every
behaviour goes through the same chain:
    fill_gaps -> smooth -> hysteresis -> mask_to_events(min duration, merge gap)
"""
import numpy as np


def fill_gaps(x: np.ndarray, max_gap: int) -> np.ndarray:
    """Linearly interpolate NaN runs of at most `max_gap` frames; longer runs stay NaN."""
    x = x.astype(float).copy()
    nan = np.isnan(x)
    if not nan.any() or nan.all():
        return x
    idx = np.arange(len(x))
    interp = np.interp(idx, idx[~nan], x[~nan])
    i = 0
    while i < len(x):
        if nan[i]:
            j = i
            while j < len(x) and nan[j]:
                j += 1
            interior = i > 0 and j < len(x)  # never extrapolate past the ends
            if interior and (j - i) <= max_gap:
                x[i:j] = interp[i:j]
            i = j
        else:
            i += 1
    return x


def smooth(x: np.ndarray, window: int) -> np.ndarray:
    """Moving median ignoring NaN (window is forced odd)."""
    window = max(1, window | 1)
    if window == 1:
        return x.astype(float).copy()
    half = window // 2
    out = np.full(len(x), np.nan)
    for i in range(len(x)):
        seg = x[max(0, i - half): i + half + 1]
        if not np.all(np.isnan(seg)):
            out[i] = np.nanmedian(seg)
    return out


def hysteresis(x: np.ndarray, enter: float, exit_: float, below: bool = False) -> np.ndarray:
    """Boolean state that turns on past `enter` and only off again past `exit_`.

    below=False: on when x > enter, off when x < exit_  (enter > exit_)
    below=True : on when x < enter, off when x > exit_  (enter < exit_)
    NaN switches the state off.
    """
    state = False
    out = np.zeros(len(x), dtype=bool)
    for i, v in enumerate(x):
        if np.isnan(v):
            state = False
        elif not state:
            state = (v < enter) if below else (v > enter)
        else:
            state = not ((v > exit_) if below else (v < exit_))
        out[i] = state
    return out


def mask_to_events(
    mask: np.ndarray, fps: float, min_dur: float, merge_gap: float = 0.0
) -> list[tuple[float, float]]:
    """True-runs -> (start_s, end_s). Runs closer than merge_gap are merged first,
    then runs shorter than min_dur are dropped. Frame i spans [i/fps, (i+1)/fps)."""
    runs: list[list[int]] = []
    i, n = 0, len(mask)
    while i < n:
        if mask[i]:
            j = i
            while j < n and mask[j]:
                j += 1
            runs.append([i, j])
            i = j
        else:
            i += 1

    merged: list[list[int]] = []
    for r in runs:
        if merged and (r[0] - merged[-1][1]) / fps < merge_gap:
            merged[-1][1] = r[1]
        else:
            merged.append(r)
    return [(a / fps, b / fps) for a, b in merged if (b - a) / fps >= min_dur]
