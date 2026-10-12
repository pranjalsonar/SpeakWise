import shutil
import subprocess

import pytest

from speakwise.config import PipelineConfig

needs_ffmpeg = pytest.mark.skipif(not shutil.which("ffmpeg"), reason="FFmpeg not installed")


def ffmpeg(*args: str) -> None:
    subprocess.run(["ffmpeg", "-y", "-v", "error", *args], check=True)


def make_av(path, seconds=4.0, audio="sine", video=True, audio_seconds=None):
    """Generate a small media file. audio: 'sine' | 'silence' | None."""
    args = []
    if video:
        args += ["-f", "lavfi", "-i", f"testsrc=duration={seconds}:size=320x240:rate=25"]
    if audio == "sine":
        args += ["-f", "lavfi", "-i", f"sine=frequency=300:duration={audio_seconds or seconds}:sample_rate=44100"]
    elif audio == "silence":
        args += ["-f", "lavfi", "-i", f"anullsrc=r=44100:cl=stereo:d={audio_seconds or seconds}"]
    if video:
        args += ["-c:v", "libx264", "-pix_fmt", "yuv420p"]
    if audio:
        args += ["-c:a", "aac"]
        if audio == "silence":
            args += ["-t", str(audio_seconds or seconds)]
    ffmpeg(*args, str(path))
    return path


@pytest.fixture
def cfg(tmp_path):
    return PipelineConfig(work_dir=tmp_path / "work", output_dir=tmp_path / "out")
