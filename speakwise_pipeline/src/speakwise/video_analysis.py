"""Video analysis: face visibility, head orientation, estimated camera-directed gaze, and
(only when the shoulders are visible) posture and movement measurements.

Adapted from backend/app/analysis/vision/{landmarks,signals,behaviors}.py: head pose from
MediaPipe's facial transformation matrix, iris-position ratios, and the gap-fill / median
smoothing / hysteresis / minimum-duration chain that turns per-frame values into events.

What this module does NOT do: infer confidence, nervousness or emotion. Frames without a
usable face are excluded from gaze/orientation denominators, never counted as "looking away".
"""
from __future__ import annotations

import time
from typing import Any, Callable, Optional

import numpy as np

from speakwise.config import PipelineConfig
from speakwise.media_preprocessing import PreprocessResult, iter_video_frames
from speakwise.schemas import Metric, Status, TimedEvent, VideoAnalysis

COLUMNS = ["t", "face", "face_w", "yaw", "pitch", "roll", "iris_h", "iris_v", "brightness",
           "shoulders", "neck_ratio", "shoulder_tilt", "shoulder_w", "sh_mid_x"]
FeatureTable = dict[str, np.ndarray]


# ------------------------------------------------------------ signal helpers
def fill_gaps(x: np.ndarray, max_gap: int) -> np.ndarray:
    """Interpolate interior NaN runs of at most max_gap samples."""
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
            if i > 0 and j < len(x) and j - i <= max_gap:
                x[i:j] = interp[i:j]
            i = j
        else:
            i += 1
    return x


def smooth(x: np.ndarray, window: int) -> np.ndarray:
    window = max(1, window | 1)
    if window == 1:
        return x.astype(float).copy()
    h = window // 2
    out = np.full(len(x), np.nan)
    for i in range(len(x)):
        seg = x[max(0, i - h): i + h + 1]
        if not np.all(np.isnan(seg)):
            out[i] = np.nanmedian(seg)
    return out


def hysteresis(x: np.ndarray, enter: float, exit_: float) -> np.ndarray:
    """On when x > enter, off again only when x < exit_. NaN = off."""
    state, out = False, np.zeros(len(x), dtype=bool)
    for i, v in enumerate(x):
        if np.isnan(v):
            state = False
        elif not state:
            state = v > enter
        else:
            state = v >= exit_
        out[i] = state
    return out


def runs(mask: np.ndarray, times: np.ndarray, step: float, min_dur: float) -> list[tuple[float, float, int, int]]:
    """True-runs as (start_s, end_s, i0, i1) lasting at least min_dur."""
    out, i, n = [], 0, len(mask)
    while i < n:
        if mask[i]:
            j = i
            while j < n and mask[j]:
                j += 1
            s, e = times[i], times[j - 1] + step
            if e - s >= min_dur:
                out.append((round(float(s), 3), round(float(e), 3), i, j))
            i = j
        else:
            i += 1
    return out


# -------------------------------------------------------- frame feature extraction
def _head_pose(matrix) -> tuple[float, float, float]:
    """Yaw/pitch/roll (deg) from MediaPipe's facial transformation matrix (OpenGL frame:
    x right, y up, z toward the camera). Facing the camera = (0, 0)."""
    R = np.array(matrix, dtype=np.float64)[:3, :3]
    R = R / np.linalg.norm(R, axis=0)
    f = R[:, 2]
    yaw = np.degrees(np.arctan2(f[0], f[2]))
    pitch = np.degrees(np.arctan2(f[1], np.hypot(f[0], f[2])))
    roll = -np.degrees(np.arctan2(R[1, 0], R[0, 0]))
    return float(yaw), float(pitch), float(roll)


class MediaPipeAnalyzer:
    """Per-frame features with MediaPipe Face Landmarker (+ Pose Landmarker lite)."""

    def __init__(self, cfg: PipelineConfig):
        import mediapipe as mp
        from mediapipe.tasks.python import BaseOptions, vision

        from speakwise import models

        self._mp = mp
        mode = vision.RunningMode.VIDEO
        self.face = vision.FaceLandmarker.create_from_options(vision.FaceLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=str(models.ensure("face_landmarker", cfg))),
            running_mode=mode, num_faces=1, output_facial_transformation_matrixes=True))
        self.pose = None
        if cfg.pose_enabled:
            self.pose = vision.PoseLandmarker.create_from_options(vision.PoseLandmarkerOptions(
                base_options=BaseOptions(model_asset_path=str(models.ensure("pose_landmarker_lite", cfg))),
                running_mode=mode, num_poses=1))
        self.vis_min = cfg.shoulder_visibility_min
        self.info = {"face": "MediaPipe Face Landmarker (float16)",
                     "pose": "MediaPipe Pose Landmarker lite" if self.pose else None}

    def __call__(self, rgb: np.ndarray, t: float) -> dict[str, float]:
        h, w = rgb.shape[:2]
        row = {c: np.nan for c in COLUMNS}
        row.update(t=t, face=0.0, shoulders=0.0, brightness=float(rgb.mean()))
        img = self._mp.Image(image_format=self._mp.ImageFormat.SRGB, data=np.ascontiguousarray(rgb))
        ts = int(round(t * 1000))
        f = self.face.detect_for_video(img, ts)
        if f.face_landmarks:
            pts = np.array([[p.x * w, p.y * h] for p in f.face_landmarks[0]])
            row["face"] = 1.0
            row["face_w"] = float((pts[:, 0].max() - pts[:, 0].min()) / w)
            if f.facial_transformation_matrixes:
                row["yaw"], row["pitch"], row["roll"] = _head_pose(f.facial_transformation_matrixes[0])
            if len(pts) >= 478:
                def ratio(i, a, b):
                    d = pts[b] - pts[a]
                    den = float(d @ d)
                    return float((pts[i] - pts[a]) @ d / den) if den > 1e-6 else np.nan
                row["iris_h"] = float(np.nanmean([ratio(468, 33, 133), ratio(473, 362, 263)]))
                vs = [(pts[i][1] - pts[u][1]) / (pts[l][1] - pts[u][1])
                      for i, u, l in ((468, 159, 145), (473, 386, 374)) if pts[l][1] - pts[u][1] > 1e-3]
                if vs:
                    row["iris_v"] = float(np.mean(vs))
        if self.pose is not None:
            p = self.pose.detect_for_video(img, ts)
            if p.pose_landmarks:
                lm = p.pose_landmarks[0]
                nose, ls, rs = lm[0], lm[11], lm[12]
                if min(nose.visibility, ls.visibility, rs.visibility) >= self.vis_min:
                    a, b = np.array([ls.x * w, ls.y * h]), np.array([rs.x * w, rs.y * h])
                    width = float(np.hypot(*(a - b)))
                    if width > 1e-3:
                        left, right = (a, b) if a[0] < b[0] else (b, a)
                        mid = (a + b) / 2
                        row.update(shoulders=1.0, shoulder_w=width / w, sh_mid_x=float(mid[0] / w),
                                   neck_ratio=float((mid[1] - nose.y * h) / width),
                                   shoulder_tilt=float(np.degrees(np.arctan2(right[1] - left[1], right[0] - left[0]))))
        return row

    def close(self) -> None:
        self.face.close()
        if self.pose is not None:
            self.pose.close()


def extract_features(prep: PreprocessResult, cfg: PipelineConfig,
                     analyzer: Optional[Callable[[np.ndarray, float], dict]] = None) -> tuple[FeatureTable, dict]:
    own = analyzer is None
    analyzer = analyzer or MediaPipeAnalyzer(cfg)
    rows = []
    t0 = time.perf_counter()
    try:
        for t, rgb in iter_video_frames(prep.source, cfg.video_sample_fps, cfg.video_max_width,
                                        prep.video_offset_s, prep.video.width, prep.video.height):
            rows.append(analyzer(rgb, t))
    finally:
        if own:
            analyzer.close()
    table = {c: np.array([r.get(c, np.nan) for r in rows], dtype=float) for c in COLUMNS}
    info = getattr(analyzer, "info", {"analyzer": type(analyzer).__name__})
    return table, {**info, "extract_time_s": round(time.perf_counter() - t0, 2), "frames": len(rows)}


# ------------------------------------------------------------- measurements
def compute_video_metrics(tbl: FeatureTable, cfg: PipelineConfig, model_info: Optional[dict] = None) -> VideoAnalysis:
    n = len(tbl["t"])
    step = 1.0 / cfg.video_sample_fps
    win = max(1, int(round(cfg.smooth_s * cfg.video_sample_fps)))
    t = tbl["t"]
    sampling = {"sample_fps": cfg.video_sample_fps, "frames": n, "max_width": cfg.video_max_width}
    va = VideoAnalysis(
        status=Status.ok, model=model_info or {}, sampling=sampling,
        frames_analyzed=Metric.measured(n, "count"),
        usable_frame_pct=Metric.missing("percent", "no frames"), face_visible_pct=Metric.missing("percent", "no frames"),
        head_toward_camera_pct=Metric.missing("percent", "no usable face"),
        camera_directed_gaze_pct=Metric.missing("percent", "no usable face"),
        limitations=[
            "Gaze is estimated from head pose plus iris position with heuristic gains; it has not been "
            "validated against an eye tracker. Looking toward the camera does not prove eye contact.",
            "Lighting, glasses, low resolution, occlusion and camera placement all reduce accuracy.",
            "Only observable measurements are reported; no inference about confidence, nervousness or emotion."])
    if n == 0:
        va.status = Status.unavailable
        va.warnings.append("No video frames could be read.")
        return va

    face = tbl["face"] == 1
    dark = tbl["brightness"] < cfg.dark_frame_mean
    usable = face & (tbl["face_w"] >= cfg.min_face_width_ratio) & ~dark
    n_use = int(usable.sum())
    va.face_visible_pct = Metric.measured(100 * face.mean(), "percent", denominator=f"{n} sampled frames")
    va.usable_frame_pct = Metric.measured(100 * usable.mean(), "percent", denominator=f"{n} sampled frames",
                                          note=f"face found, face width >= {cfg.min_face_width_ratio:.0%} of frame, not dark")
    va.lighting = {"mean_brightness": Metric.measured(float(np.mean(tbl["brightness"])), "ratio",
                                                      note="mean pixel value 0-255"),
                   "dark_frame_pct": Metric.measured(100 * dark.mean(), "percent", denominator=f"{n} sampled frames")}
    if dark.mean() > 0.3:
        va.warnings.append("The video is poorly lit in many frames; face measurements are less reliable.")
    for s, e, _, _ in runs(~usable, t, step, cfg.min_event_s):
        va.face_not_visible_intervals.append(TimedEvent(type="face_not_usable", start=s, end=e))

    if n_use < max(3, 0.2 * n):
        va.status = Status.unavailable
        va.warnings.append(f"A usable face was found in only {100 * usable.mean():.0f}% of frames; gaze and head "
                           "orientation were not measured. This says nothing about the speaker's behaviour.")
        reason = "too few frames with a usable face"
        va.head_toward_camera_pct = Metric.missing("percent", reason)
        va.camera_directed_gaze_pct = Metric.missing("percent", reason)
        return va

    gap = int(round(0.5 * cfg.video_sample_fps))

    def clean(col: str, mask: np.ndarray = usable) -> np.ndarray:
        """Gap-fill + median-smooth, then re-mask so smoothing never invents values for
        frames without evidence (those stay out of every denominator)."""
        x = smooth(fill_gaps(np.where(mask, tbl[col], np.nan), gap), win)
        return np.where(mask, x, np.nan)

    yaw, pitch = clean("yaw"), clean("pitch")
    head_dev = np.hypot(yaw, pitch)
    valid_head = ~np.isnan(head_dev)
    va.head_toward_camera_pct = Metric.measured(
        100 * float((head_dev[valid_head] <= cfg.head_cone_deg).mean()), "percent",
        denominator=f"{int(valid_head.sum())} frames with a usable face",
        note=f"head direction within {cfg.head_cone_deg:.0f} deg of the camera axis")
    va.head_orientation = {
        "median_yaw_deg": Metric.measured(float(np.nanmedian(yaw)), "degrees", note="+ = toward image right"),
        "median_pitch_deg": Metric.measured(float(np.nanmedian(pitch)), "degrees", note="+ = up"),
        "yaw_spread_deg": Metric.measured(float(np.nanstd(yaw)), "degrees"),
        "pitch_spread_deg": Metric.measured(float(np.nanstd(pitch)), "degrees")}
    speed = np.abs(np.diff(np.hypot(yaw, pitch))) * cfg.video_sample_fps
    if np.isfinite(speed).any():
        va.movement["head_movement_deg_per_s"] = Metric.measured(float(np.nanmean(speed)), "degrees",
                                                                 note="mean angular speed of the head per second")

    ih, iv = clean("iris_h"), clean("iris_v")
    gaze_h = yaw + cfg.iris_gain_h_deg * (ih - 0.5)
    gaze_v = pitch - cfg.iris_gain_v_deg * (iv - 0.5)
    gaze_dev = np.hypot(gaze_h, gaze_v)
    valid_gaze = ~np.isnan(gaze_dev)
    if valid_gaze.sum() >= 3:
        va.camera_directed_gaze_pct = Metric.measured(
            100 * float((gaze_dev[valid_gaze] <= cfg.gaze_cone_deg).mean()), "percent", warn=True,
            denominator=f"{int(valid_gaze.sum())} frames with usable face and iris landmarks",
            note=f"estimated gaze within {cfg.gaze_cone_deg:.0f} deg of the camera; heuristic, unvalidated")
        away = hysteresis(np.where(valid_gaze, gaze_dev, np.nan), cfg.gaze_cone_deg, cfg.gaze_cone_deg * 0.7)
        for s, e, i0, i1 in runs(away, t, step, cfg.min_event_s):
            h, v = float(np.nanmean(gaze_h[i0:i1])), float(np.nanmean(gaze_v[i0:i1]))
            d = ("up" if v > 0 else "down") if abs(v) > abs(h) else ("image_right" if h > 0 else "image_left")
            va.looking_away_events.append(TimedEvent(type="gaze_away_from_camera", start=s, end=e,
                                                     details={"direction": d, "max_deviation_deg":
                                                              round(float(np.nanmax(gaze_dev[i0:i1])), 1)}))
    else:
        va.camera_directed_gaze_pct = Metric.missing("percent", "iris landmarks not available")

    # ---- posture: only with enough shoulder evidence
    shoulders = (tbl["shoulders"] == 1) & usable
    if shoulders.sum() >= max(5, 0.5 * n_use):
        neck = clean("neck_ratio", shoulders)
        base = float(np.nanmedian(neck))
        drop = neck < base * (1 - cfg.posture_drop_ratio)
        events = runs(drop, t, step, 2.0)
        for s, e, i0, i1 in events:
            va.posture_events.append(TimedEvent(type="head_lowered_toward_shoulders", start=s, end=e,
                                                details={"min_ratio_vs_median": round(float(np.nanmin(neck[i0:i1]) / base), 2)}))
        den = f"{int(shoulders.sum())} frames with face and both shoulders visible"
        va.posture = {
            "shoulder_tilt_deg": Metric.measured(float(np.nanmedian(np.abs(tbl["shoulder_tilt"][shoulders]))), "degrees",
                                                 denominator=den, note="median absolute tilt of the shoulder line"),
            "head_lowered_pct": Metric.measured(100 * float(np.nanmean(drop[shoulders])), "percent", denominator=den,
                                                note=f"head-to-shoulder distance >{cfg.posture_drop_ratio:.0%} below this "
                                                     "recording's median; relative, not an absolute posture judgment")}
        x = fill_gaps(np.where(shoulders, tbl["sh_mid_x"], np.nan), gap) / np.nanmedian(tbl["shoulder_w"][shoulders])
        va.movement["torso_sway_shoulder_widths"] = Metric.measured(float(np.nanstd(x)), "ratio",
                                                                    note="std of shoulder-centre position / shoulder width")
    else:
        msg = "shoulders not reliably visible (typical laptop framing); posture not measured"
        va.posture = {"shoulder_tilt_deg": Metric.missing("degrees", msg),
                      "head_lowered_pct": Metric.missing("percent", msg)}

    if usable.mean() < 0.7:
        va.warnings.append(f"A usable face was found in only {100 * usable.mean():.0f}% of frames; percentages use "
                           "only those frames.")
    va.status = Status.warning if va.warnings else Status.ok
    return va


def analyze_video(prep: PreprocessResult, cfg: PipelineConfig,
                  analyzer: Optional[Callable[[np.ndarray, float], dict]] = None) -> VideoAnalysis:
    table, info = extract_features(prep, cfg, analyzer)
    return compute_video_metrics(table, cfg, info)
