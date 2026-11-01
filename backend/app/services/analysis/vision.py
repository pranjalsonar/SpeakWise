"""Video analysis: eye contact, posture, gestures, nervous signals (MediaPipe Tasks API).

Ported from the POC's vision.py. Differences: frames come from PyAV instead of OpenCV, and
the correct orientation is detected from the face because phone recordings often carry
rotation metadata that decoders apply inconsistently.
"""
import itertools
import math
import urllib.request

import mediapipe as mp
import numpy as np
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision

from app.core.config import settings
from app.services.analysis.media import iter_frames, rotate

SAMPLE_FPS = 10   # face every frame, pose every 2nd frame

FACE_TASK = settings.MODELS_DIR / "face_landmarker.task"
POSE_TASK = settings.MODELS_DIR / "pose_landmarker_full.task"
FACE_URL = ("https://storage.googleapis.com/mediapipe-models/face_landmarker/"
            "face_landmarker/float16/1/face_landmarker.task")
POSE_URL = ("https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
            "pose_landmarker_full/float16/1/pose_landmarker_full.task")


def ensure_models():
    settings.MODELS_DIR.mkdir(parents=True, exist_ok=True)
    for path, url in ((FACE_TASK, FACE_URL), (POSE_TASK, POSE_URL)):
        if not path.exists():
            tmp = path.with_suffix(".part")
            urllib.request.urlretrieve(url, tmp)
            tmp.replace(path)


def _landmarkers():
    # VIDEO-mode landmarkers are stateful, so create fresh ones for every recording.
    face = mp_vision.FaceLandmarker.create_from_options(mp_vision.FaceLandmarkerOptions(
        base_options=mp_python.BaseOptions(model_asset_path=str(FACE_TASK)),
        running_mode=mp_vision.RunningMode.VIDEO,
        num_faces=1,
        output_face_blendshapes=True,
    ))
    pose = mp_vision.PoseLandmarker.create_from_options(mp_vision.PoseLandmarkerOptions(
        base_options=mp_python.BaseOptions(model_asset_path=str(POSE_TASK)),
        running_mode=mp_vision.RunningMode.VIDEO,
        num_poses=1,
    ))
    return face, pose


def _detect_orientation(frames: list) -> int:
    """Quarter turns (0-3) that make the face upright, judged on a few sample frames."""
    if not frames:
        return 0
    samples = [frames[i][1] for i in np.linspace(0, len(frames) - 1, min(4, len(frames))).astype(int)]
    detector = mp_vision.FaceLandmarker.create_from_options(mp_vision.FaceLandmarkerOptions(
        base_options=mp_python.BaseOptions(model_asset_path=str(FACE_TASK)),
        running_mode=mp_vision.RunningMode.IMAGE,
        num_faces=1,
    ))
    try:
        hits = []
        for k in range(4):
            n = 0
            for img in samples:
                res = detector.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=rotate(img, k)))
                n += bool(res.face_landmarks)
            hits.append(n)
        return int(np.argmax(hits))  # ties keep the lowest k (no rotation)
    finally:
        detector.close()


def _pct(flags):
    return 100.0 * float(np.mean(flags)) if len(flags) else 0.0


def analyze_video(video_path: str, progress=None) -> dict:
    face_lm, pose_lm = _landmarkers()
    frames_iter = iter_frames(video_path, fps=SAMPLE_FPS)
    head = list(itertools.islice(frames_iter, 40))
    turns = _detect_orientation(head)

    rows = []          # per-frame face metrics
    pose_rows = []     # per pose frame
    last_ts = -1
    try:
        for idx, (t, raw) in enumerate(itertools.chain(head, frames_iter)):
            frame = rotate(raw, turns)
            h, w = frame.shape[:2]
            ts = max(int(t * 1000), last_ts + 1)   # MediaPipe needs strictly increasing timestamps
            last_ts = ts
            image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
            if progress and idx % 100 == 0:
                progress(t)

            fres = face_lm.detect_for_video(image, ts)
            if fres.face_landmarks:
                lm = fres.face_landmarks[0]
                bs = {c.category_name: c.score for c in fres.face_blendshapes[0]}
                nose, lcheek, rcheek = lm[1], lm[234], lm[454]
                eye_y = (lm[33].y + lm[263].y) / 2
                chin = lm[152]
                face_w = abs(rcheek.x - lcheek.x) or 1e-6
                yaw_ratio = (nose.x - min(lcheek.x, rcheek.x)) / face_w          # 0.5 = facing camera
                pitch_ratio = (nose.y - eye_y) / max(chin.y - eye_y, 1e-6)      # ~0.45 = level
                facing = abs(yaw_ratio - 0.5) < 0.13 and 0.25 < pitch_ratio < 0.65
                look_h = max(bs.get("eyeLookOutLeft", 0), bs.get("eyeLookOutRight", 0),
                             bs.get("eyeLookInLeft", 0), bs.get("eyeLookInRight", 0))
                look_up = max(bs.get("eyeLookUpLeft", 0), bs.get("eyeLookUpRight", 0))
                look_down = max(bs.get("eyeLookDownLeft", 0), bs.get("eyeLookDownRight", 0))
                gaze_ok = look_h < 0.55 and look_up < 0.55 and look_down < 0.6
                blink = (bs.get("eyeBlinkLeft", 0) + bs.get("eyeBlinkRight", 0)) / 2
                rows.append({
                    "t": t, "face": True, "eye_contact": facing and gaze_ok,
                    "looking_down": look_down >= 0.6 or pitch_ratio >= 0.65,
                    "blink_closed": blink > 0.5,
                    "smile": (bs.get("mouthSmileLeft", 0) + bs.get("mouthSmileRight", 0)) / 2 > 0.35,
                    "tense": max(bs.get("browDownLeft", 0), bs.get("browDownRight", 0),
                                 (bs.get("mouthPressLeft", 0) + bs.get("mouthPressRight", 0)) / 2) > 0.45,
                    "brow_raise": bs.get("browInnerUp", 0),
                    "nose": (nose.x, nose.y), "face_w": face_w,
                })
            else:
                rows.append({"t": t, "face": False, "eye_contact": False, "looking_down": False,
                             "blink_closed": False, "smile": False, "tense": False,
                             "brow_raise": 0.0, "nose": None, "face_w": None})

            if idx % 2 == 0:
                pres = pose_lm.detect_for_video(image, ts)
                if pres.pose_landmarks:
                    p = pres.pose_landmarks[0]
                    pt = lambda i: np.array([p[i].x * w, p[i].y * h])
                    vis = lambda i: (p[i].visibility or 0) > 0.5
                    row = {"t": t, "shoulders": vis(11) and vis(12)}
                    if row["shoulders"]:
                        ls, rs, nose = pt(11), pt(12), pt(0)
                        sw = np.linalg.norm(ls - rs) or 1e-6
                        mid = (ls + rs) / 2
                        row["tilt"] = abs(math.degrees(math.atan2(ls[1] - rs[1], ls[0] - rs[0])))
                        row["tilt"] = min(row["tilt"], 180 - row["tilt"])
                        row["neck"] = (mid[1] - nose[1]) / sw
                        row["sw"] = sw
                        row["mid"] = mid
                        wrists = {}
                        for side, wi in (("l", 15), ("r", 16)):
                            if vis(wi):
                                wrists[side] = pt(wi)
                        row["wrists"] = wrists
                        row["touch_face"] = any(
                            np.linalg.norm(wp - nose) < 0.45 * sw for wp in wrists.values()
                        )
                        row["arms_crossed"] = (
                            "l" in wrists and "r" in wrists
                            and (wrists["l"][0] - mid[0]) * (ls[0] - mid[0]) < 0
                            and (wrists["r"][0] - mid[0]) * (rs[0] - mid[0]) < 0
                            and wrists["l"][1] > mid[1] and wrists["r"][1] > mid[1]
                        )
                    pose_rows.append(row)
                else:
                    pose_rows.append({"t": t, "shoulders": False})
    finally:
        face_lm.close()
        pose_lm.close()

    n = len(rows)
    if n == 0:
        return empty_video_metrics()
    duration = rows[-1]["t"] + 1.0 / SAMPLE_FPS
    minutes = max(duration / 60.0, 1e-6)
    face_rows = [r for r in rows if r["face"]]

    # Blinks: closed-eye onsets.
    blinks = sum(1 for a, b in zip(rows, rows[1:]) if b["blink_closed"] and not a["blink_closed"])

    # Head movement: nose motion normalised by face width, per second.
    head_speed = []
    for a, b in zip(face_rows, face_rows[1:]):
        dt = b["t"] - a["t"]
        if 0 < dt < 0.5:
            d = math.hypot(b["nose"][0] - a["nose"][0], b["nose"][1] - a["nose"][1])
            head_speed.append(d / b["face_w"] / dt)
    head_speed = np.array(head_speed) if head_speed else np.array([0.0])

    # Posture.
    sp = [r for r in pose_rows if r.get("shoulders")]
    if sp:
        necks = np.array([r["neck"] for r in sp])
        baseline = float(np.percentile(necks, 80))
        slouch = [(r["neck"] < 0.8 * baseline) or (r["neck"] < 0.3) for r in sp]
        tilted = [r["tilt"] > 8 for r in sp]
        crossed = [r["arms_crossed"] for r in sp]
        # Face-touch events (onsets), not frames.
        touches = sum(1 for a, b in zip(sp, sp[1:]) if b["touch_face"] and not a["touch_face"])
        # Hand activity: wrist speed in shoulder-widths per second.
        gest, fidget = [], []
        for a, b in zip(sp, sp[1:]):
            dt = b["t"] - a["t"]
            if not (0 < dt < 0.6):
                continue
            speeds = [np.linalg.norm(b["wrists"][s] - a["wrists"][s]) / b["sw"] / dt
                      for s in ("l", "r") if s in a["wrists"] and s in b["wrists"]]
            if speeds:
                s = max(speeds)
                gest.append(0.25 < s < 2.5)
                fidget.append(s >= 2.5)
        hands_visible = _pct([bool(r["wrists"]) for r in sp])
    else:
        slouch = tilted = crossed = gest = fidget = []
        touches = 0
        hands_visible = 0.0

    # Eye-contact timeline in 5-second bins.
    timeline = []
    bin_s = 5
    for start in range(0, int(math.ceil(duration)), bin_s):
        chunk = [r["eye_contact"] for r in rows if start <= r["t"] < start + bin_s]
        if chunk:
            timeline.append({"second": start, "eye_contact_pct": round(_pct(chunk), 1)})

    brow = np.array([r["brow_raise"] for r in face_rows]) if face_rows else np.array([0.0])

    return {
        "frames_analyzed": n,
        "face_visible_pct": round(_pct([r["face"] for r in rows]), 1),
        "eye_contact_pct": round(_pct([r["eye_contact"] for r in rows]), 1),
        "looking_down_pct": round(_pct([r["looking_down"] for r in rows]), 1),
        "eye_contact_timeline": timeline,
        "blinks_per_min": round(blinks / minutes, 1),
        "smile_pct": round(_pct([r["smile"] for r in face_rows]), 1),
        "tension_pct": round(_pct([r["tense"] for r in face_rows]), 1),
        "expressiveness": round(float(np.std(brow)) * 100, 1),
        "head_movement": round(float(np.median(head_speed)), 3),
        "excess_head_movement_pct": round(_pct(head_speed > 0.6), 1),
        "posture_detected_pct": round(_pct([r.get("shoulders", False) for r in pose_rows]), 1),
        "slouch_pct": round(_pct(slouch), 1),
        "shoulder_tilt_pct": round(_pct(tilted), 1),
        "arms_crossed_pct": round(_pct(crossed), 1),
        "face_touch_count": int(touches),
        "hands_visible_pct": round(hands_visible, 1),
        "gesture_pct": round(_pct(gest), 1),
        "fidget_pct": round(_pct(fidget), 1),
        "rotation_applied": turns * 90,
    }


def empty_video_metrics() -> dict:
    """Used when the recording has no readable video track."""
    keys = ["face_visible_pct", "eye_contact_pct", "looking_down_pct", "blinks_per_min", "smile_pct",
            "tension_pct", "expressiveness", "head_movement", "excess_head_movement_pct",
            "posture_detected_pct", "slouch_pct", "shoulder_tilt_pct", "arms_crossed_pct",
            "hands_visible_pct", "gesture_pct", "fidget_pct"]
    return {"frames_analyzed": 0, "eye_contact_timeline": [], "face_touch_count": 0,
            "rotation_applied": 0, **{k: 0.0 for k in keys}}
