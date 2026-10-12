"""Generate the synthetic audiovisual MP4 fixture (see speakwise/fixtures.py).

    python scripts/generate_test_fixture.py --out outputs/fixture [--engine espeak-ng|sapi] [--speech-wav my.wav]
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from speakwise.fixtures import build_fixture  # noqa: E402

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="outputs/fixture")
    ap.add_argument("--engine", default=None)
    ap.add_argument("--speech-wav", default=None, help="use a consented speech recording instead of TTS")
    a = ap.parse_args()
    truth = build_fixture(a.out, engine=a.engine, speech_wav=a.speech_wav)
    print(json.dumps({k: truth[k] for k in ("source", "duration_s", "mp4")}, indent=2))
    print("pauses:", [p["duration_s"] for p in truth.get("pauses") or []])
