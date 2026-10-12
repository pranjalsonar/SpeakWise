"""End-to-end tests through process_session on the synthetic MP4 fixture.

`reference_transcriber` is a TEST DOUBLE: it returns the fixture's known script with words
spread evenly over the known speech segments, so the rest of the pipeline (real VAD, real
MediaPipe, real context models when downloaded) can be tested on machines that cannot run
Whisper. test_real_asr_end_to_end runs the actual speech recogniser (marked slow).
"""
import json
import os
from pathlib import Path

import pytest
from conftest import needs_ffmpeg

from speakwise import models
from speakwise.audio_transcription import build_transcription
from speakwise.config import PipelineConfig
from speakwise.fixtures import available_tts, build_fixture
from speakwise.pipeline import process_session
from speakwise.schemas import SessionReport, Status, WordToken

ROOT = Path(__file__).resolve().parents[1]
MATERIAL = (ROOT / "data" / "context_eval" / "materials" / "climate_change.txt").read_text(encoding="utf-8")
TOPIC = "Climate change: causes, effects and what we can do"
pytestmark = [needs_ffmpeg, pytest.mark.skipif(available_tts() is None, reason="no TTS engine for the fixture")]


@pytest.fixture(scope="module")
def fixture(tmp_path_factory):
    d = tmp_path_factory.mktemp("fixture")
    truth = build_fixture(d)
    return d / truth["mp4"], truth


def reference_transcriber(truth):
    """TEST DOUBLE (not real ASR): known words placed evenly inside each known speech segment."""
    def fn(audio, rate, cfg, env):
        words = []
        for seg in truth["speech_segments"]:
            toks = seg["text"].split()
            step = (seg["end"] - seg["start"]) / len(toks)
            for i, t in enumerate(toks):
                s = seg["start"] + i * step
                words.append(WordToken(text=t, start=round(s, 3), end=round(s + step * 0.85, 3), probability=0.95))
        return build_transcription(words, [], cfg, model_info={"model": "reference-transcript TEST DOUBLE"})
    return fn


def cfg_for(tmp_path, **kw):
    return PipelineConfig(work_dir=tmp_path / "work", output_dir=tmp_path / "out", allow_downloads=False, **kw)


def leftover_workspaces(cfg):
    return list(Path(cfg.work_dir).glob("speakwise_*")) if Path(cfg.work_dir).exists() else []


def test_full_pipeline_on_fixture(tmp_path, fixture):
    mp4, truth = fixture
    cfg = cfg_for(tmp_path)
    emb = "auto" if models.is_available("all-MiniLM-L6-v2") else None
    rep = process_session(mp4, TOPIC, MATERIAL, speaking_duration=30, config=cfg,
                          transcriber=reference_transcriber(truth), embedder=emb, nli=None)

    # contract: validates and round-trips through JSON
    again = SessionReport.model_validate_json(rep.to_json())
    assert again.session_metadata.session_id == rep.session_metadata.session_id
    saved = list((tmp_path / "out").glob("report_*.json"))
    assert len(saved) == 1 and json.loads(saved[0].read_text(encoding="utf-8"))["session_metadata"]["schema_version"]

    # preprocessing + cleanup
    assert rep.input_validation.audio_usable and rep.input_validation.video_usable
    assert leftover_workspaces(cfg) == []

    # pauses: every inserted silence is found with the right class
    events = rep.audio_analysis.pauses.events
    for p in truth["pauses"]:
        hit = [e for e in events if e.start < p["end"] and e.end > p["start"]]
        assert hit, f"inserted pause at {p['start']}s not detected"
        assert abs(hit[0].details["duration_s"] - p["duration_s"]) < 0.35
        want = "long_pause" if p["duration_s"] >= 2.0 else "short_pause"
        assert hit[0].type == want
    assert rep.audio_analysis.pauses.leading_silence_s.value == pytest.approx(0.5, abs=0.3)

    # fillers + repetition from the known transcript
    labels = rep.audio_analysis.fillers.by_type
    assert labels.get("um") == 1 and labels.get("uh") == 1 and labels.get("you know") == 1
    assert rep.audio_analysis.repetitions.accidental_word_repetitions.value == 1

    # a test pattern has no face: unavailable, never counted as poor eye contact
    va = rep.video_analysis
    assert va.status == Status.unavailable and va.camera_directed_gaze_pct.value is None
    assert any(s.id == "camera_setup" for s in rep.improvement_suggestions)
    assert not any(s.id == "gaze" for s in rep.improvement_suggestions)

    # context
    ce = rep.context_evaluation
    if emb is not None:
        assert ce.topic_relevance.value > 70
        assert any("not evaluated" in l for l in ce.limitations)  # NLI disabled in this test
    assert rep.processing_metadata.peak_rss_mb > 0 and "preprocessing" in rep.processing_metadata.timings_s


def test_corrupted_input_returns_failed_report(tmp_path):
    bad = tmp_path / "broken.mp4"
    bad.write_bytes(b"not really a video" * 100)
    rep = process_session(bad, TOPIC, MATERIAL, config=cfg_for(tmp_path), embedder=None, nli=None)
    assert rep.input_validation.status == Status.failed
    assert rep.errors and rep.errors[0].module == "preprocessing" and not rep.errors[0].recoverable
    assert rep.audio_analysis.status == Status.unavailable and rep.context_evaluation.status == Status.unavailable
    assert rep.audio_analysis.speaking_time_s.value is None


def test_asr_failure_keeps_other_results(tmp_path, fixture):
    mp4, _ = fixture

    def broken(*a):
        raise MemoryError("simulated out-of-memory while loading the speech model")

    cfg = cfg_for(tmp_path)
    rep = process_session(mp4, TOPIC, MATERIAL, config=cfg, transcriber=broken, embedder=None, nli=None)
    assert rep.transcription.status == Status.failed
    assert any(e.type == "MemoryError" and e.module == "transcription" for e in rep.errors)
    assert rep.audio_analysis.audio_quality.snr_estimate_db.value is not None  # signal metrics still measured
    assert rep.context_evaluation.status == Status.unavailable
    assert leftover_workspaces(cfg) == []


def test_interrupted_run_cleans_up(tmp_path, fixture):
    mp4, _ = fixture

    def interrupted(*a):
        raise KeyboardInterrupt

    cfg = cfg_for(tmp_path)
    with pytest.raises(KeyboardInterrupt):
        process_session(mp4, TOPIC, MATERIAL, config=cfg, transcriber=interrupted, embedder=None, nli=None)
    assert leftover_workspaces(cfg) == []


def test_modules_can_be_disabled(tmp_path, fixture):
    mp4, truth = fixture
    rep = process_session(mp4, TOPIC, MATERIAL, config={"enabled_modules": ["audio"], "work_dir": str(tmp_path / "w"),
                                                        "output_dir": str(tmp_path / "o")},
                          transcriber=reference_transcriber(truth), save=False)
    assert rep.video_analysis.status == Status.skipped and rep.context_evaluation.status == Status.skipped
    assert rep.audio_analysis.fillers.total.value == 3


@pytest.mark.slow
def test_real_asr_end_to_end(tmp_path, fixture):
    """Runs the real Whisper model chosen for this machine (minutes on CPU; skipped if it can't load)."""
    mp4, truth = fixture
    rep = process_session(mp4, TOPIC, MATERIAL, speaking_duration=30, config=cfg_for(tmp_path, allow_downloads=True))
    if rep.transcription.status == Status.failed:
        pytest.skip("speech model could not run here: " + rep.errors[0].message)
    text = rep.transcription.text.lower()
    for word in ("climate", "fossil", "carbon", "solar"):
        assert word in text
    assert rep.audio_analysis.pauses.long_pauses.value >= 1
