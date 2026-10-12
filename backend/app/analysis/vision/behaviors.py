"""FeatureTable -> baseline, events and metrics.

Event types (source="video"):
    look_away    meta: direction left|right|up|down, reading_notes (bool), max_dev_deg
    face_lost    face not detected (out of frame / turned away / covered)
    slouch       neck ratio dropped vs. baseline
    lean         shoulders tilted vs. baseline
    sway         body rocking side to side
    face_touch   hand at the face
    fidget       sustained fast hand movement (gesturing and fidgeting are NOT
                 separated in this POC; treat as "restless hands")
"""
import numpy as np

from app.analysis.config import AnalysisConfig
from app.analysis.schemas import Event, VisionMetrics
from app.analysis.vision.landmarks import FeatureTable
from app.analysis.vision.signals import fill_gaps, hysteresis, mask_to_events, smooth

_BASE_KEYS = ["yaw", "pitch", "iris_h", "iris_v", "neck_ratio", "shoulder_tilt", "shoulder_w"]


def compute_baseline(tbl: FeatureTable, fps: float, cfg: AnalysisConfig) -> dict:
    """Reference pose = "looking at the camera, sitting straight".

    Median over the first calibration_s seconds if enough frames were detected,
    otherwise over the whole clip (assuming the speaker mostly faces the camera).
    """
    n = len(tbl["t"])
    window = np.arange(n) < int(cfg.calibration_s * fps)
    source = "calibration" if cfg.calibration_s > 0 else "clip_median"

    def med(key, mask):
        vals = tbl[key][mask]
        vals = vals[~np.isnan(vals)]
        return (float(np.median(vals)), len(vals))

    base: dict = {"source": source}
    for key in _BASE_KEYS:
        mask = window if cfg.calibration_s > 0 else np.ones(n, dtype=bool)
        value, count = med(key, mask)
        if cfg.calibration_s > 0 and count < max(5, int(0.3 * fps * cfg.calibration_s)):
            value, count = med(key, np.ones(n, dtype=bool))
            base["source"] = "clip_median"
        base[key] = value if count else None
    return base


def _pct(frames: int, total: int):
    return round(100.0 * frames / total, 1) if total else None


def _slice_events(segs, fps):
    return [(int(round(s * fps)), int(round(e * fps))) for s, e in segs]


def analyze_behaviors(
    tbl: FeatureTable, fps: float, cfg: AnalysisConfig
) -> tuple[list[Event], VisionMetrics, dict]:
    n = len(tbl["t"])
    gap = int(cfg.gap_fill_s * fps)
    win = int(cfg.smooth_s * fps)
    base = compute_baseline(tbl, fps, cfg)
    events: list[Event] = []

    def clean(key):
        return smooth(fill_gaps(tbl[key], gap), win)

    def add(type_, segs, **meta_fn):
        for (s, e), (i0, i1) in zip(segs, _slice_events(segs, fps)):
            meta = {k: (fn(i0, i1) if callable(fn) else fn) for k, fn in meta_fn.items()}
            events.append(Event(type=type_, source="video", start=round(s, 3),
                                end=round(e, 3), meta=meta))
        return segs

    face_ok = tbl["face"] == 1
    metrics = dict(frames=n, face_visible_pct=_pct(int(face_ok.sum()), n) or 0.0)

    # ---------------- face lost ----------------
    lost = mask_to_events(~face_ok, fps, cfg.face_lost_min_s)
    add("face_lost", lost)
    metrics["face_lost_s"] = round(sum(e - s for s, e in lost), 2)

    # ---------------- eye contact ----------------
    if base["yaw"] is not None:
        yaw, pitch = clean("yaw"), clean("pitch")
        ih, iv = clean("iris_h"), clean("iris_v")
        h_dev = (yaw - base["yaw"]) + cfg.gaze_gain_h * np.nan_to_num(ih - base["iris_h"])
        v_dev = (pitch - base["pitch"]) - cfg.gaze_gain_v * np.nan_to_num(iv - base["iris_v"])
        dev = np.where(np.isnan(yaw) | np.isnan(pitch), np.nan, np.hypot(h_dev, v_dev))
        away = hysteresis(dev, cfg.gaze_enter_deg, cfg.gaze_exit_deg)
        segs = mask_to_events(away, fps, cfg.look_away_min_s, cfg.merge_gap_s)

        def direction(i0, i1):
            h, v = np.nanmean(h_dev[i0:i1]), np.nanmean(v_dev[i0:i1])
            if abs(v) > abs(h):
                return "up" if v > 0 else "down"
            return "right" if h > 0 else "left"

        reading_s = 0.0
        for (s, e), (i0, i1) in zip(segs, _slice_events(segs, fps)):
            d = direction(i0, i1)
            reading = d == "down" and e - s >= cfg.reading_notes_min_s
            reading_s += (e - s) if reading else 0.0
            events.append(Event(
                type="look_away", source="video", start=round(s, 3), end=round(e, 3),
                meta={"direction": d, "reading_notes": reading,
                      "max_dev_deg": round(float(np.nanmax(dev[i0:i1])), 1)}))
        durations = [e - s for s, e in segs]
        away_frames = sum(i1 - i0 for i0, i1 in _slice_events(segs, fps))
        valid = int((~np.isnan(dev)).sum())
        metrics.update(
            eye_contact_pct=_pct(max(valid - away_frames, 0), valid),
            look_away_count=len(segs),
            look_away_total_s=round(sum(durations), 2),
            longest_look_away_s=round(max(durations, default=0.0), 2),
            reading_notes_s=round(reading_s, 2),
        )

        # head motion: mean angular speed of the head
        dyaw, dpitch = np.diff(yaw) * fps, np.diff(pitch) * fps
        speed = np.hypot(dyaw, dpitch)
        if np.isfinite(speed).any():
            metrics["head_motion_deg_s"] = round(float(np.nanmean(speed)), 1)

    # ---------------- posture ----------------
    pose_ok = tbl["pose"] == 1
    pose_frames = int(pose_ok.sum())
    if base["neck_ratio"]:
        rel = clean("neck_ratio") / base["neck_ratio"]
        slouch = hysteresis(rel, 1 - cfg.slouch_enter_drop, 1 - cfg.slouch_exit_drop, below=True)
        segs = mask_to_events(slouch, fps, cfg.slouch_min_s, cfg.merge_gap_s)
        add("slouch", segs,
            min_ratio=lambda i0, i1: round(float(np.nanmin(rel[i0:i1])), 2))
        metrics["slouch_count"] = len(segs)
        metrics["slouch_pct"] = _pct(sum(i1 - i0 for i0, i1 in _slice_events(segs, fps)), pose_frames)

    if base["shoulder_tilt"] is not None:
        tilt_dev = np.abs(clean("shoulder_tilt") - base["shoulder_tilt"])
        lean = hysteresis(tilt_dev, cfg.lean_enter_deg, cfg.lean_exit_deg)
        segs = mask_to_events(lean, fps, cfg.lean_min_s, cfg.merge_gap_s)
        add("lean", segs, max_tilt_deg=lambda i0, i1: round(float(np.nanmax(tilt_dev[i0:i1])), 1))
        metrics["lean_pct"] = _pct(sum(i1 - i0 for i0, i1 in _slice_events(segs, fps)), pose_frames)

    # ---------------- sway (rocking) ----------------
    if base["shoulder_w"]:
        x = fill_gaps(tbl["sh_mid_x"], gap) / base["shoulder_w"]
        w = max(3, int(cfg.sway_window_s * fps))
        sway_idx = np.full(n, np.nan)
        for i in range(n):
            seg = x[max(0, i - w // 2): i + w // 2 + 1]
            if np.sum(~np.isnan(seg)) >= w // 2:
                sway_idx[i] = np.nanstd(seg)
        sway = hysteresis(sway_idx, cfg.sway_enter, cfg.sway_exit)
        segs = mask_to_events(sway, fps, cfg.sway_min_s, cfg.merge_gap_s)
        add("sway", segs)
        metrics["sway_pct"] = _pct(sum(i1 - i0 for i0, i1 in _slice_events(segs, fps)), pose_frames)

    # ---------------- hands ----------------
    hands_ok = ~np.isnan(tbl["n_hands"])
    if hands_ok.any():
        metrics["hands_visible_pct"] = _pct(int((tbl["n_hands"] > 0).sum()), int(hands_ok.sum()))
        touch = tbl["hand_in_face"] == 1
        segs = mask_to_events(touch, fps, cfg.face_touch_min_s, cfg.merge_gap_s)
        add("face_touch", segs)
        metrics["face_touch_count"] = len(segs)

    if base["shoulder_w"]:
        speeds = []
        for side in ("l", "r"):
            px = smooth(fill_gaps(tbl[f"wrist_{side}x"], gap), 3)
            py = smooth(fill_gaps(tbl[f"wrist_{side}y"], gap), 3)
            sp = np.full(n, np.nan)
            sp[1:] = np.hypot(np.diff(px), np.diff(py)) / base["shoulder_w"] * fps
            speeds.append(sp)
        both = np.vstack(speeds)
        all_nan = np.all(np.isnan(both), axis=0)
        speed = np.full(n, np.nan)
        speed[~all_nan] = np.nanmax(both[:, ~all_nan], axis=0)
        speed = smooth(speed, max(3, int(cfg.fidget_window_s * fps)))
        fidget = hysteresis(speed, cfg.fidget_enter_speed, cfg.fidget_exit_speed)
        segs = mask_to_events(fidget, fps, cfg.fidget_min_s, cfg.merge_gap_s)
        add("fidget", segs,
            mean_speed=lambda i0, i1: round(float(np.nanmean(speed[i0:i1])), 2))
        valid = int((~np.isnan(speed)).sum())
        metrics["fidget_pct"] = _pct(sum(i1 - i0 for i0, i1 in _slice_events(segs, fps)), valid)

    events.sort(key=lambda e: (e.start, e.end))
    return events, VisionMetrics(**metrics), base
