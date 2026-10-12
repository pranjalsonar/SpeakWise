"""Synthetic MP4 test fixture: known speech (text-to-speech) + exact silences + a test-pattern video.

    python scripts/generate_test_fixture.py --out outputs/fixture

Speech comes from a local TTS engine: espeak-ng on Linux/Colab (apt-get install espeak-ng),
Windows SAPI on Windows. If none is available, pass --speech-wav with a consented recording
instead; synthetic tones are never used as "speech".

Each spoken clip is trimmed of its own leading/trailing silence, so the inserted silences are
the exact pause durations written to ground_truth.json. A static/moving test pattern cannot
validate gaze or posture estimation; it only exercises the video path.
"""
from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import tempfile
import wave
from pathlib import Path
from typing import Optional

import numpy as np

RATE = 16000

# (kind, value): "say" text, or "silence" seconds. Fillers and a repetition are deliberate.
DEFAULT_SCRIPT = [
    ("say", "Today I will talk about climate change."),
    ("silence", 0.8),
    ("say", "Um, the main cause is the burning of fossil fuels like coal, oil and gas."),
    ("silence", 2.5),
    ("say", "This releases carbon dioxide, which traps heat and raises the the temperature of the planet."),
    ("silence", 0.7),
    ("say", "Uh, as a result, the ice is melting and sea levels are rising."),
    ("silence", 1.2),
    ("say", "We can reduce emissions with solar and wind power, you know, and governments must act together."),
]
EXPECTED = {"fillers": ["um", "uh", "you know"], "repetitions": ["the the"],
            "topic": "Climate change: causes, effects and what we can do"}


def _powershell() -> Optional[str]:
    found = shutil.which("powershell") or shutil.which("powershell.exe")
    if found:
        return found
    std = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32" / "WindowsPowerShell" / "v1.0" / "powershell.exe"
    return str(std) if std.is_file() else None


def available_tts() -> Optional[str]:
    if shutil.which("espeak-ng"):
        return "espeak-ng"
    if shutil.which("espeak"):
        return "espeak"
    if platform.system() == "Windows" and _powershell():
        return "sapi"
    return None


def _tts_to_wav(engine: str, text: str, out: Path, rate_wpm: int = 150) -> None:
    if engine in ("espeak-ng", "espeak"):
        subprocess.run([engine, "-s", str(rate_wpm), "-v", "en-us", "-w", str(out), text], check=True, capture_output=True)
    elif engine == "sapi":
        safe = text.replace("'", "''")
        ps = ("Add-Type -AssemblyName System.Speech; $s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
              f"$s.Rate = 0; $s.SetOutputToWaveFile('{out}'); $s.Speak('{safe}'); $s.Dispose()")
        subprocess.run([_powershell() or "powershell", "-NoProfile", "-Command", ps], check=True, capture_output=True)
    else:
        raise RuntimeError(f"Unknown TTS engine {engine}")


def _read_16k(path: Path, tmp: Path) -> np.ndarray:
    conv = tmp / (path.stem + "_16k.wav")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(path), "-ac", "1", "-ar", str(RATE), "-c:a", "pcm_s16le",
                    str(conv)], check=True)
    with wave.open(str(conv), "rb") as w:
        return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768


def _trim(x: np.ndarray, db: float = -45.0) -> np.ndarray:
    frame = int(0.01 * RATE)
    n = len(x) // frame
    if n == 0:
        return x
    rms = np.sqrt((x[: n * frame].reshape(n, frame) ** 2).mean(1))
    loud = np.where(20 * np.log10(np.maximum(rms, 1e-10)) > db)[0]
    if loud.size == 0:
        raise RuntimeError("TTS produced silence")
    return x[loud[0] * frame: (loud[-1] + 1) * frame]


def build_fixture(out_dir: str | Path, script=DEFAULT_SCRIPT, engine: Optional[str] = None,
                  speech_wav: Optional[str | Path] = None, video: str = "testsrc2") -> dict:
    """Create fixture.mp4 + ground_truth.json in out_dir; returns the ground truth dict."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="sw_fixture_"))
    try:
        if speech_wav:
            audio = _read_16k(Path(speech_wav), tmp)
            truth = {"source": "user-supplied speech", "reference_transcript": None, "speech_segments": None,
                     "pauses": None}
        else:
            engine = engine or available_tts()
            if not engine:
                raise RuntimeError("No text-to-speech engine found. Install espeak-ng (Linux: apt-get install "
                                   "espeak-ng) or pass speech_wav= with a consented recording.")
            parts, segs, pauses, t = [], [], [], 0.0
            for i, (kind, val) in enumerate(script):
                if kind == "silence":
                    n = int(round(val * RATE))
                    parts.append(np.zeros(n, np.float32))
                    pauses.append({"start": round(t, 3), "end": round(t + n / RATE, 3), "duration_s": round(n / RATE, 3)})
                    t += n / RATE
                else:
                    raw = tmp / f"say_{i}.wav"
                    _tts_to_wav(engine, val, raw)
                    clip = _trim(_read_16k(raw, tmp))
                    if len(clip) < 0.3 * RATE:
                        raise RuntimeError("TTS output too short; the engine may not be working")
                    parts.append(clip)
                    segs.append({"start": round(t, 3), "end": round(t + len(clip) / RATE, 3), "text": val})
                    t += len(clip) / RATE
            lead = np.zeros(int(0.5 * RATE), np.float32)  # recording-boundary silence (not a pause)
            audio = np.concatenate([lead] + parts + [lead])
            for s in segs + pauses:
                s["start"] = round(s["start"] + 0.5, 3)
                s["end"] = round(s["end"] + 0.5, 3)
            truth = {"source": f"synthetic TTS ({engine})", "reference_transcript": " ".join(s["text"] for s in segs),
                     "speech_segments": segs, "pauses": pauses, "expected": EXPECTED,
                     "boundary_silence_s": {"leading": 0.5, "trailing": 0.5}}
        wav = tmp / "speech.wav"
        with wave.open(str(wav), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(RATE)
            w.writeframes((np.clip(audio, -1, 1) * 32767).astype(np.int16).tobytes())
        dur = len(audio) / RATE
        mp4 = out / "fixture.mp4"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f"{video}=size=640x480:rate=25:duration={dur:.3f}",
                        "-i", str(wav), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k",
                        "-shortest", str(mp4)], check=True)
        truth.update({"mp4": mp4.name, "duration_s": round(dur, 3),
                      "video": f"{video} test pattern (cannot validate gaze/posture)",
                      "note": "Pause times are exact for the inserted silences; TTS speech is not natural speech."})
        (out / "ground_truth.json").write_text(json.dumps(truth, indent=2), encoding="utf-8")
        return truth
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
