"""Debug overlay video: raw signals + active events drawn on each frame.

Use it to tune thresholds in config.py - you can see exactly when and why a
look_away / slouch / ... event fires.  Output: <run_dir>/debug_vision.mp4
"""
import shutil
import subprocess
from pathlib import Path

import cv2
import numpy as np

from app.analysis.config import AnalysisConfig
from app.analysis.preprocess import PreprocessResult
from app.analysis.schemas import Event
from app.analysis.vision.landmarks import FeatureTable

_COLORS = {  # BGR
    "look_away": (0, 0, 255), "face_lost": (0, 0, 160), "slouch": (0, 140, 255),
    "lean": (0, 200, 255), "sway": (255, 0, 255), "face_touch": (255, 120, 0),
    "fidget": (255, 200, 0),
}


def render_debug_video(
    run: PreprocessResult, tbl: FeatureTable, events: list[Event],
    baseline: dict, cfg: AnalysisConfig,
) -> Path:
    m = run.metadata
    out_dir = run.run_dir / "debug_frames"
    out_dir.mkdir(exist_ok=True)
    pattern = Path(m.frames_pattern).name

    for i in range(m.frame_count):
        img = cv2.imread(str(run.frames_dir / pattern.format(i)))
        if img is None:
            continue
        t = i / m.frame_fps
        active = [e for e in events if e.start <= t < e.end]

        def val(key, fmt="{:.1f}"):
            v = tbl[key][i]
            return "-" if np.isnan(v) else fmt.format(v)

        lines = [
            f"t={t:5.1f}s  yaw {val('yaw')} pitch {val('pitch')}",
            f"iris h {val('iris_h', '{:.2f}')} v {val('iris_v', '{:.2f}')}  neck {val('neck_ratio', '{:.2f}')}"
            f" (base {baseline.get('neck_ratio') or 0:.2f})",
            f"hands {val('n_hands', '{:.0f}')}  tilt {val('shoulder_tilt')}",
        ] + [f"! {e.type} {e.meta.get('direction', '')}".strip() for e in active]

        for k, line in enumerate(lines):
            color = (255, 255, 255) if k < 3 else _COLORS.get(active[k - 3].type, (0, 255, 255))
            cv2.putText(img, line, (8, 20 + 22 * k), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 3)
            cv2.putText(img, line, (8, 20 + 22 * k), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        if not np.isnan(tbl["face_x0"][i]):
            cv2.rectangle(img, (int(tbl["face_x0"][i]), int(tbl["face_y0"][i])),
                          (int(tbl["face_x1"][i]), int(tbl["face_y1"][i])), (0, 255, 0), 1)
        if not np.isnan(tbl["sh_mid_x"][i]):
            cv2.circle(img, (int(tbl["sh_mid_x"][i]), int(tbl["sh_mid_y"][i])), 5, (0, 255, 255), -1)
        for s in ("l", "r"):
            if not np.isnan(tbl[f"wrist_{s}x"][i]):
                cv2.circle(img, (int(tbl[f"wrist_{s}x"][i]), int(tbl[f"wrist_{s}y"][i])), 6, (255, 0, 0), -1)
        if active:
            h, w = img.shape[:2]
            cv2.rectangle(img, (0, 0), (w - 1, h - 1), _COLORS.get(active[0].type, (0, 255, 255)), 4)
        cv2.imwrite(str(out_dir / pattern.format(i)), img)

    out = run.run_dir / "debug_vision.mp4"
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-framerate", str(m.frame_fps),
         "-i", str(out_dir / pattern.replace("{:06d}", "%06d")),
         "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out)],
        check=True,
    )
    shutil.rmtree(out_dir, ignore_errors=True)
    return out
