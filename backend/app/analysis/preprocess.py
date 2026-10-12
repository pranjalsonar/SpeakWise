"""Phase 1: video -> 16 kHz mono WAV + frames @ N fps + metadata.json.

Run layout (one directory per run):

    <runs_dir>/<run_id>/
        audio.wav            16 kHz, mono, 16-bit PCM
        frames/frame_000000.jpg ...   frame i is at i / frame_fps seconds
        metadata.json        MediaMetadata

Clock alignment: both streams are shifted so their first sample/frame is at
t=0 (audio is padded with silence if it starts late), so phases 2 and 3 can
share timestamps without any offset handling.
"""
import json
import re
import shutil
import subprocess
import uuid
import wave
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.analysis.config import DEFAULT_CONFIG, AnalysisConfig
from app.analysis.schemas import MediaMetadata, PreprocessResult


class PreprocessError(Exception):
    """Raised for unreadable input, missing streams or ffmpeg failures."""


def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(cmd, capture_output=True, text=True, check=False)
    except FileNotFoundError as exc:
        raise PreprocessError(
            f"'{cmd[0]}' not found. Install FFmpeg and make sure it is on PATH."
        ) from exc


def probe(video_path: Path, cfg: AnalysisConfig = DEFAULT_CONFIG) -> dict:
    """Return ffprobe's JSON (format + streams)."""
    proc = _run(
        [cfg.ffprobe_bin, "-v", "error", "-print_format", "json",
         "-show_format", "-show_streams", str(video_path)]
    )
    if proc.returncode != 0:
        raise PreprocessError(f"ffprobe could not read the file: {proc.stderr.strip()}")
    return json.loads(proc.stdout)


def _parse_fps(rate: Optional[str]) -> Optional[float]:
    if not rate or "/" not in rate:
        return None
    num, den = rate.split("/")
    try:
        return float(num) / float(den) if float(den) else None
    except ValueError:
        return None


def _rotation(stream: dict) -> int:
    """Rotation in degrees from stream tags or display-matrix side data."""
    rot = (stream.get("tags") or {}).get("rotate")
    if rot is None:
        for sd in stream.get("side_data_list") or []:
            if "rotation" in sd:
                rot = sd["rotation"]
    try:
        return int(float(rot)) % 360 if rot is not None else 0
    except ValueError:
        return 0


def _wav_duration(wav_path: Path) -> float:
    with wave.open(str(wav_path), "rb") as w:
        return w.getnframes() / float(w.getframerate())


def preprocess_video(
    video_path: str | Path,
    run_id: Optional[str] = None,
    cfg: AnalysisConfig = DEFAULT_CONFIG,
) -> PreprocessResult:
    video_path = Path(video_path)
    if not video_path.is_file():
        raise PreprocessError(f"Input file not found: {video_path}")

    info = probe(video_path, cfg)
    streams = info.get("streams", [])
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    audio = next((s for s in streams if s.get("codec_type") == "audio"), None)
    if video is None:
        raise PreprocessError("No video stream found in the input.")
    if audio is None:
        raise PreprocessError("No audio stream found; speech analysis needs audio.")

    run_id = run_id or f"{datetime.now():%Y%m%d_%H%M%S}_{uuid.uuid4().hex[:6]}"
    if not re.fullmatch(r"[\w\-]+", run_id):
        raise PreprocessError("run_id may only contain letters, digits, '_' and '-'.")

    run_dir = cfg.runs_dir / run_id
    frames_dir = run_dir / "frames"
    audio_path = run_dir / "audio.wav"
    if run_dir.exists():
        shutil.rmtree(run_dir)
    frames_dir.mkdir(parents=True)

    try:
        # --- audio: 16 kHz mono PCM, first sample at t=0 (pad late starts) ---
        proc = _run(
            [cfg.ffmpeg_bin, "-y", "-v", "error", "-i", str(video_path),
             "-map", "0:a:0", "-vn",
             "-af", "aresample=async=1:first_pts=0",
             "-ac", "1", "-ar", str(cfg.audio_sample_rate),
             "-c:a", "pcm_s16le", str(audio_path)]
        )
        if proc.returncode != 0 or not audio_path.exists():
            raise PreprocessError(f"Audio extraction failed: {proc.stderr.strip()}")
        audio_duration = _wav_duration(audio_path)

        # Browser (MediaRecorder) WebM often has no container duration, so
        # trust the decoded audio length when ffprobe can't tell us.
        try:
            duration = float(info.get("format", {}).get("duration"))
        except (TypeError, ValueError):
            duration = audio_duration
        if duration <= 0:
            duration = audio_duration

        if duration > cfg.max_duration_s:
            raise PreprocessError(
                f"Video is {duration:.0f}s; maximum allowed is {cfg.max_duration_s:.0f}s."
            )

        # --- frames: N fps, first frame at t=0, ffmpeg auto-rotates ---
        pattern = f"frame_%06d.{cfg.frame_ext}"
        proc = _run(
            [cfg.ffmpeg_bin, "-y", "-v", "error", "-i", str(video_path),
             "-map", "0:v:0", "-an",
             "-vf", f"setpts=PTS-STARTPTS,fps={cfg.frame_fps}",
             "-q:v", str(cfg.frame_quality), "-start_number", "0",
             str(frames_dir / pattern)]
        )
        if proc.returncode != 0:
            raise PreprocessError(f"Frame extraction failed: {proc.stderr.strip()}")
        frame_count = sum(1 for _ in frames_dir.glob(f"frame_*.{cfg.frame_ext}"))
        if frame_count == 0:
            raise PreprocessError("No frames were extracted from the video.")

        width, height = int(video["width"]), int(video["height"])
        if _rotation(video) in (90, 270):
            width, height = height, width

        metadata = MediaMetadata(
            run_id=run_id,
            source_filename=video_path.name,
            duration_s=round(duration, 3),
            width=width,
            height=height,
            source_fps=_parse_fps(video.get("avg_frame_rate")),
            frame_fps=cfg.frame_fps,
            frame_count=frame_count,
            frames_pattern=f"frames/frame_{{:06d}}.{cfg.frame_ext}",
            audio_file=audio_path.name,
            audio_sample_rate=cfg.audio_sample_rate,
            audio_duration_s=round(audio_duration, 3),
        )
    except Exception:
        shutil.rmtree(run_dir, ignore_errors=True)
        raise

    metadata_path = run_dir / "metadata.json"
    metadata_path.write_text(metadata.model_dump_json(indent=2), encoding="utf-8")

    return PreprocessResult(
        run_dir=run_dir,
        audio_path=audio_path,
        frames_dir=frames_dir,
        metadata_path=metadata_path,
        metadata=metadata,
    )


def load_run(run_dir: str | Path) -> PreprocessResult:
    """Re-open a finished run (what phases 2 and 3 call with a run directory)."""
    run_dir = Path(run_dir)
    metadata_path = run_dir / "metadata.json"
    if not metadata_path.is_file():
        raise PreprocessError(f"No metadata.json in {run_dir}")
    metadata = MediaMetadata.model_validate_json(metadata_path.read_text(encoding="utf-8"))
    return PreprocessResult(
        run_dir=run_dir,
        audio_path=run_dir / metadata.audio_file,
        frames_dir=run_dir / "frames",
        metadata_path=metadata_path,
        metadata=metadata,
    )
