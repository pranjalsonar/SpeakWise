"""Hosted speech-to-text: Groq Whisper and Deepgram, run in parallel and merged.

Groq (whisper-large-v3-turbo) keeps filler words best, so its words and text are used.
Deepgram (nova-3) has more accurate word timings and per-word confidence, so those are
copied onto the matching Groq words. If one provider fails, the other is used alone.
"""
import difflib
import logging
import re
import time
from concurrent.futures import ThreadPoolExecutor

import requests

from app.core.config import settings

log = logging.getLogger(__name__)

# Whisper tends to "clean up" disfluencies. A prompt written in a disfluent style makes
# it far more likely to keep um/uh/like in the transcript.
DISFLUENT_PROMPT = (
    "Umm, let me think like, hmm... Okay, here's what I'm, like, thinking. "
    "So, uh, I mean, you know, it's- it's kind of, um, like that."
)
TIMEOUT = (60, 180)  # (connect/send, read) seconds; generous for slow upload links


class ASRError(Exception):
    def __init__(self, provider: str, code: str, message: str):
        super().__init__(f"{provider}: {message}")
        self.provider = provider
        self.code = code


def _token(raw: str) -> str:
    return re.sub(r"^[^\w']+|[^\w'-]+$", "", raw.lower()).strip("-")


def _post(provider: str, send) -> dict:
    """POST with one retry on rate limits (429) and server errors (5xx)."""
    for attempt in range(2):
        try:
            resp = send()
        except requests.RequestException as exc:
            if attempt == 0:
                time.sleep(1.5)
                continue
            raise ASRError(provider, "network", str(exc)) from exc
        if resp.status_code == 429 or resp.status_code >= 500:
            if attempt == 0:
                wait = min(float(resp.headers.get("retry-after", 2) or 2), 8.0)
                time.sleep(wait)
                continue
            code = "rate_limited" if resp.status_code == 429 else "provider_error"
            raise ASRError(provider, code, f"HTTP {resp.status_code}")
        if resp.status_code in (401, 403):
            raise ASRError(provider, "auth", "API key rejected")
        if not resp.ok:
            raise ASRError(provider, "provider_error", f"HTTP {resp.status_code}: {resp.text[:200]}")
        return resp.json()
    raise ASRError(provider, "provider_error", "no response")


def groq_transcribe(audio: tuple[bytes, str, str]) -> tuple[str, list[dict]]:
    if not settings.GROQ_API_KEY:
        raise ASRError("groq", "not_configured", "GROQ_API_KEY missing")
    data = _post("groq", lambda: requests.post(
        "https://api.groq.com/openai/v1/audio/transcriptions",
        headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}"},
        files={"file": (audio[1], audio[0], audio[2])},
        data=[
            ("model", settings.GROQ_ASR_MODEL),
            ("response_format", "verbose_json"),
            ("timestamp_granularities[]", "word"),
            ("timestamp_granularities[]", "segment"),
            ("language", "en"),
            ("temperature", "0"),
            ("prompt", DISFLUENT_PROMPT),
        ],
        timeout=TIMEOUT,
    ))
    words = []
    for w in data.get("words") or []:
        token = _token(w["word"])
        if token:
            words.append({"raw": w["word"].strip(), "word": token, "start": float(w["start"]),
                          "end": float(w["end"]), "prob": None})
    return (data.get("text") or "").strip(), words


def deepgram_transcribe(audio: tuple[bytes, str, str]) -> tuple[str, list[dict]]:
    if not settings.DEEPGRAM_API_KEY:
        raise ASRError("deepgram", "not_configured", "DEEPGRAM_API_KEY missing")
    data = _post("deepgram", lambda: requests.post(
        "https://api.deepgram.com/v1/listen",
        params={"model": settings.DEEPGRAM_MODEL, "language": "en", "punctuate": "true",
                "smart_format": "true", "filler_words": "true"},
        headers={"Authorization": f"Token {settings.DEEPGRAM_API_KEY}", "Content-Type": audio[2]},
        data=audio[0],
        timeout=TIMEOUT,
    ))
    alt = data["results"]["channels"][0]["alternatives"][0]
    words = []
    for w in alt.get("words", []):
        token = _token(w["word"])
        if token:
            words.append({"raw": w.get("punctuated_word", w["word"]), "word": token,
                          "start": float(w["start"]), "end": float(w["end"]),
                          "prob": float(w.get("confidence", 0.0))})
    return alt.get("transcript", ""), words


def merge_words(groq_words: list[dict], dg_words: list[dict]) -> list[dict]:
    """Groq words with Deepgram timings/confidence wherever the two transcripts agree."""
    out = [dict(w) for w in groq_words]
    sm = difflib.SequenceMatcher(a=[w["word"] for w in groq_words],
                                 b=[w["word"] for w in dg_words], autojunk=False)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        # "replace" blocks of equal length are usually spelling differences (ok/okay, 2/two).
        if tag == "equal" or (tag == "replace" and i2 - i1 == j2 - j1):
            for k in range(i2 - i1):
                d = dg_words[j1 + k]
                out[i1 + k].update(start=d["start"], end=d["end"], prob=d["prob"], timed_by="deepgram")
    # Groq-only words (mostly fillers) keep Groq timings; clamp them between their neighbours.
    for i, w in enumerate(out):
        if w.get("timed_by") == "deepgram":
            continue
        prev_end = out[i - 1]["end"] if i else 0.0
        nxt = next((x for x in out[i + 1:] if x.get("timed_by") == "deepgram"), None)
        start = max(w["start"], prev_end)
        end = max(w["end"], start + 0.05)
        if nxt and end > nxt["start"]:
            end = max(start + 0.05, nxt["start"] - 0.01)
        w.update(start=start, end=end)
    return out


def transcribe(audio: tuple[bytes, str, str]) -> dict:
    """Run both providers in parallel on (file bytes, filename, mime).

    Returns transcript, words and which providers succeeded.
    """
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = {"groq": pool.submit(groq_transcribe, audio), "deepgram": pool.submit(deepgram_transcribe, audio)}
        results, errors = {}, {}
        for name, fut in futures.items():
            try:
                results[name] = fut.result()
            except ASRError as exc:
                log.warning("ASR provider failed: %s", exc)
                errors[name] = exc.code
            except Exception as exc:  # unexpected payload shapes etc.
                log.exception("ASR provider crashed: %s", name)
                errors[name] = "provider_error"

    if "groq" in results and "deepgram" in results:
        text, gw = results["groq"]
        _, dw = results["deepgram"]
        words = merge_words(gw, dw) if dw else gw
        providers = ["groq", "deepgram"]
    elif "groq" in results:
        text, words = results["groq"]
        providers = ["groq"]
    elif "deepgram" in results:
        text, words = results["deepgram"]
        providers = ["deepgram"]
    else:
        code = "rate_limited" if "rate_limited" in errors.values() else "asr_unavailable"
        raise ASRError("all", code, f"All speech-to-text providers failed: {errors}")
    return {"transcript": text, "words": words, "providers": providers, "errors": errors}
