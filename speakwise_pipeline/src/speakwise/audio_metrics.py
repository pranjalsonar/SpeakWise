"""Audio analysis: fillers, repetitions, pauses, clarity and recording quality.

Adapted from backend/app/analysis/audio/{fillers,pauses,vad}.py and extended with
repetition categories, energy-checked pauses, clarity segments and quality metrics.
Inputs: 16 kHz mono float audio + the Transcription section. Pure functions; no I/O.
"""
from __future__ import annotations

import re
from bisect import bisect_right
from collections import Counter
from typing import Optional

import numpy as np

from speakwise.config import PipelineConfig
from speakwise.schemas import (AudioAnalysis, AudioQuality, ClarityAnalysis, FillerAnalysis, Metric,
                               PauseAnalysis, RepetitionAnalysis, Status, TimedEvent, Transcription,
                               WordToken)

# ---------------------------------------------------------------- lexicons
# Language-keyed so Hindi-English fillers ("matlab", "na", "yaar") can be added later.
LEXICONS = {
    "en": {
        "non_lexical": re.compile(r"^(u+h*m+|u+h+|e+r+m*|a+h+|h+m+|m{2,}|mhm|uh-huh)$"),
        "lexical": {"basically", "actually", "literally", "honestly", "obviously"},
        "phrases": [("you", "know"), ("i", "mean"), ("you", "see"), ("kind", "of"), ("sort", "of")],
        "contextual": {"like", "so", "well", "right", "okay", "ok"},
        "emphasis": {"very", "really", "so", "no", "yes", "never", "much", "too", "more", "many",
                     "please", "again", "far", "long", "bye", "ha"},
    }
}
# "kind of" / "sort of" are fillers only when set off; keep them in a separate guarded set
_GUARDED_PHRASES = {("kind", "of"), ("sort", "of")}
_EDGE = re.compile(r"^\W+|\W+$")
DB_FLOOR = -96.0  # 16-bit quantisation floor: digital silence must not produce absurd SNRs


def norm(text: str) -> str:
    return _EDGE.sub("", text.lower())


def _lex(cfg: PipelineConfig) -> dict:
    return LEXICONS.get((cfg.language or "en").split("-")[0], LEXICONS["en"])


def _set_off(words: list[WordToken], i: int, j: int, cfg: PipelineConfig) -> bool:
    """Words i..j-1 are separated from their neighbours by a comma or a pause on both sides."""
    before_comma = i > 0 and words[i - 1].text.rstrip().endswith(",")
    own_comma = words[j - 1].text.rstrip().endswith(",")
    if before_comma or own_comma:
        return True
    if 0 < i and j < len(words):
        return (words[i].start - words[i - 1].end >= cfg.contextual_filler_gap_s
                and words[j].start - words[j - 1].end >= cfg.contextual_filler_gap_s)
    return False


# ----------------------------------------------------------------- fillers
def detect_fillers(words: list[WordToken], cfg: PipelineConfig) -> list[TimedEvent]:
    lex = _lex(cfg)
    ns = [norm(w.text) for w in words]
    out: list[TimedEvent] = []
    i = 0
    while i < len(words):
        phrase = next((p for p in lex["phrases"] if tuple(ns[i:i + len(p)]) == p), None)
        if phrase and (phrase not in _GUARDED_PHRASES or _set_off(words, i, i + len(phrase), cfg)):
            span = words[i:i + len(phrase)]
            out.append(_filler(span, "phrase", " ".join(phrase), "high"))
            i += len(phrase)
            continue
        n = ns[i]
        if lex["non_lexical"].match(n):
            out.append(_filler([words[i]], "non_lexical", re.sub(r"(.)\1+", r"\1", n), "high"))
        elif n in lex["lexical"]:
            out.append(_filler([words[i]], "lexical", n, "medium"))
        elif n in lex["contextual"] and _set_off(words, i, i + 1, cfg):
            # sentence-initial "So," / "Okay," starting a new point is a discourse marker; keep it
            # but mark lower confidence
            out.append(_filler([words[i]], "contextual", n, "low"))
        i += 1
    return out


def _filler(span: list[WordToken], kind: str, label: str, confidence: str) -> TimedEvent:
    probs = [w.probability for w in span if w.probability is not None]
    return TimedEvent(type="filler", start=span[0].start, end=span[-1].end, text=" ".join(w.text for w in span),
                      details={"kind": kind, "label": label, "confidence": confidence,
                               "asr_probability": round(min(probs), 3) if probs else None})


# -------------------------------------------------------------- repetitions
def detect_repetitions(words: list[WordToken], fillers: list[TimedEvent], cfg: PipelineConfig) -> list[TimedEvent]:
    lex = _lex(cfg)
    filler_starts = {f.start for f in fillers}
    toks = [(w, norm(w.text)) for w in words if w.start not in filler_starts and norm(w.text)]
    out: list[TimedEvent] = []
    used = set()
    i = 0
    while i < len(toks):
        hit = False
        for n in (4, 3, 2):  # phrase repetitions first ("in the in the")
            a, b = toks[i:i + n], toks[i + n:i + 2 * n]
            if len(b) < n or [t for _, t in a] != [t for _, t in b]:
                continue
            if b[0][0].start - a[-1][0].end > cfg.repetition_max_gap_s or a[-1][0].text.rstrip()[-1:] in ".?!":
                continue
            out.append(TimedEvent(type="phrase_repetition", start=a[0][0].start, end=b[-1][0].end,
                                  text=" ".join(w.text for w, _ in a + b), details={"phrase": " ".join(t for _, t in a)}))
            used.update(range(i, i + 2 * n))
            i += 2 * n
            hit = True
            break
        if hit:
            continue
        if i + 1 < len(toks) and toks[i][1] == toks[i + 1][1]:
            (w1, t1), (w2, _) = toks[i], toks[i + 1]
            j = i + 1
            while j + 1 < len(toks) and toks[j + 1][1] == t1:  # "the the the" = one event
                j += 1
            gap = w2.start - w1.end
            if gap <= cfg.repetition_max_gap_s and w1.text.rstrip()[-1:] not in ".?!":
                emphasis = t1 in lex["emphasis"] or w1.text.rstrip().endswith(",")
                out.append(TimedEvent(
                    type="possible_emphasis" if emphasis else "word_repetition",
                    start=w1.start, end=toks[j][0].end, text=" ".join(w.text for w, _ in toks[i:j + 1]),
                    details={"word": t1, "times": j - i + 1,
                             "reason": "intensifier or comma-separated repeat; may be deliberate" if emphasis
                             else "immediate repeat with no punctuation; likely accidental"}))
                i = j + 1
                continue
        i += 1
    return out


# ------------------------------------------------------------------ signal
def frame_db(audio: np.ndarray, rate: int, frame_s: float = 0.03) -> tuple[np.ndarray, float]:
    n = max(1, int(rate * frame_s))
    m = len(audio) // n
    if m == 0:
        return np.array([-200.0]), frame_s
    fr = audio[: m * n].reshape(m, n).astype(np.float64)
    rms = np.sqrt((fr ** 2).mean(axis=1))
    return np.maximum(20 * np.log10(np.maximum(rms, 1e-10)), DB_FLOOR), frame_s


def interval_db(audio: np.ndarray, rate: int, start: float, end: float) -> float:
    seg = audio[int(start * rate): int(end * rate)].astype(np.float64)
    if seg.size == 0:
        return DB_FLOOR
    rms = float(np.sqrt((seg ** 2).mean()))
    return max(20 * np.log10(rms), DB_FLOOR) if rms > 1e-10 else DB_FLOOR


def vad_segments(audio: np.ndarray, rate: int, cfg: PipelineConfig) -> list[tuple[float, float]]:
    """Speech intervals from Silero VAD (bundled in faster-whisper), tuned for pause timing:
    tiny padding and 250 ms minimum silence so gaps approximate the real silences."""
    from faster_whisper.vad import VadOptions, get_speech_timestamps

    opts = VadOptions(threshold=cfg.vad_threshold, min_silence_duration_ms=250,
                      min_speech_duration_ms=100, speech_pad_ms=30)
    return [(c["start"] / rate, c["end"] / rate) for c in get_speech_timestamps(audio, opts, sampling_rate=rate)]


def audio_quality(audio: np.ndarray, rate: int, speech: list[tuple[float, float]], cfg: PipelineConfig) -> AudioQuality:
    db, fs = frame_db(audio, rate)
    t = np.arange(len(db)) * fs
    mask = np.zeros(len(db), dtype=bool)
    for s, e in speech:
        mask |= (t >= s) & (t < e)
    peak = float(np.max(np.abs(audio))) if audio.size else 0.0
    q = AudioQuality(
        status=Status.ok,
        peak_dbfs=Metric.measured(max(20 * np.log10(max(peak, 1e-10)), DB_FLOOR), "dbfs"),
        rms_dbfs=Metric.measured(interval_db(audio, rate, 0, len(audio) / rate), "dbfs"),
        clipping_ratio=Metric.measured(float((np.abs(audio) >= 0.999).mean()) if audio.size else 0.0, "ratio",
                                       denominator="all samples"),
        speech_rms_dbfs=Metric.missing("dbfs", "no speech detected"),
        noise_floor_dbfs=Metric.missing("dbfs", "no speech detected"),
        snr_estimate_db=Metric.missing("db", "no speech detected"),
        limitations=["Signal measures describe the recording, not the speaker's ability.",
                     "SNR is estimated from VAD speech vs. non-speech frames, not measured with a reference."])
    if mask.any():
        sumsq, count = 0.0, 0
        for s, e in speech:  # running sums: no copy of the speech samples
            seg = audio[int(s * rate): int(e * rate)].astype(np.float64)
            sumsq += float((seg ** 2).sum())
            count += seg.size
        speech_db = max(float(20 * np.log10(max(np.sqrt(sumsq / max(count, 1)), 1e-10))), DB_FLOOR)
        q.speech_rms_dbfs = Metric.measured(speech_db, "dbfs", denominator="VAD speech samples")
        if (~mask).sum() * fs >= 1.0:
            noise_db, note = float(np.median(db[~mask])), "median of non-speech frames"
        else:
            noise_db, note = float(np.percentile(db, 10)), "10th percentile of all frames (little non-speech audio)"
        q.noise_floor_dbfs = Metric.measured(noise_db, "dbfs", note=note)
        q.snr_estimate_db = Metric.measured(speech_db - noise_db, "db", note="estimate")
        if speech_db < cfg.low_volume_dbfs:
            q.warnings.append(f"Speech is quiet ({speech_db:.0f} dBFS); move closer to the microphone.")
        if speech_db - noise_db < cfg.noisy_snr_db:
            q.warnings.append(f"Background noise is high (estimated SNR {speech_db - noise_db:.0f} dB).")
    if q.clipping_ratio.value > cfg.clipping_warn_ratio:
        q.warnings.append("The audio clips (too loud); some words may be distorted.")
    q.status = Status.warning if q.warnings else Status.ok
    return q


# ------------------------------------------------------------------- pauses
def detect_pauses(words: list[WordToken], speech: list[tuple[float, float]], fillers: list[TimedEvent],
                  audio: np.ndarray, rate: int, speech_db: Optional[float], duration: float,
                  cfg: PipelineConfig) -> PauseAnalysis:
    span_start = min([w.start for w in words] + [s for s, _ in speech[:1]]) if (words or speech) else None
    span_end = max([w.end for w in words] + [e for _, e in speech[-1:]]) if (words or speech) else None
    thresholds = {"short_pause_min_s": cfg.short_pause_min_s, "long_pause_min_s": cfg.long_pause_min_s,
                  "energy_margin_db": cfg.pause_energy_margin_db}
    method = ("Silences between Silero-VAD speech segments inside the speech span, plus gaps between "
              "recognised words that the VAD missed. Silence before the first and after the last speech "
              "is reported separately (recording boundaries). A gap whose loudness is within "
              f"{cfg.pause_energy_margin_db:.0f} dB of the speech level is excluded as uncertain "
              "(possible quiet speech or noise).")
    if span_start is None:
        none = lambda u: Metric.missing(u, "no speech detected")  # noqa: E731
        return PauseAnalysis(status=Status.unavailable, thresholds=thresholds, method=method,
                             short_pauses=none("count"), long_pauses=none("count"), longest_pause_s=none("seconds"),
                             total_pause_s=none("seconds"), pauses_per_minute=none("per_minute"),
                             leading_silence_s=none("seconds"), trailing_silence_s=none("seconds"),
                             uncertain_gaps=none("count"), warnings=["No speech detected."])

    cands = [(pe, ns, "vad") for (_, pe), (ns, _) in zip(speech, speech[1:]) if pe >= span_start and ns <= span_end]
    for a, b in zip(words, words[1:]):
        if b.start - a.end >= cfg.short_pause_min_s and not any(s < b.start and e > a.end for s, e, _ in cands):
            cands.append((a.end, b.start, "asr"))
    cands.sort()

    ends = [w.end for w in words]
    events, uncertain = [], 0
    for s, e, src in cands:
        dur = e - s
        if dur < cfg.short_pause_min_s:
            continue
        gap_db = interval_db(audio, rate, s, e)
        if speech_db is not None and gap_db > speech_db - cfg.pause_energy_margin_db:
            uncertain += 1
            continue
        k = bisect_right(ends, s + 0.2) - 1
        prev = words[k].text.rstrip() if k >= 0 else ""
        position = ("sentence_boundary" if prev[-1:] in ".?!" else
                    "clause_boundary" if prev[-1:] in ",;:" else "mid_sentence")
        events.append(TimedEvent(
            type="long_pause" if dur >= cfg.long_pause_min_s else "short_pause", start=round(s, 3), end=round(e, 3),
            details={"duration_s": round(dur, 3), "position": position, "detected_by": src,
                     "level_dbfs": round(gap_db, 1),
                     "next_to_filler": any(f.end >= s - 0.2 and f.start <= e + 0.2 for f in fillers)}))

    span_min = (span_end - span_start) / 60
    longs = [p for p in events if p.type == "long_pause"]
    total = sum(p.details["duration_s"] for p in events)
    den = f"speech span {span_end - span_start:.1f}s (first to last speech)"
    pa = PauseAnalysis(
        status=Status.ok, thresholds=thresholds, method=method, events=events,
        short_pauses=Metric.measured(len(events) - len(longs), "count",
                                     note=f"{cfg.short_pause_min_s}s <= pause < {cfg.long_pause_min_s}s"),
        long_pauses=Metric.measured(len(longs), "count", note=f"pause >= {cfg.long_pause_min_s}s"),
        longest_pause_s=Metric.measured(max((p.details["duration_s"] for p in events), default=0.0), "seconds"),
        total_pause_s=Metric.measured(total, "seconds"),
        pauses_per_minute=Metric.measured(len(events) / span_min if span_min > 0 else 0.0, "per_minute",
                                          denominator=den),
        leading_silence_s=Metric.measured(span_start, "seconds", note="recording boundary, not a pause"),
        trailing_silence_s=Metric.measured(max(duration - span_end, 0.0), "seconds",
                                           note="recording boundary, not a pause"),
        uncertain_gaps=Metric.measured(uncertain, "count", note="excluded from pause counts"))
    if uncertain:
        pa.warnings.append(f"{uncertain} gap(s) were not counted because they were nearly as loud as speech.")
    pa.limitations.append("Thresholds follow common speech-research conventions and have not yet been "
                          "validated against manually marked SpeakWise recordings.")
    pa.status = Status.warning if pa.warnings else Status.ok
    return pa


# ------------------------------------------------------------------ clarity
def detect_clarity(words: list[WordToken], speech: list[tuple[float, float]], audio: np.ndarray, rate: int,
                   q: AudioQuality, cfg: PipelineConfig) -> tuple[ClarityAnalysis, int]:
    """Returns (clarity section, number of short untranscribed voiced bits = possible dropped fillers)."""
    speech_db = q.speech_rms_dbfs.value
    noise_db = q.noise_floor_dbfs.value
    segs: list[TimedEvent] = []

    def cause(s: float, e: float) -> tuple[str, float]:
        level = interval_db(audio, rate, s, e)
        if speech_db is not None and level < speech_db - 10:
            return "low volume", level
        if noise_db is not None and level - noise_db < cfg.noisy_snr_db:
            return "background noise likely", level
        return "recognition uncertainty (cause unknown: accent, vocabulary, articulation or noise)", level

    run: list[WordToken] = []
    for w in words + [WordToken(text="", start=1e9, end=1e9, probability=1.0)]:
        if w.probability is not None and w.probability < cfg.low_confidence_word_prob:
            run.append(w)
            continue
        if len(run) >= cfg.unclear_min_words:
            c, lvl = cause(run[0].start, run[-1].end)
            segs.append(TimedEvent(type="low_confidence_words", start=run[0].start, end=run[-1].end,
                                   text=" ".join(x.text for x in run),
                                   details={"mean_probability": round(float(np.mean([x.probability for x in run])), 3),
                                            "level_dbfs": round(lvl, 1), "likely_cause": c}))
        run = []

    hesitation_bits = 0
    for s, e in speech:
        overlap = [w for w in words if w.end > s - 0.05 and w.start < e + 0.05]
        if overlap:
            continue
        if e - s >= cfg.untranscribed_speech_min_s:
            c, lvl = cause(s, e)
            segs.append(TimedEvent(type="untranscribed_speech", start=round(s, 3), end=round(e, 3),
                                   details={"level_dbfs": round(lvl, 1), "likely_cause": c}))
        elif e - s <= cfg.hesitation_sound_max_s:
            hesitation_bits += 1

    segs.sort(key=lambda x: x.start)
    ca = ClarityAnalysis(
        status=Status.warning if segs else Status.ok, segments=segs,
        unclear_segments=Metric.measured(len(segs), "count"),
        unclear_speech_s=Metric.measured(sum(x.end - x.start for x in segs), "seconds"),
        method=(f"Runs of >= {cfg.unclear_min_words} words with recognition probability < "
                f"{cfg.low_confidence_word_prob}, and VAD speech >= {cfg.untranscribed_speech_min_s}s with no "
                "recognised words. Each segment lists a likely cause from its loudness and the noise level."),
        limitations=["This flags hard-to-recognise speech, not mumbling: accents, rare words and noise also "
                     "lower recognition confidence. It is not a validated articulation measure."])
    return ca, hesitation_bits


# --------------------------------------------------------------------- main
def analyze_audio(audio: np.ndarray, rate: int, transcription: Transcription, duration_s: float,
                  cfg: PipelineConfig, speech: Optional[list[tuple[float, float]]] = None) -> AudioAnalysis:
    speech = vad_segments(audio, rate, cfg) if speech is None else speech
    words = transcription.words
    q = audio_quality(audio, rate, speech, cfg)
    fillers = detect_fillers(words, cfg)
    reps = detect_repetitions(words, fillers, cfg)
    pauses = detect_pauses(words, speech, fillers, audio, rate, q.speech_rms_dbfs.value, duration_s, cfg)
    have_transcript = transcription.status in (Status.ok, Status.warning) or bool(words)
    if have_transcript:
        clarity, hesitation_bits = detect_clarity(words, speech, audio, rate, q, cfg)
    else:  # without a transcript every stretch of speech would look "unrecognised"
        clarity = ClarityAnalysis(status=Status.unavailable, unclear_segments=Metric.missing("count", "no transcript"),
                                  unclear_speech_s=Metric.missing("seconds", "no transcript"),
                                  warnings=["Clarity needs a transcript; none is available."])
        hesitation_bits = 0

    speaking = sum(e - s for s, e in speech)
    span = (words[-1].end - words[0].start) if words else 0.0
    filler_starts = {f.start for f in fillers}
    content_words = [w for w in words if w.start not in filler_starts]
    n_words = len(content_words)
    no_words = Metric.missing("per_minute", "no speech recognised")
    trans_warn = transcription.status == Status.warning

    # ---- fillers
    by_type = Counter(f.details["label"] for f in fillers)
    by_kind = Counter(f.details["kind"] for f in fillers)
    span_den = f"speech span {span:.1f}s (first to last recognised word)"
    fa = FillerAnalysis(
        status=Status.ok if words else Status.unavailable,
        total=Metric.measured(len(fillers), "count", warn=trans_warn) if words else Metric.missing("count", "no speech recognised"),
        per_minute=Metric.measured(len(fillers) / (span / 60), "per_minute", denominator=span_den, warn=trans_warn)
        if span > 0 else no_words,
        per_100_words=Metric.measured(len(fillers) / n_words * 100, "per_100_words",
                                      denominator=f"{n_words} words excluding fillers", warn=trans_warn)
        if n_words else Metric.missing("per_100_words", "no words recognised"),
        by_type=dict(by_type.most_common()), by_kind=dict(by_kind), events=fillers,
        possible_untranscribed_hesitations=Metric.missing("count", "no transcript") if not words else Metric.measured(
            hesitation_bits, "count", warn=True,
            note=f"short voiced sounds (<= {cfg.hesitation_sound_max_s}s) with no recognised word; may be "
                 "fillers the recogniser dropped, or noise. Not included in the filler total."),
        method=("Transcript-based: hesitation sounds (um/uh/er/hmm), filler words (basically, actually...), "
                "filler phrases (you know, I mean), and 'like/so/well/right/okay' only when set off by a comma "
                "or by pauses on both sides. Audio evidence: untranscribed short voiced sounds are reported "
                "separately."),
        limitations=["Speech recognition often omits 'um'/'uh', so totals are likely lower bounds.",
                     "Context rules for 'like'/'so' can misclassify; these detections have low confidence."])
    if by_kind.get("contextual"):
        fa.warnings.append(f"{by_kind['contextual']} filler(s) were identified from context ('like', 'so', ...) "
                           "and are uncertain.")
    if trans_warn:
        fa.warnings.append("Transcript confidence is low, so filler detection is less reliable.")
    if words:
        fa.status = Status.warning if fa.warnings else Status.ok

    # ---- repetitions
    acc = [r for r in reps if r.type == "word_repetition"]
    phr = [r for r in reps if r.type == "phrase_repetition"]
    emp = [r for r in reps if r.type == "possible_emphasis"]
    ra = RepetitionAnalysis(
        status=Status.ok if words else Status.unavailable, events=reps,
        accidental_word_repetitions=Metric.measured(len(acc), "count") if words else Metric.missing("count", "no speech"),
        phrase_repetitions=Metric.measured(len(phr), "count") if words else Metric.missing("count", "no speech"),
        possible_emphasis=Metric.measured(len(emp), "count", note="not counted as errors") if words else Metric.missing("count", "no speech"),
        per_100_words=Metric.measured((len(acc) + len(phr)) / n_words * 100, "per_100_words",
                                      denominator=f"{n_words} words excluding fillers") if n_words
        else Metric.missing("per_100_words", "no words recognised"),
        method=("Immediate repeats of a word or 2-4 word phrase within "
                f"{cfg.repetition_max_gap_s}s, with no sentence break between them. Repeated intensifiers "
                "('very very') or comma-separated repeats are reported as possible emphasis, not errors. "
                "Ordinary re-use of a word later in the talk is not counted."),
        limitations=["Deliberate repetition and stumbles can sound alike; without prosody modelling the "
                     "emphasis category is a heuristic.",
                     "Speech recognition sometimes collapses or invents repeats."])
    if trans_warn:
        ra.warnings.append("Transcript confidence is low; repetition counts are less reliable.")
        ra.status = Status.warning

    # ---- dependencies: noisy audio makes pauses uncertain
    if q.snr_estimate_db.value is not None and q.snr_estimate_db.value < cfg.noisy_snr_db and pauses.status != Status.unavailable:
        pauses.warnings.append("Background noise can hide pauses; pause counts are less reliable.")
        pauses.status = Status.warning

    aa = AudioAnalysis(
        status=Status.ok,
        speaking_time_s=Metric.measured(speaking, "seconds", note="total VAD speech"),
        speech_span_s=Metric.measured(span, "seconds") if words else Metric.missing("seconds", "no speech recognised"),
        words_per_minute=Metric.measured(n_words / (span / 60), "words_per_minute", denominator=span_den)
        if span > 0 else Metric.missing("words_per_minute", "no speech recognised"),
        fillers=fa, repetitions=ra, pauses=pauses, clarity=clarity, audio_quality=q)
    parts = [fa, ra, pauses, clarity, q]
    if not words:
        # signal-level results (pauses from VAD, recording quality) remain valid without a transcript
        signal_ok = pauses.status != Status.unavailable  # i.e. the VAD found speech
        aa.status = Status.warning if signal_ok else Status.unavailable
        aa.warnings.append("No transcript: fillers, repetitions, pace and clarity are unavailable; "
                           "pauses and recording quality are measured from the audio signal.")
    elif any(p.status in (Status.warning, Status.unavailable) for p in parts):
        aa.status = Status.warning
    return aa
