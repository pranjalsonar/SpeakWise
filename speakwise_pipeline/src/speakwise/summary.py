"""Human-readable text summary of a SessionReport (for notebooks, logs and the CLI)."""
from __future__ import annotations

from speakwise.schemas import Metric, SessionReport


def _m(m: Metric | None, fmt: str = "{:.1f}") -> str:
    if m is None:
        return "-"
    if m.value is None:
        return f"n/a ({m.status.value}: {m.note or ''})".strip()
    s = fmt.format(m.value)
    return s + (" [!]" if m.status.value == "warning" else "")


def summarize(r: SessionReport) -> str:
    aa, va, ce, tr = r.audio_analysis, r.video_analysis, r.context_evaluation, r.transcription
    L = [f"Session {r.session_metadata.session_id}  |  {r.session_metadata.input_file}  |  topic: {r.session_metadata.topic}",
         f"Input: {r.input_validation.status.value}  audio usable={r.input_validation.audio_usable}  "
         f"video usable={r.input_validation.video_usable}",
         f"Transcription: {tr.status.value}  model={tr.model.get('model')} ({tr.model.get('device')}/{tr.model.get('compute_type')})  "
         f"words={_m(tr.word_count, '{:.0f}')}  mean prob={_m(tr.mean_word_probability, '{:.2f}')}",
         f"  \"{tr.text[:300]}{'...' if len(tr.text) > 300 else ''}\"",
         f"Audio: {aa.status.value}  wpm={_m(aa.words_per_minute, '{:.0f}')}  speaking={_m(aa.speaking_time_s)}s"]
    if aa.fillers:
        L.append(f"  fillers={_m(aa.fillers.total, '{:.0f}')}  per min={_m(aa.fillers.per_minute)}  "
                 f"per 100 words={_m(aa.fillers.per_100_words)}  {aa.fillers.by_type}")
    if aa.repetitions:
        L.append(f"  repetitions: accidental={_m(aa.repetitions.accidental_word_repetitions, '{:.0f}')}  "
                 f"phrase={_m(aa.repetitions.phrase_repetitions, '{:.0f}')}  emphasis={_m(aa.repetitions.possible_emphasis, '{:.0f}')}")
    if aa.pauses:
        p = aa.pauses
        L.append(f"  pauses: short={_m(p.short_pauses, '{:.0f}')}  long={_m(p.long_pauses, '{:.0f}')}  "
                 f"longest={_m(p.longest_pause_s)}s  per min={_m(p.pauses_per_minute)}")
    if aa.clarity:
        L.append(f"  unclear segments={_m(aa.clarity.unclear_segments, '{:.0f}')}")
    if aa.audio_quality:
        q = aa.audio_quality
        L.append(f"  quality: speech {_m(q.speech_rms_dbfs)} dBFS, SNR~{_m(q.snr_estimate_db)} dB, clipping {_m(q.clipping_ratio, '{:.4f}')}")
    L.append(f"Video: {va.status.value}  face visible={_m(va.face_visible_pct)}%  usable={_m(va.usable_frame_pct)}%  "
             f"head toward camera={_m(va.head_toward_camera_pct)}%  est. camera gaze={_m(va.camera_directed_gaze_pct)}%")
    L.append(f"Context: {ce.status.value}  relevance={_m(ce.topic_relevance)}  coverage(adj)={_m(ce.key_point_coverage_adjusted)}%  "
             f"alignment={_m(ce.context_alignment)} (provisional target {ce.provisional_threshold:.0f})  claims={ce.consistency_counts}")
    for s in ce.off_topic_segments[:3]:
        L.append(f"  off-topic @ {s.start:.1f}s: {(s.text or '')[:90]}")
    if r.improvement_suggestions:
        L.append("Suggestions:")
        L += [f"  - [{s.area}] {s.title}: {s.evidence[0]}" for s in r.improvement_suggestions]
    if r.errors:
        L.append("Errors:")
        L += [f"  - {e.module}/{e.stage}: {e.type}: {e.message[:150]}" for e in r.errors]
    pm = r.processing_metadata
    L.append(f"Timing: {pm.timings_s}  total={pm.total_time_s}s  peak RSS={pm.peak_rss_mb} MB  GPU mem={pm.gpu_memory_mb}")
    return "\n".join(L)
