"""Per-frame feature extraction with MediaPipe Face / Pose / Hand Landmarkers.

Output is a FeatureTable: {column: float array of length n_frames}, NaN where a
detector found nothing. Frame i is at i / fps seconds (shared clock).

Conventions
    image coordinates are pixels, x right, y down; yaw/pitch/roll in degrees:
    yaw   > 0  face points toward image-right
    pitch > 0  face points up
    roll  > 0  head tilts clockwise on screen
    Head pose comes from MediaPipe's facial transformation matrix (a fit of the
    canonical face model to all 468 landmarks). An earlier 6-point solvePnP
    version had a ~30 degree constant pitch bias on real faces.
    iris_h in [0,1], 0.5 = centred, larger = iris toward image-right
    iris_v in [0,1], 0.5 = centred, larger = iris lower
"""
from pathlib import Path

import cv2
import numpy as np

from app.analysis.vision.models import model_path

COLUMNS = [
    "t", "face", "yaw", "pitch", "roll", "iris_h", "iris_v",
    "face_x0", "face_y0", "face_x1", "face_y1",
    "pose", "neck_ratio", "shoulder_tilt", "shoulder_w", "sh_mid_x", "sh_mid_y",
    "wrist_lx", "wrist_ly", "wrist_rx", "wrist_ry",
    "n_hands", "hand_in_face",
]
FeatureTable = dict[str, np.ndarray]

_FINGERTIPS = [4, 8, 12, 16, 20]
_VIS = 0.5  # pose landmark visibility threshold


def empty_table(n: int) -> FeatureTable:
    return {c: np.full(n, np.nan) for c in COLUMNS}


def _head_pose(matrix) -> tuple[float, float, float]:
    """Yaw/pitch/roll (degrees) from MediaPipe's 4x4 facial transformation matrix.

    The matrix is in an OpenGL-style frame (x right, y up, z toward the camera);
    the face's forward direction is the rotation's third column.
    """
    R = np.array(matrix, dtype=np.float64)[:3, :3]
    R = R / np.linalg.norm(R, axis=0)  # strip the scale
    f = R[:, 2]
    yaw = np.degrees(np.arctan2(f[0], f[2]))
    pitch = np.degrees(np.arctan2(f[1], np.hypot(f[0], f[2])))
    roll = -np.degrees(np.arctan2(R[1, 0], R[0, 0]))  # y-up CCW -> on-screen clockwise
    return float(yaw), float(pitch), float(roll)


def _face_features(lm, matrix, w: int, h: int, row: dict) -> None:
    pts = np.array([[p.x * w, p.y * h] for p in lm])  # (478, 2)
    row["face"] = 1.0
    xs, ys = pts[:, 0], pts[:, 1]
    row["face_x0"], row["face_x1"] = float(xs.min()), float(xs.max())
    row["face_y0"], row["face_y1"] = float(ys.min()), float(ys.max())

    if matrix is not None:
        row["yaw"], row["pitch"], row["roll"] = _head_pose(matrix)

    if len(pts) >= 478:  # iris landmarks present
        def ratio(i, a, b):
            d = pts[b] - pts[a]
            den = float(d @ d)
            return float((pts[i] - pts[a]) @ d / den) if den > 1e-6 else np.nan

        # image-left eye: outer 33 -> inner 133, iris 468; image-right: inner 362 -> outer 263, iris 473
        h_ratio = np.nanmean([ratio(468, 33, 133), ratio(473, 362, 263)])
        v_vals = []
        for iris, up, lo in ((468, 159, 145), (473, 386, 374)):
            span = pts[lo][1] - pts[up][1]
            if span > 1e-3:
                v_vals.append((pts[iris][1] - pts[up][1]) / span)
        row["iris_h"] = float(h_ratio)
        if v_vals:
            row["iris_v"] = float(np.mean(v_vals))


def _pose_features(lm, w: int, h: int, row: dict) -> None:
    def pt(i):
        p = lm[i]
        return np.array([p.x * w, p.y * h]), p.visibility

    nose, vn = pt(0)
    ls, vl = pt(11)
    rs, vr = pt(12)
    if min(vn, vl, vr) >= _VIS:
        width = float(np.hypot(*(ls - rs)))
        if width > 1e-3:
            mid = (ls + rs) / 2
            a, b = (ls, rs) if ls[0] < rs[0] else (rs, ls)  # left-most -> right-most on screen
            row["pose"] = 1.0
            row["shoulder_w"] = width
            row["sh_mid_x"], row["sh_mid_y"] = float(mid[0]), float(mid[1])
            row["neck_ratio"] = float((mid[1] - nose[1]) / width)
            row["shoulder_tilt"] = float(np.degrees(np.arctan2(b[1] - a[1], b[0] - a[0])))
    for name, i in (("l", 15), ("r", 16)):  # wrists
        p, v = pt(i)
        if v >= _VIS:
            row[f"wrist_{name}x"], row[f"wrist_{name}y"] = float(p[0]), float(p[1])


def _hand_features(hands, w: int, h: int, row: dict) -> None:
    row["n_hands"] = float(len(hands))
    touching = 0.0
    x0, x1, y0, y1 = row["face_x0"], row["face_x1"], row["face_y0"], row["face_y1"]
    if not np.isnan(x0):
        mx, my = 0.1 * (x1 - x0), 0.1 * (y1 - y0)  # a bit of margin around the face box
        for lm in hands:
            for i in _FINGERTIPS:
                px, py = lm[i].x * w, lm[i].y * h
                if x0 - mx <= px <= x1 + mx and y0 - my <= py <= y1 + my:
                    touching = 1.0
    row["hand_in_face"] = touching


def extract_features(frames_dir: Path, pattern: str, frame_count: int, fps: int) -> FeatureTable:
    """Run the three landmarkers over frames 0..frame_count-1."""
    import mediapipe as mp
    from mediapipe.tasks.python import BaseOptions, vision

    run_mode = vision.RunningMode.VIDEO

    def opts(cls, kind, **kw):
        return getattr(vision, cls)(
            base_options=BaseOptions(model_asset_path=str(model_path(kind))),
            running_mode=run_mode, **kw)

    table = empty_table(frame_count)
    with vision.FaceLandmarker.create_from_options(
            opts("FaceLandmarkerOptions", "face", num_faces=1,
                 output_facial_transformation_matrixes=True)) as face_det, \
         vision.PoseLandmarker.create_from_options(
            opts("PoseLandmarkerOptions", "pose", num_poses=1)) as pose_det, \
         vision.HandLandmarker.create_from_options(
            opts("HandLandmarkerOptions", "hand", num_hands=2)) as hand_det:

        for i in range(frame_count):
            bgr = cv2.imread(str(frames_dir / pattern.format(i)))
            if bgr is None:
                continue
            h, w = bgr.shape[:2]
            img = mp.Image(image_format=mp.ImageFormat.SRGB,
                           data=cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
            ts = int(i * 1000 / fps)

            row = {c: np.nan for c in COLUMNS}
            row["t"] = i / fps
            row["face"] = 0.0
            row["pose"] = 0.0

            f = face_det.detect_for_video(img, ts)
            if f.face_landmarks:
                matrix = f.facial_transformation_matrixes[0] if f.facial_transformation_matrixes else None
                _face_features(f.face_landmarks[0], matrix, w, h, row)
            p = pose_det.detect_for_video(img, ts)
            if p.pose_landmarks:
                _pose_features(p.pose_landmarks[0], w, h, row)
            hd = hand_det.detect_for_video(img, ts)
            _hand_features(hd.hand_landmarks, w, h, row)

            for c in COLUMNS:
                table[c][i] = row[c]
    return table


def save_features_csv(table: FeatureTable, path: Path) -> None:
    n = len(table["t"])
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(",".join(COLUMNS) + "\n")
        for i in range(n):
            fh.write(",".join("" if np.isnan(table[c][i]) else f"{table[c][i]:.4f}"
                              for c in COLUMNS) + "\n")
