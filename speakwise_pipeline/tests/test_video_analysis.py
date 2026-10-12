"""Video tests.

* Logic tests use synthetic per-frame feature tables (known truth, no model).
* One integration test runs MediaPipe on a still public-domain portrait: it checks that
  face detection runs end to end, NOT that gaze/posture estimates are accurate.
"""
from pathlib import Path

import numpy as np
import pytest
from conftest import ffmpeg, needs_ffmpeg

from speakwise import models
from speakwise.config import PipelineConfig
from speakwise.media_preprocessing import preprocess_mp4
from speakwise.schemas import Status
from speakwise.video_analysis import COLUMNS, analyze_video, compute_video_metrics, hysteresis, runs

FPS = 5.0
CFG = PipelineConfig(video_sample_fps=FPS)
PORTRAIT = Path(__file__).parent / "assets" / "portrait_public_domain.jpg"


def table(n=150, **cols):
    t = {c: np.full(n, np.nan) for c in COLUMNS}
    t["t"] = np.arange(n) / FPS
    base = dict(face=1.0, face_w=0.3, yaw=0.0, pitch=0.0, roll=0.0, iris_h=0.5, iris_v=0.5, brightness=120.0,
                shoulders=1.0, neck_ratio=0.6, shoulder_tilt=1.0, shoulder_w=0.4, sh_mid_x=0.5)
    for k, v in {**base, **cols}.items():
        t[k][:] = v
    return t


def test_hysteresis_and_runs():
    x = np.array([0, 25, 14, 12, 5, 30, np.nan])
    assert hysteresis(x, 15, 10).tolist() == [False, True, True, True, False, True, False]
    m = np.array([0, 1, 1, 1, 1, 1, 0, 1, 0], bool)
    assert runs(m, np.arange(9) / FPS, 1 / FPS, 1.0) == [(0.2, 1.2, 1, 6)]


def test_attentive_speaker():
    va = compute_video_metrics(table(), CFG)
    assert va.status == Status.ok
    assert va.face_visible_pct.value == 100 and va.camera_directed_gaze_pct.value == 100
    assert va.looking_away_events == [] and va.posture_events == []
    assert va.camera_directed_gaze_pct.status == Status.warning  # always flagged as an estimate


def test_look_away_and_missing_face_are_kept_separate():
    tb = table()
    tb["yaw"][50:70] = 40  # 4 s looking to the side
    tb["face"][100:125] = 0  # 5 s no face (out of frame)
    for c in ("yaw", "pitch", "iris_h", "iris_v", "face_w"):
        tb[c][100:125] = np.nan
    va = compute_video_metrics(tb, CFG)
    assert len(va.looking_away_events) == 1
    ev = va.looking_away_events[0]
    assert ev.details["direction"] == "image_right" and 9.5 <= ev.start <= 10.5
    assert [(i.start, i.end) for i in va.face_not_visible_intervals] == [(20.0, 25.0)]
    # missing-face frames are excluded from the denominator, not counted as looking away
    assert "125 frames" in va.camera_directed_gaze_pct.denominator
    assert va.camera_directed_gaze_pct.value == pytest.approx(100 * (125 - 20) / 125, abs=2)
    assert va.face_visible_pct.value == pytest.approx(100 * 125 / 150)


def test_no_face_means_unavailable_not_bad():
    tb = table(face=0.0)
    for c in ("yaw", "pitch", "iris_h", "iris_v", "face_w"):
        tb[c][:] = np.nan
    va = compute_video_metrics(tb, CFG)
    assert va.status == Status.unavailable
    assert va.camera_directed_gaze_pct.value is None and va.camera_directed_gaze_pct.status == Status.unavailable
    assert "says nothing about the speaker" in va.warnings[0]


def test_posture_only_with_visible_shoulders():
    tb = table(shoulders=0.0)
    va = compute_video_metrics(tb, CFG)
    assert va.posture["head_lowered_pct"].status == Status.unavailable
    tb = table()
    tb["neck_ratio"][60:90] = 0.4  # 6 s with the head sunk toward the shoulders
    va = compute_video_metrics(tb, CFG)
    assert len(va.posture_events) == 1 and va.posture["head_lowered_pct"].value == pytest.approx(20, abs=3)


def test_dark_video_warns():
    va = compute_video_metrics(table(brightness=20.0), CFG)
    assert va.status == Status.unavailable  # dark frames are not usable
    assert va.lighting["dark_frame_pct"].value == 100


@needs_ffmpeg
@pytest.mark.models
def test_mediapipe_runs_on_still_portrait(tmp_path):
    if not models.is_available("face_landmarker"):
        pytest.skip("face_landmarker model not downloaded")
    mp4 = tmp_path / "portrait.mp4"
    ffmpeg("-loop", "1", "-framerate", "10", "-i", str(PORTRAIT), "-f", "lavfi", "-i", "sine=frequency=200:duration=4",
           "-t", "4", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(mp4))
    cfg = PipelineConfig(video_sample_fps=FPS, work_dir=tmp_path / "w")
    prep = preprocess_mp4(mp4, cfg)
    try:
        va = analyze_video(prep, cfg)
    finally:
        prep.workspace.cleanup()
    assert va.frames_analyzed.value >= 18
    assert va.face_visible_pct.value > 90  # MediaPipe found the face
    assert va.head_orientation["yaw_spread_deg"].value < 2  # still image: stable estimates
