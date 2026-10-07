"""Phase 4 tests on synthetic phase-2/3 outputs (no models, no video)."""
import pytest

from app.analysis.config import DEFAULT_CONFIG as CFG
from app.analysis.fusion.pipeline import build_report
from app.analysis.fusion.scoring import band, lin
from app.analysis.schemas import (AudioAnalysis, AudioMetrics, Event, VisionAnalysis,
                                  VisionMetrics)


def audio_metrics(**kw):
    base = dict(total_duration_s=60, start_delay_s=1, speaking_span_s=55, word_count=140,
                wpm=150, filler_count=2, fillers_per_min=2.2, filler_breakdown={},
                repetition_count=0, pause_count=8, long_pause_count=0,
                hesitation_pause_count=1, avg_pause_s=0.6, silence_ratio=0.1,
                pitch_mean_hz=120, pitch_std_semitones=3.5, intensity_std_db=6)
    base.update(kw)
    return AudioMetrics(**base)


def vision_metrics(**kw):
    base = dict(frames=600, face_visible_pct=100, eye_contact_pct=80, look_away_count=3,
                look_away_total_s=8, longest_look_away_s=4, reading_notes_s=0, face_lost_s=0,
                slouch_pct=2, slouch_count=0, lean_pct=1, sway_pct=0, hands_visible_pct=50,
                face_touch_count=0, fidget_pct=2, head_motion_deg_s=10)
    base.update(kw)
    return VisionMetrics(**base)


def audio(events=(), **kw):
    return AudioAnalysis(run_id="t", transcript="hello", words=[], events=list(events),
                         metrics=audio_metrics(**kw), asr_model="small")


def vision(events=(), **kw):
    return VisionAnalysis(run_id="t", baseline={"source": "calibration"},
                          events=list(events), metrics=vision_metrics(**kw))


def filler(t, label="um"):
    return Event(type="filler", source="audio", start=t, end=t + 0.3,
                 meta={"label": label, "kind": "non_lexical"})


def look_away(a, b):
    return Event(type="look_away", source="video", start=a, end=b,
                 meta={"direction": "left", "reading_notes": False})


def test_lin_and_band():
    assert lin(1, good=1, bad=10) == 100 and lin(10, 1, 10) == 0 and lin(55, 1, 10) == 0
    assert lin(5.5, 1, 10) == pytest.approx(50)
    assert lin(0.2, good=0.15, bad=0.5) == pytest.approx(85.7, abs=0.1)
    assert band(140, 90, 120, 160, 200) == 100
    assert band(105, 90, 120, 160, 200) == pytest.approx(50)
    assert band(230, 90, 120, 160, 200) == 0


def test_good_speaker_outscores_struggling_speaker_and_drivers_explain():
    good = build_report("g", 60, audio(), vision())
    bad = build_report(
        "b", 60,
        audio(filler_count=14, repetition_count=4, long_pause_count=3, hesitation_pause_count=9,
              wpm=75, pitch_std_semitones=0.8, silence_ratio=0.45),
        vision(eye_contact_pct=30, slouch_pct=35, fidget_pct=30, face_touch_count=5,
               reading_notes_s=15))
    assert good.scores.overall > 80
    assert bad.scores.overall < 40
    drivers = bad.scores.fluency.drivers
    assert drivers[0].metric == "fillers_per_min"
    assert [d.points_lost for d in drivers] == sorted((d.points_lost for d in drivers), reverse=True)


def test_missing_vision_renormalises_weights():
    r = build_report("a", 60, audio(), None)
    assert r.scores.eye_contact is None and r.scores.posture is None
    assert set(r.scores.weights_used) == {"fluency", "delivery"}
    assert sum(r.scores.weights_used.values()) == pytest.approx(1.0, abs=0.01)
    assert r.scores.overall is not None
    assert any("Vision analysis missing" in w for w in r.warnings)


def test_requires_some_input():
    with pytest.raises(ValueError):
        build_report("x", 60, None, None)


def test_clusters_correlations_and_segments():
    fillers = [filler(10.0), filler(11.0, "uh"), filler(12.5)]
    lone_pause = Event(type="long_pause", source="audio", start=40, end=43,
                       meta={"duration_s": 3, "position": "hesitation", "filled": False})
    r = build_report("c", 70, audio(fillers + [lone_pause]), vision([look_away(9.5, 13.0)]))

    assert len(r.clusters) == 1  # the lone pause is not a cluster
    c = r.clusters[0]
    assert c.start == 10.0 and c.counts == {"um": 2, "uh": 1}
    assert c.concurrent_video == {"look_away": 1}

    co = r.correlations["fillers_vs_look_away"]
    assert co["events"] == 3 and co["fraction"] == 1.0
    assert co["baseline_fraction"] == pytest.approx(3.5 / 70, abs=0.01)
    assert r.correlations["hesitations_vs_look_away"]["overlapping"] == 0

    assert [(s.start, s.end) for s in r.segments] == [(0.0, 30.0), (30.0, 60.0), (60.0, 70.0)]
    assert r.segments[0].fillers == 3 and r.segments[1].long_pauses == 1
    assert r.segments[0].look_away_s == 3.5
    assert r.segments[0].eye_contact_pct == pytest.approx(88.3, abs=0.1)
    assert [e.start for e in r.events] == sorted(e.start for e in r.events)


def test_tiny_tail_segment_is_folded():
    r = build_report("t", 62, audio(), vision())
    assert [(s.start, s.end) for s in r.segments] == [(0.0, 30.0), (30.0, 62.0)]


def test_warnings_for_small_model_and_missing_fillers():
    r = build_report("w", 60, audio(filler_count=0), vision(face_visible_pct=40))
    text = " ".join(r.warnings)
    assert "under-counted" not in text  # asr_model is 'small'
    assert "No fillers found" in text and "Face visible in only 40" in text
    a = audio()
    a.asr_model = "tiny"
    assert any("under-counted" in w for w in build_report("w", 60, a, None).warnings)


def test_ml_training_and_prediction_plumbing(tmp_path):
    """Plumbing only: labels here are generated from the rule score, NOT human ratings."""
    pytest.importorskip("sklearn")
    pytest.importorskip("joblib")
    from app.analysis.fusion import ml

    rows = ["run_id,score"]
    for i in range(12):
        rep = build_report(f"r{i}", 60, audio(filler_count=i, hesitation_pause_count=i // 2),
                           vision(eye_contact_pct=90 - 5 * i))
        d = tmp_path / f"r{i}"
        d.mkdir()
        (d / "session_report.json").write_text(rep.model_dump_json(), encoding="utf-8")
        rows.append(f"r{i},{rep.scores.overall}")
    csv_path = tmp_path / "labels.csv"
    csv_path.write_text("\n".join(rows), encoding="utf-8")

    model_path = tmp_path / "model.joblib"
    ml.train(str(csv_path), runs_dir=tmp_path, out=model_path)

    feats = build_report("x", 60, audio(filler_count=3), vision()).features
    score, name = ml.predict(feats, model_path)
    assert 0 <= score <= 100 and name
    assert ml.predict(feats, tmp_path / "missing.joblib") == (None, None)

    with_model = build_report("x", 60, audio(), vision(), model_path=model_path)
    assert with_model.scores.ml_overall is not None
