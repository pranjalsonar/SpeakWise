import dataclasses
import subprocess

import pytest

from app.analysis.config import DEFAULT_CONFIG
from app.analysis.preprocess import PreprocessError, load_run, preprocess_video


@pytest.fixture
def cfg(tmp_path):
    return dataclasses.replace(DEFAULT_CONFIG, runs_dir=tmp_path / "runs")


def _make_video(path, seconds=3, with_audio=True):
    cmd = ["ffmpeg", "-y", "-v", "error",
           "-f", "lavfi", "-i", f"testsrc=duration={seconds}:size=320x240:rate=30"]
    if with_audio:
        cmd += ["-f", "lavfi", "-i", f"sine=frequency=440:duration={seconds}:sample_rate=44100"]
    cmd += ["-pix_fmt", "yuv420p", str(path)]
    subprocess.run(cmd, check=True)


def test_preprocess_produces_aligned_outputs(tmp_path, cfg):
    video = tmp_path / "in.mp4"
    _make_video(video, seconds=3)

    result = preprocess_video(video, run_id="t1", cfg=cfg)
    m = result.metadata

    assert result.audio_path.is_file() and result.metadata_path.is_file()
    assert m.audio_sample_rate == 16000
    assert abs(m.audio_duration_s - 3.0) < 0.1
    assert abs(m.frame_count - 30) <= 1  # 3 s * 10 fps
    assert (result.run_dir / m.frames_pattern.format(0)).is_file()
    assert (m.width, m.height) == (320, 240)

    reloaded = load_run(result.run_dir)
    assert reloaded.metadata == m


def test_missing_audio_is_rejected(tmp_path, cfg):
    video = tmp_path / "silent.mp4"
    _make_video(video, with_audio=False)
    with pytest.raises(PreprocessError, match="audio"):
        preprocess_video(video, run_id="t2", cfg=cfg)


def test_too_long_is_rejected_and_cleaned_up(tmp_path, cfg):
    video = tmp_path / "in.mp4"
    _make_video(video, seconds=3)
    short = dataclasses.replace(cfg, max_duration_s=1)
    with pytest.raises(PreprocessError, match="maximum"):
        preprocess_video(video, run_id="t3", cfg=short)
    assert not (short.runs_dir / "t3").exists()


def test_bad_input(tmp_path, cfg):
    bad = tmp_path / "bad.mp4"
    bad.write_bytes(b"not a video")
    with pytest.raises(PreprocessError):
        preprocess_video(bad, cfg=cfg)
    with pytest.raises(PreprocessError):
        preprocess_video(tmp_path / "nope.mp4", cfg=cfg)
