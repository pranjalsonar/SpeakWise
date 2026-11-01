"""Compare hosted ASR providers against what SpeakWise's speech analysis needs.

Usage:  python compare_asr.py path/to/recording.m4a

Reads GROQ_API_KEY / DEEPGRAM_API_KEY from SpeakWise/backend/.env (or the environment)
and runs every provider that has a key. For each one it reports what the POC's
speech.py depends on: word timestamps, per-word confidence, kept fillers and pauses.
Raw and normalised responses are saved to ./out for side-by-side inspection.
"""
import json
import os
import re
import sys
import time
from pathlib import Path

import requests

HERE = Path(__file__).resolve().parent
ENV_FILE = HERE.parents[1] / "backend" / ".env"
OUT_DIR = HERE / "out"

# Same disfluent prompt as the POC (speech.py) so Whisper keeps um/uh/like.
DISFLUENT_PROMPT = (
    "Umm, let me think like, hmm... Okay, here's what I'm, like, thinking. "
    "So, uh, I mean, you know, it's- it's kind of, um, like that."
)
FILLERS = {"uh", "uhh", "uhhh", "um", "umm", "ummm", "uhm", "uhmm", "erm", "er", "err",
           "ah", "ahh", "eh", "hmm", "hm", "mm", "mhm", "mmm", "mhmm", "uh-huh"}
SHORT_PAUSE, LONG_PAUSE = 0.5, 1.5


def load_env():
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8-sig").splitlines():
            m = re.match(r"\s*([A-Z_][A-Z0-9_]*)\s*=\s*(.*)\s*$", line)
            if m and m.group(1) not in os.environ:
                os.environ[m.group(1)] = m.group(2).strip().strip('"').strip("'")


def _token(raw):
    return re.sub(r"^[^\w']+|[^\w'-]+$", "", raw.lower()).strip("-")


def groq(path, key):
    with open(path, "rb") as f:
        resp = requests.post(
            "https://api.groq.com/openai/v1/audio/transcriptions",
            headers={"Authorization": f"Bearer {key}"},
            files={"file": (Path(path).name, f)},
            data=[
                ("model", "whisper-large-v3-turbo"),
                ("response_format", "verbose_json"),
                ("timestamp_granularities[]", "word"),
                ("timestamp_granularities[]", "segment"),
                ("language", "en"),
                ("temperature", "0"),
                ("prompt", DISFLUENT_PROMPT),
            ],
            timeout=300,
        )
    resp.raise_for_status()
    data = resp.json()
    words = [
        {"raw": w["word"].strip(), "word": _token(w["word"]), "start": float(w["start"]),
         "end": float(w["end"]), "prob": w.get("probability")}
        for w in data.get("words") or []
    ]
    return data, data.get("text", "").strip(), words


def deepgram(path, key):
    with open(path, "rb") as f:
        resp = requests.post(
            "https://api.deepgram.com/v1/listen",
            params={"model": "nova-3", "language": "en", "punctuate": "true",
                    "smart_format": "true", "filler_words": "true"},
            headers={"Authorization": f"Token {key}", "Content-Type": "application/octet-stream"},
            data=f,
            timeout=300,
        )
    resp.raise_for_status()
    data = resp.json()
    alt = data["results"]["channels"][0]["alternatives"][0]
    words = [
        {"raw": w.get("punctuated_word", w["word"]), "word": _token(w["word"]),
         "start": float(w["start"]), "end": float(w["end"]), "prob": w.get("confidence")}
        for w in alt.get("words", [])
    ]
    return data, alt.get("transcript", ""), words


PROVIDERS = {"groq": ("GROQ_API_KEY", groq), "deepgram": ("DEEPGRAM_API_KEY", deepgram)}


def summarise(words):
    gaps = [b["start"] - a["end"] for a, b in zip(words, words[1:])]
    probs = [w["prob"] for w in words if w["prob"] is not None]
    fillers = [w["word"] for w in words if w["word"] in FILLERS]
    return {
        "words": len(words),
        "word_timestamps": bool(words),
        "per_word_confidence": f"{len(probs)}/{len(words)}",
        "low_conf_words(<0.45)": sum(p < 0.45 for p in probs),
        "vocal_fillers": len(fillers),
        "filler_list": " ".join(fillers[:15]),
        "short_pauses(0.5-1.5s)": sum(SHORT_PAUSE <= g < LONG_PAUSE for g in gaps),
        "long_pauses(>=1.5s)": sum(g >= LONG_PAUSE for g in gaps),
    }


def main():
    if len(sys.argv) != 2 or not Path(sys.argv[1]).is_file():
        raise SystemExit("Usage: python compare_asr.py path/to/recording.(m4a|mp3|wav|webm|mp4)")
    audio = sys.argv[1]
    size_mb = Path(audio).stat().st_size / 1e6
    if size_mb > 25:
        print(f"Warning: file is {size_mb:.0f} MB; Groq's free tier caps uploads at 25 MB.")

    load_env()
    OUT_DIR.mkdir(exist_ok=True)
    results = {}
    for name, (env, fn) in PROVIDERS.items():
        key = os.environ.get(env)
        if not key:
            print(f"- {name}: skipped ({env} not set)")
            continue
        print(f"- {name}: transcribing...")
        t0 = time.time()
        try:
            raw, transcript, words = fn(audio, key)
        except requests.HTTPError as exc:
            print(f"  failed: {exc} {exc.response.text[:300]}")
            continue
        stats = {"latency_sec": round(time.time() - t0, 1), **summarise(words)}
        results[name] = stats
        (OUT_DIR / f"{name}_raw.json").write_text(json.dumps(raw, indent=2), encoding="utf-8")
        (OUT_DIR / f"{name}_words.json").write_text(
            json.dumps({"transcript": transcript, "words": words}, indent=2), encoding="utf-8")
        print(f"  transcript: {transcript[:300]}{'...' if len(transcript) > 300 else ''}")

    if not results:
        raise SystemExit(f"No provider ran. Add API keys to {ENV_FILE}")
    names = list(results)
    print("\n" + "metric".ljust(26) + "".join(n.ljust(28) for n in names))
    for metric in results[names[0]]:
        print(metric.ljust(26) + "".join(str(results[n][metric]).ljust(28) for n in names))
    print(f"\nFull responses saved in {OUT_DIR}")


if __name__ == "__main__":
    main()
