"""Decode phone recordings with PyAV (bundled FFmpeg, no system install needed)."""
import io
import wave

import av
import cv2
import numpy as np

SAMPLE_RATE = 16000


class MediaError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def probe(path: str) -> dict:
    """Duration and which tracks exist. Raises MediaError for unreadable files."""
    try:
        with av.open(path) as c:
            duration = c.duration / av.time_base if c.duration else None
            if duration is None and c.streams.video:
                s = c.streams.video[0]
                if s.duration and s.time_base:
                    duration = float(s.duration * s.time_base)
            return {
                "duration": duration,
                "has_audio": bool(c.streams.audio),
                "has_video": bool(c.streams.video),
            }
    except av.error.FFmpegError as exc:
        raise MediaError("invalid_file", "The recording could not be read.") from exc


def load_audio(path: str) -> np.ndarray:
    """First audio track as 16 kHz mono float32 in [-1, 1]."""
    with av.open(path) as c:
        if not c.streams.audio:
            raise MediaError("no_audio", "The recording has no sound.")
        resampler = av.AudioResampler(format="flt", layout="mono", rate=SAMPLE_RATE)
        chunks = []
        for frame in c.decode(c.streams.audio[0]):
            for out in resampler.resample(frame):
                chunks.append(out.to_ndarray().reshape(-1))
        for out in resampler.resample(None):
            chunks.append(out.to_ndarray().reshape(-1))
    if not chunks:
        raise MediaError("no_audio", "The recording has no sound.")
    return np.clip(np.concatenate(chunks).astype(np.float32), -1.0, 1.0)


def wav_bytes(audio: np.ndarray, sr: int = SAMPLE_RATE) -> bytes:
    """16-bit PCM WAV (~1.9 MB per minute)."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((audio * 32767).astype(np.int16).tobytes())
    return buf.getvalue()


def _encode(audio: np.ndarray, fmt: str, codec: str, bit_rate: int | None) -> bytes:
    buf = io.BytesIO()
    with av.open(buf, "w", format=fmt) as c:
        stream = c.add_stream(codec, rate=SAMPLE_RATE, layout="mono")
        if bit_rate:
            stream.bit_rate = bit_rate
        stream.codec_context.open()
        frame = av.AudioFrame.from_ndarray(audio.reshape(1, -1), format="flt", layout="mono")
        frame.sample_rate = SAMPLE_RATE
        resampler = av.AudioResampler(format=stream.codec_context.format, layout="mono", rate=SAMPLE_RATE,
                                      frame_size=stream.codec_context.frame_size or None)
        for f in resampler.resample(frame) + resampler.resample(None):
            for packet in stream.encode(f):
                c.mux(packet)
        for packet in stream.encode(None):
            c.mux(packet)
    return buf.getvalue()


def speech_audio_file(audio: np.ndarray) -> tuple[bytes, str, str]:
    """Small audio file for the ASR providers: Opus (~0.2 MB/min), else FLAC, else WAV.

    Uploading a compact file matters on slow connections; both Groq and Deepgram accept all three.
    """
    for fmt, codec, bit_rate, name, mime in (("ogg", "libopus", 24000, "audio.ogg", "audio/ogg"),
                                             ("flac", "flac", None, "audio.flac", "audio/flac")):
        try:
            return _encode(audio, fmt, codec, bit_rate), name, mime
        except Exception:
            continue
    return wav_bytes(audio), "audio.wav", "audio/wav"


def iter_frames(path: str, fps: float = 10.0, width: int = 640):
    """Yield (seconds, RGB frame) sampled at `fps`, resized to `width`. Rotation is NOT applied."""
    with av.open(path) as c:
        if not c.streams.video:
            return
        stream = c.streams.video[0]
        stream.thread_type = "AUTO"
        next_t = 0.0
        step = 1.0 / fps
        for frame in c.decode(stream):
            if frame.time is None or frame.time + 1e-6 < next_t:
                continue
            next_t += step
            img = frame.to_ndarray(format="rgb24")
            h, w = img.shape[:2]
            if w > width:
                img = cv2.resize(img, (width, int(h * width / w)), interpolation=cv2.INTER_AREA)
            yield float(frame.time), img


def rotate(img: np.ndarray, quarter_turns: int) -> np.ndarray:
    return np.ascontiguousarray(np.rot90(img, quarter_turns)) if quarter_turns % 4 else img
