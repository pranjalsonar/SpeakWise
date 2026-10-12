"""Stage 1: validate one MP4 (audio + video), extract audio, prepare video frame sampling.

Adapted from backend/app/analysis/preprocess.py (ffprobe/ffmpeg calls, rotation and
WebM-duration handling) and extended with the validation required here: decodability,
silence, truncation, duration limits and audio/video alignment.

Design:
  * Audio is decoded once to 16 kHz mono 16-bit WAV in a temporary workspace (what
    Whisper and Silero VAD expect). Transformations are recorded in the report.
  * Video frames are NOT extracted to disk. `iter_video_frames` streams sampled frames
    through an ffmpeg pipe at the requested rate, with their timestamps.
  * Shared clock: seconds from the start of the container. Audio is padded so its
    first sample is at t=0; video sample i is at video_offset + i / fps.
"""
from __future__ import annotations

import json
import math
import shutil
import subprocess
import tempfile
import wave
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator, Optional

import numpy as np

from speakwise.config import PipelineConfig
from speakwise.schemas import (CheckResult, ErrorRecord, InputValidation, Preprocessing, Status,
                               StreamInfo)

MP4_FAMILY = ("mov", "mp4", "m4a", "3gp", "3g2", "mj2")
KNOWN_OTHER = ("matroska", "webm", "avi")


class PreprocessError(Exception):
    """Unrecoverable input problem (nothing can be analysed)."""


class Workspace:
    """Temporary directory for one session; removed on cleanup unless retention is requested."""

    def __init__(self, root: Optional[Path], keep: bool):
        if root:
            Path(root).mkdir(parents=True, exist_ok=True)
        self.path = Path(tempfile.mkdtemp(prefix="speakwise_", dir=str(root) if root else None))
        self.keep = keep

    def cleanup(self) -> None:
        if not self.keep:
            shutil.rmtree(self.path, ignore_errors=True)

    def __enter__(self) -> "Workspace":
        return self

    def __exit__(self, *exc) -> None:
        self.cleanup()


@dataclass
class PreprocessResult:
    validation: InputValidation
    preprocessing: Preprocessing
    workspace: Workspace
    source: Path
    duration_s: Optional[float] = None
    audio_path: Optional[Path] = None
    audio_duration_s: Optional[float] = None
    video: Optional[StreamInfo] = None
    video_offset_s: float = 0.0
    errors: list[ErrorRecord] = field(default_factory=list)

    @property
    def audio_usable(self) -> bool:
        return self.validation.audio_usable

    @property
    def video_usable(self) -> bool:
        return self.validation.video_usable

    def load_audio(self) -> tuple[np.ndarray, int]:
        if not self.audio_path:
            raise PreprocessError("No usable audio was extracted.")
        return load_wav(self.audio_path)


# ------------------------------------------------------------------ helpers
def _run(cmd: list[str], timeout: float = 600) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                              encoding="utf-8", errors="replace")
    except FileNotFoundError as exc:
        raise PreprocessError(f"'{cmd[0]}' not found; install FFmpeg and put it on PATH.") from exc
    except subprocess.TimeoutExpired as exc:
        raise PreprocessError(f"'{cmd[0]}' timed out after {timeout:.0f}s.") from exc


def _float(x) -> Optional[float]:
    try:
        v = float(x)
        return v if math.isfinite(v) else None
    except (TypeError, ValueError):
        return None


def _fps(rate: Optional[str]) -> Optional[float]:
    if not rate or "/" not in rate:
        return None
    num, den = rate.split("/")
    try:
        return float(num) / float(den) if float(den) else None
    except ValueError:
        return None


def _rotation(stream: dict) -> int:
    rot = (stream.get("tags") or {}).get("rotate")
    for sd in stream.get("side_data_list") or []:
        if rot is None and "rotation" in sd:
            rot = sd["rotation"]
    try:
        return int(float(rot)) % 360 if rot is not None else 0
    except (TypeError, ValueError):
        return 0


def load_wav(path: Path) -> tuple[np.ndarray, int]:
    with wave.open(str(path), "rb") as w:
        if w.getsampwidth() != 2:
            raise PreprocessError("Expected 16-bit PCM WAV.")
        rate, ch = w.getframerate(), w.getnchannels()
        data = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
    if ch > 1:
        data = data.reshape(-1, ch).mean(axis=1)
    return data, rate


def dbfs(x: np.ndarray) -> float:
    rms = float(np.sqrt(np.mean(np.square(x, dtype=np.float64)))) if x.size else 0.0
    return 20 * math.log10(rms) if rms > 1e-10 else -200.0


def probe(path: Path) -> dict:
    proc = _run(["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(path)], 120)
    if proc.returncode != 0:
        raise PreprocessError(f"ffprobe could not read the file: {proc.stderr.strip()[:300] or 'unknown error'}")
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise PreprocessError("ffprobe returned unreadable metadata.") from exc


def _stream_info(s: dict, fmt_start: float) -> StreamInfo:
    rot = _rotation(s) if s.get("codec_type") == "video" else 0
    w, h = s.get("width"), s.get("height")
    if rot in (90, 270) and w and h:
        w, h = h, w
    start = _float(s.get("start_time"))
    return StreamInfo(
        codec=s.get("codec_name"), duration_s=_float(s.get("duration")),
        start_time_s=round(start - fmt_start, 4) if start is not None else None,
        sample_rate=int(s["sample_rate"]) if s.get("sample_rate") else None,
        channels=s.get("channels"), width=w, height=h,
        frame_rate=_fps(s.get("avg_frame_rate")) or _fps(s.get("r_frame_rate")), rotation_deg=rot)


def _decodes_video_at(path: Path, t: float) -> tuple[bool, str]:
    cmd = ["ffmpeg", "-v", "error", "-xerror"]
    if t > 0:
        cmd += ["-ss", f"{t:.3f}"]
    cmd += ["-i", str(path), "-map", "0:v:0", "-frames:v", "1", "-f", "null", "-"]
    proc = _run(cmd, 120)
    return proc.returncode == 0, proc.stderr.strip()[:200]


# --------------------------------------------------------------- main entry
def preprocess_mp4(mp4_path: str | Path, config: Optional[PipelineConfig] = None,
                   speaking_duration_s: Optional[float] = None) -> PreprocessResult:
    """Validate the recording, extract audio, describe the video. Never raises for a
    partially usable file: missing/unusable streams are reported in the result.
    Raises PreprocessError only when nothing at all can be analysed."""
    cfg = config or PipelineConfig()
    src = Path(mp4_path)
    checks: list[CheckResult] = []
    warnings: list[str] = []

    def check(name: str, passed: bool, detail: str) -> bool:
        checks.append(CheckResult(name=name, passed=passed, detail=detail))
        return passed

    # ---- file
    if not src.exists():
        raise PreprocessError(f"File not found: {src.name}")
    if not src.is_file():
        raise PreprocessError(f"Not a file: {src.name}")
    try:
        with open(src, "rb") as fh:
            head = fh.read(16)
    except OSError as exc:
        raise PreprocessError(f"File is not readable: {exc.strerror}") from exc
    if not head:
        raise PreprocessError("File is empty.")
    check("file_readable", True, f"{src.stat().st_size / 1e6:.1f} MB")

    info = probe(src)
    fmt = info.get("format", {})
    fmt_names = (fmt.get("format_name") or "").split(",")
    fmt_start = _float(fmt.get("start_time")) or 0.0
    is_mp4 = any(n in MP4_FAMILY for n in fmt_names)
    if is_mp4:
        check("container", True, f"MP4/QuickTime family ({fmt.get('format_name')})")
    elif any(n in KNOWN_OTHER for n in fmt_names):
        check("container", True, f"{fmt.get('format_name')} accepted; MP4 is the expected input")
        warnings.append(f"Input is {fmt.get('format_name')}, not MP4; it was processed but MP4 is the supported input.")
    else:
        raise PreprocessError(f"Unsupported container '{fmt.get('format_name')}'. Provide an MP4 file.")

    streams = info.get("streams", [])
    a = next((s for s in streams if s.get("codec_type") == "audio"), None)
    v = next((s for s in streams if s.get("codec_type") == "video"
              and not (s.get("disposition") or {}).get("attached_pic")), None)
    has_audio = check("audio_stream_present", a is not None, a.get("codec_name", "?") if a else "no audio stream")
    has_video = check("video_stream_present", v is not None, v.get("codec_name", "?") if v else "no video stream")
    if not has_audio and not has_video:
        raise PreprocessError("The file has neither an audio nor a video stream.")

    container_dur = _float(fmt.get("duration"))
    a_info = _stream_info(a, fmt_start) if a else None
    v_info = _stream_info(v, fmt_start) if v else None
    ws = Workspace(cfg.work_dir, cfg.keep_artifacts)
    result = PreprocessResult(
        validation=InputValidation(status=Status.ok, checks=checks, has_audio=has_audio, has_video=has_video),
        preprocessing=Preprocessing(status=Status.ok, container=fmt.get("format_name"),
                                    container_duration_s=container_dur, audio_stream=a_info, video_stream=v_info),
        workspace=ws, source=src, video=v_info)

    try:
        audio_ok = _extract_audio(result, cfg, check, warnings) if has_audio else False
        video_ok = _check_video(result, cfg, check, warnings) if has_video else False
    except PreprocessError:
        ws.cleanup()
        raise

    # ---- durations
    durations = [d for d in (result.audio_duration_s, v_info.duration_s if v_info else None, container_dur) if d]
    result.duration_s = max(durations) if durations else None
    dur = result.duration_s
    if dur is None:
        check("duration_known", False, "duration could not be determined")
    else:
        ok = cfg.min_duration_s <= dur <= cfg.max_duration_s
        check("duration_in_range", ok, f"{dur:.1f}s (allowed {cfg.min_duration_s:.0f}-{cfg.max_duration_s:.0f}s)")
        if not ok:
            audio_ok = video_ok = False
            warnings.append(f"Recording length {dur:.1f}s is outside the supported {cfg.min_duration_s:.0f}-"
                            f"{cfg.max_duration_s:.0f}s range; analysis was not run.")
        if container_dur and result.audio_duration_s and \
                abs(container_dur - result.audio_duration_s) > cfg.duration_tolerance_s:
            check("duration_metadata_consistent", False,
                  f"container says {container_dur:.1f}s, decoded audio is {result.audio_duration_s:.1f}s")
            warnings.append("The duration stored in the file does not match the decoded audio; "
                            "the recording may be incomplete or its metadata wrong. Decoded length is used.")
        if speaking_duration_s and dur < 0.5 * speaking_duration_s:
            warnings.append(f"The recording ({dur:.0f}s) is much shorter than the selected speaking "
                            f"duration ({speaking_duration_s:.0f}s).")

    # ---- alignment
    align = {"clock": "seconds from container start",
             "audio_start_offset_s": a_info.start_time_s if a_info else None,
             "video_start_offset_s": v_info.start_time_s if v_info else None}
    if a_info and v_info and a_info.start_time_s is not None and v_info.start_time_s is not None:
        diff = abs(a_info.start_time_s - v_info.start_time_s)
        align["start_offset_difference_s"] = round(diff, 4)
        if diff > cfg.av_offset_warn_s:
            warnings.append(f"Audio and video start {diff:.2f}s apart; timestamps are corrected but "
                            "lip-level synchrony is not guaranteed.")
    if result.audio_duration_s and v_info and v_info.duration_s:
        align["length_difference_s"] = round(abs(result.audio_duration_s - v_info.duration_s), 3)
    result.video_offset_s = (v_info.start_time_s or 0.0) if v_info else 0.0
    result.preprocessing.alignment = align
    result.preprocessing.video_sampling = {
        "method": "ffmpeg pipe, frames sampled on demand (not stored)",
        "sample_fps": cfg.video_sample_fps, "max_width": cfg.video_max_width,
        "timestamp_rule": "t = video_start_offset + i / sample_fps"}

    result.validation.checks = checks  # pydantic copied the list at construction
    result.validation.audio_usable = audio_ok
    result.validation.video_usable = video_ok
    if not audio_ok and not video_ok:
        result.validation.status = Status.failed
    elif warnings or not (audio_ok and video_ok) or not all(c.passed for c in checks):
        result.validation.status = Status.warning
    result.validation.warnings = warnings
    result.preprocessing.status = result.validation.status if result.validation.status != Status.failed else Status.failed
    if cfg.keep_artifacts and result.audio_path:
        result.preprocessing.retained_artifacts = [str(result.audio_path)]
    return result


def _extract_audio(result: PreprocessResult, cfg: PipelineConfig, check, warnings: list[str]) -> bool:
    out = result.workspace.path / "audio_16k_mono.wav"
    proc = _run(["ffmpeg", "-y", "-v", "error", "-i", str(result.source), "-map", "0:a:0", "-vn",
                 "-af", "aresample=async=1:first_pts=0",
                 "-ac", str(cfg.audio_channels), "-ar", str(cfg.audio_sample_rate),
                 "-c:a", "pcm_s16le", str(out)])
    if proc.returncode != 0 or not out.exists() or out.stat().st_size <= 44:
        check("audio_decodable", False, proc.stderr.strip()[:200] or "no audio decoded")
        result.errors.append(ErrorRecord(module="preprocessing", stage="audio_extraction",
                                         type="DecodeError", message="Audio stream could not be decoded."))
        return False
    if proc.stderr.strip():
        warnings.append("Audio decoded with errors (possibly a damaged recording): " + proc.stderr.strip()[:150])
    check("audio_decodable", True, "decoded to 16 kHz mono PCM")

    audio, rate = load_wav(out)
    result.audio_path = out
    result.audio_duration_s = round(len(audio) / rate, 3)
    level = dbfs(audio)
    result.preprocessing.audio_signal_dbfs = round(level, 1)
    src = result.preprocessing.audio_stream
    result.preprocessing.extracted_audio = {
        "format": "WAV PCM 16-bit", "sample_rate": rate, "channels": 1, "duration_s": result.audio_duration_s,
        "transformations": [
            f"resampled from {src.sample_rate} Hz to {rate} Hz (model input rate)" if src and src.sample_rate != rate else "no resampling needed",
            f"downmixed {src.channels} channels to mono" if src and (src.channels or 1) > 1 else "already mono",
            "padded/aligned so the first sample is at t=0 of the container timeline"]}
    audible = level > cfg.silence_rms_dbfs
    check("audio_not_silent", audible, f"RMS {level:.1f} dBFS (threshold {cfg.silence_rms_dbfs:.0f})")
    if not audible:
        warnings.append("The audio is silent or too quiet to analyse; speech analysis was skipped.")
    return audible


def _check_video(result: PreprocessResult, cfg: PipelineConfig, check, warnings: list[str]) -> bool:
    ok, err = _decodes_video_at(result.source, 0)
    if not check("video_decodable_start", ok, err or "first frame decoded"):
        result.errors.append(ErrorRecord(module="preprocessing", stage="video_decode",
                                         type="DecodeError", message="Video stream could not be decoded."))
        return False
    dur = (result.video.duration_s if result.video else None) or result.preprocessing.container_duration_s
    if dur and dur > 2:
        ok_end, _ = _decodes_video_at(result.source, max(dur - 1.0, 0))
        if not check("video_decodable_end", ok_end, "last second decoded" if ok_end else "end of video not decodable"):
            warnings.append("The end of the video could not be decoded; the file may be truncated.")
    v = result.video
    if v and (not v.width or not v.height):
        check("video_resolution", False, "unknown resolution")
        return False
    return True


def iter_video_frames(path: Path, fps: float, max_width: int, offset_s: float = 0.0,
                      width: Optional[int] = None, height: Optional[int] = None) -> Iterator[tuple[float, np.ndarray]]:
    """Yield (timestamp_s, RGB uint8 frame) sampled at `fps`, scaled to at most `max_width`.
    Frames are streamed through a pipe; nothing is written to disk."""
    if not width or not height:
        info = probe(path)
        v = next(s for s in info["streams"] if s.get("codec_type") == "video")
        si = _stream_info(v, _float(info.get("format", {}).get("start_time")) or 0.0)
        width, height = si.width, si.height
    scale = min(1.0, max_width / float(width))
    w = max(2, int(round(width * scale / 2)) * 2)
    h = max(2, int(round(height * scale / 2)) * 2)
    cmd = ["ffmpeg", "-v", "error", "-i", str(path), "-map", "0:v:0", "-an",
           "-vf", f"fps={fps},scale={w}:{h}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    frame_bytes = w * h * 3
    i = 0
    try:
        assert proc.stdout is not None
        while True:
            buf = proc.stdout.read(frame_bytes)
            if len(buf) < frame_bytes:
                break
            yield offset_s + i / fps, np.frombuffer(buf, dtype=np.uint8).reshape(h, w, 3)
            i += 1
    finally:
        proc.kill()
        proc.wait()
