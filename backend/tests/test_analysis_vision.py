"""Unit tests for phase 3 logic on synthetic feature tables (no MediaPipe needed)."""
import numpy as np

from app.analysis.config import DEFAULT_CONFIG as CFG
from app.analysis.vision.behaviors import analyze_behaviors
from app.analysis.vision.landmarks import empty_table
from app.analysis.vision.signals import fill_gaps, hysteresis, mask_to_events, smooth

FPS = 10


def test_fill_gaps_only_short_interior_gaps():
    x = np.array([1, np.nan, 3, np.nan, np.nan, np.nan, 7, np.nan])
    out = fill_gaps(x, max_gap=2)
    assert out[1] == 2.0
    assert np.isnan(out[3:6]).all()  # gap of 3 > max_gap
    assert np.isnan(out[7])  # trailing NaN is never extrapolated


def test_smooth_removes_single_frame_spike():
    x = np.zeros(20)
    x[10] = 100
    assert smooth(x, 5).max() == 0


def test_hysteresis_holds_state_until_exit_level():
    x = np.array([0, 25, 15, 15, 5, 15])  # enter > 20, exit < 12
    assert hysteresis(x, 20, 12).tolist() == [False, True, True, True, False, False]
    # below=True: on under 0.85, off again only above 0.92
    y = np.array([1.0, 0.8, 0.9, 0.95, 0.9])
    assert hysteresis(y, 0.85, 0.92, below=True).tolist() == [False, True, True, False, False]


def test_mask_to_events_merges_and_drops_short():
    mask = np.zeros(100, dtype=bool)
    mask[10:30] = True   # 2.0 s
    mask[32:40] = True   # 0.2 s gap -> merged with the first
    mask[60:63] = True   # 0.3 s -> dropped (min 1.0)
    assert mask_to_events(mask, FPS, min_dur=1.0, merge_gap=0.5) == [(1.0, 4.0)]


def make_session():
    n = 600  # 60 s @ 10 fps
    t = empty_table(n)
    t["t"] = np.arange(n) / FPS
    t["face"][:] = 1; t["pose"][:] = 1
    for k, v in dict(yaw=0, pitch=0, roll=0, iris_h=.5, iris_v=.5, neck_ratio=1.0,
                     shoulder_tilt=0, shoulder_w=200, sh_mid_x=320, sh_mid_y=300,
                     wrist_lx=250, wrist_ly=500, wrist_rx=390, wrist_ry=500,
                     n_hands=0, hand_in_face=0).items():
        t[k][:] = v
    t["yaw"][100:140] = 40               # 10-14 s   look right
    t["yaw"][200:203] = 40               # 0.3 s glance: ignored
    t["pitch"][250:290] = -35            # 25-29 s   look down (reading notes)
    t["neck_ratio"][300:400] = 0.7       # 30-40 s   slouch
    t["n_hands"][450:460] = 1; t["hand_in_face"][450:460] = 1  # 1 s face touch
    for k in ("face", "yaw", "pitch", "roll", "iris_h", "iris_v"):  # 50-53 s no face
        t[k][500:530] = 0 if k == "face" else np.nan
    return t


def by_type(events, type_):
    return [e for e in events if e.type == type_]


def test_behaviors_on_planted_session():
    events, metrics, base = analyze_behaviors(make_session(), FPS, CFG)

    assert base["source"] == "calibration" and base["yaw"] == 0

    away = by_type(events, "look_away")
    assert len(away) == 2  # the 0.3 s glance is dropped
    assert (away[0].meta["direction"], away[0].meta["reading_notes"]) == ("right", False)
    assert (away[1].meta["direction"], away[1].meta["reading_notes"]) == ("down", True)
    assert abs(away[0].start - 10.0) < 0.3 and abs(away[0].end - 14.0) < 0.3

    assert len(by_type(events, "slouch")) == 1
    assert len(by_type(events, "face_touch")) == 1
    lost = by_type(events, "face_lost")
    assert len(lost) == 1 and abs(lost[0].end - lost[0].start - 3.0) < 0.3
    assert by_type(events, "sway") == [] and by_type(events, "fidget") == []

    assert metrics.look_away_count == 2
    assert 85 < metrics.eye_contact_pct < 87  # (570 valid - ~80 away) / 570
    assert metrics.reading_notes_s > 3.5
    assert metrics.slouch_count == 1 and 15 < metrics.slouch_pct < 18
    assert metrics.face_touch_count == 1


def test_no_calibration_falls_back_to_clip_median():
    t = make_session()
    t["face"][:25] = 0
    for k in ("yaw", "pitch", "iris_h", "iris_v", "neck_ratio", "shoulder_tilt", "shoulder_w"):
        t[k][:25] = np.nan  # nothing detected during the calibration window
    _, _, base = analyze_behaviors(t, FPS, CFG)
    assert base["source"] == "clip_median"


def test_fidget_and_sway_detected():
    t = make_session()
    n = len(t["t"])
    idx = np.arange(n)
    # 20-30 s: right wrist waves at 0.7 Hz (~2 shoulder-widths/s on average);
    # 40-50 s: body rocks side to side
    swing = (idx >= 200) & (idx < 300)
    t["wrist_rx"][swing] = 390 + 150 * np.sin(2 * np.pi * 0.7 * idx[swing] / FPS)
    rock = (idx >= 400) & (idx < 500)
    t["sh_mid_x"][rock] = 320 + 80 * np.sin(idx[rock] * 0.6)
    events, metrics, _ = analyze_behaviors(t, FPS, CFG)
    assert len(by_type(events, "fidget")) >= 1
    assert len(by_type(events, "sway")) >= 1
    assert metrics.fidget_pct > 5
