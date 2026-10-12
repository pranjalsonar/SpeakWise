import numpy as np
import pytest
from conftest import ffmpeg, make_av, needs_ffmpeg

from speakwise.media_preprocessing import (PreprocessError, iter_video_frames, load_wav,
                                           preprocess_mp4)
from speakwise.schemas import Status

pytestmark = needs_ffmpeg


def check(res, name):
    return next(c for c in res.validation.checks if c.name == name)


def test_valid_mp4_extracts_aligned_audio(tmp_path, cfg):
    src = make_av(tmp_path / "ok.mp4", seconds=4)
    res = preprocess_mp4(src, cfg)
    try:
        assert res.audio_usable and res.video_usable
        assert res.validation.status == Status.ok, res.validation.warnings
        audio, rate = res.load_audio()
        assert rate == 16000 and audio.ndim == 1
        assert abs(len(audio) / rate - 4.0) < 0.1
        assert res.preprocessing.alignment["length_difference_s"] < 0.15
        assert res.video.width == 320 and res.video.frame_rate == 25
        assert any("resampled from 44100" in t for t in res.preprocessing.extracted_audio["transformations"])
    finally:
        res.workspace.cleanup()
    assert not res.workspace.path.exists()  # cleanup removes temporary audio


def test_sampled_frame_timestamps_match_duration(tmp_path, cfg):
    src = make_av(tmp_path / "ok.mp4", seconds=4)
    frames = list(iter_video_frames(src, fps=5, max_width=160))
    assert abs(len(frames) - 20) <= 1
    ts = [t for t, _ in frames]
    assert ts[0] == 0.0 and np.allclose(np.diff(ts), 0.2)
    assert frames[0][1].shape == (120, 160, 3)
    assert ts[-1] <= 4.0  # last sampled frame lies inside the extracted audio's span


def test_missing_audio_is_reported_not_fatal(tmp_path, cfg):
    res = preprocess_mp4(make_av(tmp_path / "noaudio.mp4", audio=None), cfg)
    assert not res.validation.has_audio and not res.audio_usable and res.video_usable
    assert res.validation.status == Status.warning
    assert check(res, "audio_stream_present").passed is False
    res.workspace.cleanup()


def test_missing_video_is_reported_not_fatal(tmp_path, cfg):
    src = tmp_path / "audio_only.mp4"
    ffmpeg("-f", "lavfi", "-i", "sine=frequency=300:duration=4", "-c:a", "aac", str(src))
    res = preprocess_mp4(src, cfg)
    assert res.audio_usable and not res.validation.has_video and not res.video_usable
    res.workspace.cleanup()


def test_silent_recording_marks_audio_unusable(tmp_path, cfg):
    res = preprocess_mp4(make_av(tmp_path / "silent.mp4", audio="silence"), cfg)
    assert not res.audio_usable and res.video_usable
    assert check(res, "audio_not_silent").passed is False
    assert any("silent" in w for w in res.validation.warnings)
    res.workspace.cleanup()


def test_corrupted_file_raises(tmp_path, cfg):
    bad = tmp_path / "corrupt.mp4"
    bad.write_bytes(b"\x00\x00\x00\x18ftypmp42" + bytes(range(256)) * 20)
    with pytest.raises(PreprocessError):
        preprocess_mp4(bad, cfg)


def test_truncated_file_is_detected(tmp_path, cfg):
    full = tmp_path / "full.mp4"
    make_av(full, seconds=6)
    ffmpeg("-i", str(full), "-c", "copy", "-movflags", "+faststart", str(tmp_path / "fs.mp4"))
    data = (tmp_path / "fs.mp4").read_bytes()
    cut = tmp_path / "truncated.mp4"
    cut.write_bytes(data[: int(len(data) * 0.5)])
    try:
        res = preprocess_mp4(cut, cfg)
    except PreprocessError:
        return  # also acceptable: reported as unreadable
    failed = [c.name for c in res.validation.checks if not c.passed]
    assert failed, "a truncated file must fail at least one check"
    assert res.validation.status in (Status.warning, Status.failed)
    res.workspace.cleanup()


def test_unsupported_format_raises(tmp_path, cfg):
    img = tmp_path / "picture.png"
    ffmpeg("-f", "lavfi", "-i", "testsrc=size=64x64:duration=1", "-frames:v", "1", str(img))
    with pytest.raises(PreprocessError, match="Unsupported container"):
        preprocess_mp4(img, cfg)


def test_inconsistent_duration_metadata(tmp_path, cfg):
    # 8 s of video but only 2 s of audio: the container length disagrees with the audio
    src = make_av(tmp_path / "short_audio.mp4", seconds=8, audio_seconds=2)
    res = preprocess_mp4(src, cfg)
    assert check(res, "duration_metadata_consistent").passed is False
    assert any("does not match" in w for w in res.validation.warnings)
    res.workspace.cleanup()


def test_too_short_recording(tmp_path, cfg):
    res = preprocess_mp4(make_av(tmp_path / "tiny.mp4", seconds=1), cfg)
    assert check(res, "duration_in_range").passed is False
    assert not res.audio_usable and not res.video_usable
    assert res.validation.status == Status.failed
    res.workspace.cleanup()


@pytest.mark.parametrize("bad", ["missing.mp4", "."])
def test_unreadable_paths(tmp_path, cfg, bad):
    with pytest.raises(PreprocessError):
        preprocess_mp4(tmp_path / bad, cfg)


def test_keep_artifacts_retains_audio(tmp_path, cfg):
    cfg.keep_artifacts = True
    res = preprocess_mp4(make_av(tmp_path / "ok.mp4"), cfg)
    res.workspace.cleanup()
    assert res.audio_path.exists() and res.preprocessing.retained_artifacts
    load_wav(res.audio_path)
