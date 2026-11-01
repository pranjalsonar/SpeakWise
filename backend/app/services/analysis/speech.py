"""Speech analysis: fillers, pauses, repetition, mumbling, pace, voice.

Ported from the POC's speech.py. Differences:
- works on an in-memory 16 kHz signal and on merged ASR words whose `prob` may be None
  (Groq gives no per-word confidence; such words are judged on loudness only);
- pauses come from the audio signal (silent stretches), falling back to word gaps;
- the transcript is returned as segments the app can highlight, instead of HTML.
"""
import math
from collections import Counter

import librosa
import numpy as np

FILLERS = {
    "uh": "uh", "uhh": "uh", "uhhh": "uh", "uh-huh": "uh",
    "um": "um", "umm": "um", "ummm": "um", "uhm": "um", "uhmm": "um",
    "erm": "erm", "er": "erm", "err": "erm",
    "ah": "ah", "ahh": "ah", "eh": "eh",
    "hmm": "hmm", "hm": "hmm", "mm": "hmm", "mhm": "hmm", "mmm": "hmm", "mhmm": "hmm",
}
CONTEXTUAL_FILLERS = {"like", "so", "well", "actually", "basically", "literally",
                      "right", "okay", "ok", "anyway"}
FILLER_PHRASES = {"you know", "i mean", "kind of", "sort of"}

STOPWORDS = set("""
a an the and or but if then so of to in on at by for with from as is are was were be been
being am do does did have has had i you he she it we they me him her us them my your his its
our their this that these those there here what which who whom when where why how not no yes
can could will would shall should may might must just also very really too than about into
over under up down out off again more most some any all each other such only own same both
few many much now then once because while during before after above below between through
like well okay ok right uh um its it's i'm don't that's there's they're we're you're can't
get got go going gonna want say said thing things lot one two
""".split())

SHORT_PAUSE = (0.5, 1.5)   # seconds: natural breath/phrase pause
LONG_PAUSE = 1.5           # seconds and above: noticeable "dead air"
FRAME_S = 0.025


def _frame_features(audio, sr):
    hop = int(sr * FRAME_S)
    rms = librosa.feature.rms(y=audio, frame_length=hop * 2, hop_length=hop)[0]
    flat = librosa.feature.spectral_flatness(y=audio, n_fft=hop * 2, hop_length=hop)[0]
    times = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=hop)
    return times, rms, flat


def _is_contextual_filler(i, words):
    """Heuristic: is this occurrence of like/so/well/... used as a filler?"""
    w = words[i]
    token = w["word"]
    prev = words[i - 1] if i > 0 else None
    nxt = words[i + 1] if i + 1 < len(words) else None
    gap_before = w["start"] - prev["end"] if prev else 1.0
    gap_after = nxt["start"] - w["end"] if nxt else 1.0
    comma_after = w["raw"].endswith(",")
    comma_before = prev is not None and prev["raw"].endswith(",")
    sentence_start = prev is None or prev["raw"][-1:] in ".?!"

    if comma_after or comma_before or gap_before >= 0.4 or gap_after >= 0.4:
        return True
    if token == "like":
        prev_tok = prev["word"] if prev else ""
        next_tok = nxt["word"] if nxt else ""
        return (
            prev_tok in {"and", "but", "so", "um", "uh", "was", "were", "it's", "just", "is"}
            and next_tok not in {"a", "an", "the", "this", "that", "to", "how", "what",
                                 "when", "i", "you", "we", "they", "he", "she", "it"}
        )
    if token in {"so", "well", "okay", "ok", "right", "anyway", "basically", "actually"}:
        return sentence_start
    return False


def _silent_runs(times, silent, start, end, min_len):
    """(start, end) of silent stretches >= min_len seconds inside [start, end]."""
    runs, run_start = [], None
    for t, s in zip(times, silent):
        inside = start <= t <= end
        if s and inside:
            run_start = t if run_start is None else run_start
        elif run_start is not None:
            if t - run_start >= min_len:
                runs.append((run_start, t))
            run_start = None
    if run_start is not None and end - run_start >= min_len:
        runs.append((run_start, end))
    return runs


def analyze_speech(transcript: str, words: list[dict], audio: np.ndarray, sr: int) -> dict:
    duration = len(audio) / sr
    minutes = max(duration / 60.0, 1e-6)

    times, frame_rms, frame_flat = _frame_features(audio, sr)
    noise_floor = float(np.percentile(frame_rms, 10)) if len(frame_rms) else 0.0

    # ---- per-word loudness ------------------------------------------------
    def seg_rms(a, b):
        seg = audio[int(a * sr): max(int(b * sr), int(a * sr) + 1)]
        return float(np.sqrt(np.mean(seg ** 2))) if len(seg) else 0.0

    for w in words:
        w["rms"] = seg_rms(w["start"], w["end"])
    speech_rms = float(np.median([w["rms"] for w in words])) if words else 0.0
    voiced_thr = max(noise_floor * 3.0, speech_rms * 0.25)

    # ---- fillers ------------------------------------------------------------
    filler_events = []
    for i, w in enumerate(words):
        if w["word"] in FILLERS:
            filler_events.append({"word": FILLERS[w["word"]], "start": w["start"], "kind": "vocal"})
        elif w["word"] in CONTEXTUAL_FILLERS and _is_contextual_filler(i, words):
            filler_events.append({"word": w["word"], "start": w["start"], "kind": "contextual"})
    for i in range(len(words) - 1):
        phrase = f'{words[i]["word"]} {words[i + 1]["word"]}'
        if phrase in FILLER_PHRASES:
            nxt = words[i + 2] if i + 2 < len(words) else None
            punct = words[i + 1]["raw"].endswith(",") or (i > 0 and words[i - 1]["raw"].endswith(","))
            pause = nxt is None or nxt["start"] - words[i + 1]["end"] >= 0.4
            if punct or pause or phrase in {"you know", "i mean"}:
                filler_events.append({"word": phrase, "start": words[i]["start"], "kind": "contextual"})
    filler_word_idx = {i for i, w in enumerate(words) if w["word"] in FILLERS}

    # ASR still drops some "uhhh"s. Find voiced sound inside gaps between words:
    # loud enough, tonal (low spectral flatness) and >= 0.25 s long.
    hesitations = []
    for i in range(1, len(words)):
        a, b = words[i - 1]["end"], words[i]["start"]
        if b - a < 0.4:
            continue
        mask = (times >= a + 0.05) & (times <= b - 0.05)
        voiced = (frame_rms[mask] > voiced_thr) & (frame_flat[mask] < 0.1)
        run = best = 0
        for v in voiced:
            run = run + 1 if v else 0
            best = max(best, run)
        if best * FRAME_S >= 0.25:
            hesitations.append({"start": a, "end": b})
    for h in hesitations:
        filler_events.append({"word": "(uh) untranscribed", "start": h["start"], "kind": "hesitation"})
    filler_events.sort(key=lambda e: e["start"])
    filler_breakdown = Counter(e["word"] for e in filler_events)

    # ---- pauses: silent stretches in the signal, else gaps between words ------
    pauses = []
    if words and (frame_rms > voiced_thr).any():
        silent = frame_rms <= voiced_thr
        for a, b in _silent_runs(times, silent, words[0]["start"], words[-1]["end"], SHORT_PAUSE[0]):
            pauses.append({"start": round(float(a), 2), "end": round(float(b), 2), "duration": round(float(b - a), 2)})
    else:
        hes_starts = {round(h["start"], 3) for h in hesitations}
        for i in range(1, len(words)):
            a, b = words[i - 1]["end"], words[i]["start"]
            if b - a >= SHORT_PAUSE[0] and round(a, 3) not in hes_starts:
                pauses.append({"start": round(a, 2), "end": round(b, 2), "duration": round(b - a, 2)})
    for p in pauses:
        p["type"] = "long" if p["duration"] >= LONG_PAUSE else "short"
    short_pauses = [p for p in pauses if p["type"] == "short"]
    long_pauses = [p for p in pauses if p["type"] == "long"]
    opening_silence = words[0]["start"] if words else duration

    # ---- repetition -----------------------------------------------------------
    content_tokens = [w["word"] for i, w in enumerate(words) if i not in filler_word_idx]
    stutters = []
    for i in range(1, len(content_tokens)):
        if content_tokens[i] == content_tokens[i - 1] and content_tokens[i] not in {"that", "had", "very"}:
            stutters.append(content_tokens[i])
    for i in range(3, len(content_tokens)):
        if content_tokens[i - 3:i - 1] == content_tokens[i - 1:i + 1]:
            stutters.append(" ".join(content_tokens[i - 1:i + 1]))

    word_count = len(content_tokens)
    meaningful = [t for t in content_tokens if t not in STOPWORDS and len(t) > 2]
    overuse_min = max(3, math.ceil(0.02 * word_count))
    overused = [
        {"word": w, "count": c}
        for w, c in Counter(meaningful).most_common()
        if c >= overuse_min
    ][:8]
    trigrams = Counter(
        tuple(content_tokens[i:i + 3]) for i in range(len(content_tokens) - 2)
        if not all(t in STOPWORDS for t in content_tokens[i:i + 3])
    )
    repeated_phrases = [
        {"phrase": " ".join(k), "count": c} for k, c in trigrams.most_common(10) if c >= 2
    ][:5]

    # ---- mumbling / clarity -----------------------------------------------------
    mumbled = []
    for i, w in enumerate(words):
        if i in filler_word_idx:
            continue
        quiet = speech_rms > 0 and w["rms"] < 0.3 * speech_rms and (w["end"] - w["start"]) > 0.08
        unclear = w["prob"] is not None and w["prob"] < 0.45
        if unclear or quiet:
            mumbled.append({
                "word": w["word"], "start": round(w["start"], 2),
                "reason": "unclear" if unclear else "too quiet",
            })
    clarity_pct = 100.0 * (1 - len(mumbled) / word_count) if word_count else 0.0

    # ---- pace -------------------------------------------------------------------
    span = (words[-1]["end"] - words[0]["start"]) if len(words) > 1 else 0.0
    wpm = word_count / (span / 60.0) if span > 0 else 0.0
    speaking_time = sum(w["end"] - w["start"] for w in words)

    # ---- voice: loudness and pitch variety --------------------------------------
    speech_mask = frame_rms > voiced_thr
    loud_db = 20 * np.log10(frame_rms[speech_mask] + 1e-9) if speech_mask.any() else np.array([-60.0])
    try:
        f0 = librosa.yin(audio, fmin=65, fmax=400, sr=sr, frame_length=1600, hop_length=400)
        f0_rms = librosa.feature.rms(y=audio, frame_length=1600, hop_length=400)[0][: len(f0)]
        f0_flat = librosa.feature.spectral_flatness(y=audio, n_fft=1600, hop_length=400)[0][: len(f0)]
        voiced_f0 = f0[: len(f0_rms)][(f0_rms > voiced_thr) & (f0_flat < 0.1)]
        voiced_f0 = voiced_f0[(voiced_f0 > 70) & (voiced_f0 < 390)]
        if len(voiced_f0) > 20:
            semis = 12 * np.log2(voiced_f0 / np.median(voiced_f0))
            pitch_var = float(np.std(semis[np.abs(semis) < 12]))
        else:
            pitch_var = 0.0
    except Exception:
        pitch_var = 0.0

    # Transcript segments with fillers / mumbles marked, for the app to highlight.
    filler_starts = {round(e["start"], 3) for e in filler_events if e["kind"] != "hesitation"}
    mumble_starts = {m["start"] for m in mumbled}
    segments = []
    for w in words:
        kind = None
        if round(w["start"], 3) in filler_starts:
            kind = "filler"
        elif round(w["start"], 2) in mumble_starts:
            kind = "mumble"
        segments.append({"text": w["raw"], "kind": kind})

    return {
        "transcript": transcript,
        "transcript_segments": segments,
        "duration_sec": round(duration, 1),
        "word_count": word_count,
        "speaking_time_sec": round(speaking_time, 1),
        "wpm": round(wpm, 1),
        "opening_silence_sec": round(opening_silence, 1),
        "filler_count": len(filler_events),
        "filler_per_min": round(len(filler_events) / minutes, 2),
        "filler_breakdown": dict(filler_breakdown),
        "filler_events": filler_events,
        "short_pause_count": len(short_pauses),
        "long_pause_count": len(long_pauses),
        "short_pause_total_sec": round(sum(p["duration"] for p in short_pauses), 1),
        "long_pause_total_sec": round(sum(p["duration"] for p in long_pauses), 1),
        "longest_pause_sec": max((p["duration"] for p in pauses), default=0.0),
        "pauses": pauses,
        "stutter_repeats": stutters,
        "stutter_count": len(stutters),
        "overused_words": overused,
        "repeated_phrases": repeated_phrases,
        "mumbled_words": mumbled,
        "mumbled_count": len(mumbled),
        "clarity_pct": round(clarity_pct, 1),
        "loudness_dbfs": round(float(np.median(loud_db)), 1),
        "loudness_variation_db": round(float(np.std(loud_db)), 1),
        "pitch_variation_semitones": round(pitch_var, 2),
    }
