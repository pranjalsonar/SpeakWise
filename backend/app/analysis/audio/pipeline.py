"""Phase 2 entry point: run_dir (from phase 1) -> audio_analysis.json."""
from pathlib import Path

from app.analysis.audio.asr import transcribe
from app.analysis.audio.fillers import detect_fillers, detect_repetitions
from app.analysis.audio.pauses import detect_pauses
from app.analysis.audio.prosody import analyze_prosody
from app.analysis.audio.vad import load_wav, speech_segments
from app.analysis.config import DEFAULT_CONFIG, AnalysisConfig
from app.analysis.preprocess import PreprocessResult, load_run
from app.analysis.schemas import AudioAnalysis, AudioMetrics, Event, Word

OUTPUT_FILE = "audio_analysis.json"


def build_metrics(
    words: list[Word],
    fillers: list[Event],
    repetitions: list[Event],
    pauses: list[Event],
    total_duration_s: float,
    prosody: dict,
) -> AudioMetrics:
    filler_starts = {e.start for e in fillers}
    spoken = [w for w in words if w.start not in filler_starts]
    span_start = words[0].start if words else 0.0
    span = (words[-1].end - span_start) if words else 0.0

    pause_total = sum(e.meta["duration_s"] for e in pauses)
    breakdown: dict[str, int] = {}
    for f in fillers:
        label = f.meta["label"]
        breakdown[label] = breakdown.get(label, 0) + 1

    return AudioMetrics(
        total_duration_s=round(total_duration_s, 3),
        start_delay_s=round(span_start, 3),
        speaking_span_s=round(span, 3),
        word_count=len(spoken),
        wpm=round(len(spoken) / span * 60, 1) if span > 0 else 0.0,
        filler_count=len(fillers),
        fillers_per_min=round(len(fillers) / span * 60, 2) if span > 0 else 0.0,
        filler_breakdown=dict(sorted(breakdown.items(), key=lambda kv: -kv[1])),
        repetition_count=len(repetitions),
        pause_count=len(pauses),
        long_pause_count=sum(e.type == "long_pause" for e in pauses),
        hesitation_pause_count=sum(e.meta["position"] == "hesitation" for e in pauses),
        avg_pause_s=round(pause_total / len(pauses), 2) if pauses else 0.0,
        silence_ratio=round(pause_total / span, 3) if span > 0 else 0.0,
        **prosody,
    )


def analyze_audio(
    run: str | Path | PreprocessResult,
    cfg: AnalysisConfig = DEFAULT_CONFIG,
) -> AudioAnalysis:
    if not isinstance(run, PreprocessResult):
        run = load_run(run)

    audio, rate = load_wav(run.audio_path)

    words, language, asr_model = transcribe(audio, cfg)
    segments = speech_segments(audio, rate, cfg)

    fillers = detect_fillers(words, cfg)
    repetitions = detect_repetitions(words, fillers, cfg)
    pauses = detect_pauses(words, segments, fillers, cfg)
    prosody = analyze_prosody(audio, rate, segments)

    events = sorted(fillers + repetitions + pauses, key=lambda e: (e.start, e.end))
    result = AudioAnalysis(
        run_id=run.metadata.run_id,
        language=language,
        asr_model=asr_model,
        transcript=" ".join(w.text for w in words),
        words=words,
        events=events,
        metrics=build_metrics(
            words, fillers, repetitions, pauses, run.metadata.audio_duration_s, prosody
        ),
    )
    (run.run_dir / OUTPUT_FILE).write_text(result.model_dump_json(indent=2), encoding="utf-8")
    return result
