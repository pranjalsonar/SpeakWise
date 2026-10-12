"""Report schema (the output contract).

Rules enforced here:
  * Every measurement is a `Metric` with a unit and a status. A valid zero has
    status ok/warning and value 0; a missing measurement has status
    unavailable/failed/skipped and value None. The validator rejects mixtures.
  * Every module section carries its own status, warnings and limitations.
  * All times are seconds from the start of the media file.

`SessionReport.model_json_schema()` exports the JSON Schema (scripts/export_schema.py).
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

SCHEMA_VERSION = "1.0.0"


class Status(str, Enum):
    ok = "ok"  # measured
    warning = "warning"  # measured, with a limitation worth reading
    unavailable = "unavailable"  # not enough evidence (e.g. no face, no speech)
    failed = "failed"  # processing error
    skipped = "skipped"  # disabled by configuration

    @property
    def has_value(self) -> bool:
        return self in (Status.ok, Status.warning)


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class Metric(_Model):
    value: Optional[float] = None
    unit: str  # count | seconds | percent | per_minute | per_100_words | words_per_minute | dbfs | db | degrees | score_0_100 | ratio
    status: Status
    denominator: Optional[str] = None  # what a rate/percentage is relative to
    note: Optional[str] = None

    @model_validator(mode="after")
    def _value_matches_status(self) -> "Metric":
        if self.status.has_value and self.value is None:
            raise ValueError(f"Metric with status '{self.status.value}' needs a value")
        if not self.status.has_value and self.value is not None:
            raise ValueError(f"Metric with status '{self.status.value}' must not carry a value")
        return self

    @classmethod
    def measured(cls, value: float, unit: str, denominator: Optional[str] = None,
                 note: Optional[str] = None, warn: bool = False) -> "Metric":
        return cls(value=round(float(value), 4), unit=unit, denominator=denominator, note=note,
                   status=Status.warning if warn else Status.ok)

    @classmethod
    def missing(cls, unit: str, reason: str, status: Status = Status.unavailable) -> "Metric":
        return cls(value=None, unit=unit, status=status, note=reason)


class Issue(_Model):
    module: str
    code: str
    message: str


class ErrorRecord(_Model):
    module: str
    stage: str
    type: str
    message: str
    recoverable: bool = True


class Section(_Model):
    status: Status
    warnings: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class TimedEvent(_Model):
    type: str
    start: float
    end: float
    text: Optional[str] = None  # transcript excerpt, when relevant
    details: dict[str, Any] = Field(default_factory=dict)


# ------------------------------------------------------------------- metadata
class SessionMetadata(_Model):
    session_id: str
    created_at: str
    schema_version: str = SCHEMA_VERSION
    pipeline_version: str
    input_file: str  # file name only (no full private path)
    topic: str
    reading_material_sha256: str
    reading_material_words: int
    speaking_duration_selected_s: Optional[float] = None


class CheckResult(_Model):
    name: str
    passed: bool
    detail: str


class InputValidation(Section):
    checks: list[CheckResult] = Field(default_factory=list)
    has_audio: bool = False
    has_video: bool = False
    audio_usable: bool = False
    video_usable: bool = False


class StreamInfo(_Model):
    codec: Optional[str] = None
    duration_s: Optional[float] = None
    start_time_s: Optional[float] = None
    sample_rate: Optional[int] = None
    channels: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    frame_rate: Optional[float] = None
    rotation_deg: int = 0


class Preprocessing(Section):
    container: Optional[str] = None
    container_duration_s: Optional[float] = None
    audio_stream: Optional[StreamInfo] = None
    video_stream: Optional[StreamInfo] = None
    extracted_audio: dict[str, Any] = Field(default_factory=dict)  # format + transformations
    video_sampling: dict[str, Any] = Field(default_factory=dict)
    alignment: dict[str, Any] = Field(default_factory=dict)
    audio_signal_dbfs: Optional[float] = None
    retained_artifacts: list[str] = Field(default_factory=list)


# --------------------------------------------------------------- transcription
class WordToken(_Model):
    text: str
    start: float
    end: float
    probability: Optional[float] = None


class TranscriptSegment(_Model):
    start: float
    end: float
    text: str
    avg_logprob: Optional[float] = None
    no_speech_prob: Optional[float] = None
    compression_ratio: Optional[float] = None


class Transcription(Section):
    model: dict[str, Any] = Field(default_factory=dict)
    language: Optional[str] = None
    language_probability: Optional[float] = None
    text: str = ""
    words: list[WordToken] = Field(default_factory=list)
    segments: list[TranscriptSegment] = Field(default_factory=list)
    word_count: Metric = Field(default_factory=lambda: Metric.missing("count", "not transcribed"))
    mean_word_probability: Metric = Field(default_factory=lambda: Metric.missing("ratio", "not transcribed"))
    low_confidence_word_pct: Metric = Field(default_factory=lambda: Metric.missing("percent", "not transcribed"))


# ---------------------------------------------------------------- audio analysis
class FillerAnalysis(Section):
    total: Metric
    per_minute: Metric
    per_100_words: Metric
    by_type: dict[str, int] = Field(default_factory=dict)
    by_kind: dict[str, int] = Field(default_factory=dict)  # non_lexical | lexical | phrase | contextual
    events: list[TimedEvent] = Field(default_factory=list)
    possible_untranscribed_hesitations: Metric
    method: str = ""


class RepetitionAnalysis(Section):
    accidental_word_repetitions: Metric
    phrase_repetitions: Metric
    possible_emphasis: Metric
    per_100_words: Metric
    events: list[TimedEvent] = Field(default_factory=list)
    method: str = ""


class PauseAnalysis(Section):
    thresholds: dict[str, float] = Field(default_factory=dict)
    short_pauses: Metric
    long_pauses: Metric
    longest_pause_s: Metric
    total_pause_s: Metric
    pauses_per_minute: Metric
    leading_silence_s: Metric
    trailing_silence_s: Metric
    uncertain_gaps: Metric  # gaps excluded because the energy suggests speech/noise
    events: list[TimedEvent] = Field(default_factory=list)
    method: str = ""


class ClarityAnalysis(Section):
    unclear_segments: Metric
    unclear_speech_s: Metric
    segments: list[TimedEvent] = Field(default_factory=list)
    method: str = ""


class AudioQuality(Section):
    peak_dbfs: Metric
    rms_dbfs: Metric
    speech_rms_dbfs: Metric
    noise_floor_dbfs: Metric
    snr_estimate_db: Metric
    clipping_ratio: Metric


class AudioAnalysis(Section):
    speaking_time_s: Metric
    speech_span_s: Metric
    words_per_minute: Metric
    fillers: Optional[FillerAnalysis] = None
    repetitions: Optional[RepetitionAnalysis] = None
    pauses: Optional[PauseAnalysis] = None
    clarity: Optional[ClarityAnalysis] = None
    audio_quality: Optional[AudioQuality] = None


# ---------------------------------------------------------------- video analysis
class VideoAnalysis(Section):
    model: dict[str, Any] = Field(default_factory=dict)
    sampling: dict[str, Any] = Field(default_factory=dict)
    frames_analyzed: Metric
    usable_frame_pct: Metric
    face_visible_pct: Metric
    face_not_visible_intervals: list[TimedEvent] = Field(default_factory=list)
    head_toward_camera_pct: Metric
    camera_directed_gaze_pct: Metric
    head_orientation: dict[str, Metric] = Field(default_factory=dict)
    looking_away_events: list[TimedEvent] = Field(default_factory=list)
    posture: dict[str, Metric] = Field(default_factory=dict)
    movement: dict[str, Metric] = Field(default_factory=dict)
    posture_events: list[TimedEvent] = Field(default_factory=list)
    lighting: dict[str, Metric] = Field(default_factory=dict)


# ------------------------------------------------------------- context evaluation
class KeyPoint(_Model):
    id: int
    text: str
    source: str  # "extracted" (from the material) or "provided"
    covered: bool
    similarity: float
    evidence_start: Optional[float] = None
    evidence_text: Optional[str] = None


class Claim(_Model):
    text: str
    start: Optional[float] = None
    end: Optional[float] = None
    label: str  # supported | potentially_inconsistent | not_addressed | unable_to_evaluate
    evidence: Optional[str] = None  # material passage used
    retrieval_similarity: Optional[float] = None
    entailment: Optional[float] = None
    contradiction: Optional[float] = None
    reason: Optional[str] = None


class SpeechUnit(_Model):
    start: Optional[float] = None
    end: Optional[float] = None
    text: str
    relevance: float  # 0-1 (rubric step 2)
    label: str  # on_topic | related | off_topic | too_short
    closest_passage: Optional[str] = None


class ContextEvaluation(Section):
    rubric_version: str
    method: dict[str, Any] = Field(default_factory=dict)
    reliability: dict[str, Any] = Field(default_factory=dict)
    topic_relevance: Metric
    key_point_coverage_raw: Metric
    key_point_coverage_adjusted: Metric
    context_alignment: Metric  # composite (documented weights); provisional
    provisional_threshold: float
    verdict: Optional[str] = None  # meets_provisional_target | below_provisional_target | None
    key_points: list[KeyPoint] = Field(default_factory=list)
    claims: list[Claim] = Field(default_factory=list)
    consistency_counts: dict[str, int] = Field(default_factory=dict)
    off_topic_segments: list[TimedEvent] = Field(default_factory=list)
    units: list[SpeechUnit] = Field(default_factory=list)


# ------------------------------------------------------------------ suggestions
class Suggestion(_Model):
    id: str
    area: str  # fluency | pauses | clarity | recording | gaze | posture | content
    title: str
    suggestion: str
    evidence: list[str]
    based_on: list[str]  # report paths of the metrics used
    moments: list[float] = Field(default_factory=list)
    certainty: str  # measured | estimate


class ProcessingMetadata(_Model):
    environment: dict[str, Any] = Field(default_factory=dict)
    config: dict[str, Any] = Field(default_factory=dict)
    models: dict[str, Any] = Field(default_factory=dict)
    timings_s: dict[str, float] = Field(default_factory=dict)
    peak_rss_mb: Optional[float] = None
    gpu_memory_mb: Optional[float] = None
    total_time_s: Optional[float] = None


class SessionReport(_Model):
    session_metadata: SessionMetadata
    input_validation: InputValidation
    preprocessing: Preprocessing
    transcription: Transcription
    audio_analysis: AudioAnalysis
    video_analysis: VideoAnalysis
    context_evaluation: ContextEvaluation
    improvement_suggestions: list[Suggestion] = Field(default_factory=list)
    processing_metadata: ProcessingMetadata
    warnings: list[Issue] = Field(default_factory=list)
    errors: list[ErrorRecord] = Field(default_factory=list)

    def to_json(self, **kw) -> str:
        return self.model_dump_json(indent=2, **kw)
