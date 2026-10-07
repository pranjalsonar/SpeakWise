"""Pydantic contracts shared by all analysis phases."""
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field


class MediaMetadata(BaseModel):
    """Output of phase 1; the input contract for phases 2 and 3.

    Paths are relative to the run directory so a run can be moved or
    archived. Use `PreprocessResult.audio_path` / `.frames_dir` for absolutes.
    """

    run_id: str
    source_filename: str
    duration_s: float
    has_audio: bool = True

    # video
    width: int
    height: int
    source_fps: Optional[float] = None
    frame_fps: int
    frame_count: int
    frames_pattern: str  # e.g. "frames/frame_{:06d}.jpg"; index i -> time i / frame_fps
    first_frame_index: int = 0

    # audio
    audio_file: str  # e.g. "audio.wav"
    audio_sample_rate: int
    audio_channels: int = 1
    audio_duration_s: float


class PreprocessResult(BaseModel):
    run_dir: Path
    audio_path: Path
    frames_dir: Path
    metadata_path: Path
    metadata: MediaMetadata


class Event(BaseModel):
    """Common timestamped event emitted by phases 2 and 3, merged in phase 4.

    `source` is "audio" or "video"; `type` is a short snake_case label such as
    "filler", "pause", "long_pause", "look_away", "slouch", "face_touch".
    Times are seconds on the shared clock (see package docstring).
    """

    type: str
    source: str
    start: float
    end: float
    confidence: float = 1.0
    meta: dict[str, Any] = Field(default_factory=dict)


class Word(BaseModel):
    """One ASR word on the shared clock. `text` keeps Whisper's punctuation."""

    text: str
    start: float
    end: float
    probability: float = 1.0


class AudioMetrics(BaseModel):
    total_duration_s: float
    start_delay_s: float  # silence before the first word (not counted as a pause)
    speaking_span_s: float  # first word start -> last word end
    word_count: int  # excludes fillers
    wpm: float
    filler_count: int
    fillers_per_min: float
    filler_breakdown: dict[str, int] = Field(default_factory=dict)
    repetition_count: int
    pause_count: int  # includes long pauses
    long_pause_count: int
    hesitation_pause_count: int  # pauses in the middle of a phrase
    avg_pause_s: float
    silence_ratio: float  # silent time inside the speaking span / span
    pitch_mean_hz: Optional[float] = None
    pitch_std_semitones: Optional[float] = None  # speaker-independent monotone measure
    intensity_std_db: Optional[float] = None


class AudioAnalysis(BaseModel):
    """Output of phase 2 (audio_analysis.json)."""

    run_id: str
    language: Optional[str] = None
    asr_model: Optional[str] = None  # may be smaller than configured (see asr.transcribe)
    transcript: str
    words: list[Word]
    events: list[Event]
    metrics: AudioMetrics


class VisionMetrics(BaseModel):
    frames: int
    face_visible_pct: float
    eye_contact_pct: Optional[float] = None  # % of visible-face time, glances < 1 s excluded
    look_away_count: int = 0
    look_away_total_s: float = 0.0
    longest_look_away_s: float = 0.0
    reading_notes_s: float = 0.0  # sustained look-down time
    face_lost_s: float = 0.0
    slouch_pct: Optional[float] = None
    slouch_count: int = 0
    lean_pct: Optional[float] = None
    sway_pct: Optional[float] = None
    hands_visible_pct: Optional[float] = None
    face_touch_count: int = 0
    fidget_pct: Optional[float] = None
    head_motion_deg_s: Optional[float] = None


class VisionAnalysis(BaseModel):
    """Output of phase 3 (vision_analysis.json)."""

    run_id: str
    baseline: dict[str, Any]
    events: list[Event]
    metrics: VisionMetrics


# ---------------- phase 4: fusion ----------------

class ScoreDriver(BaseModel):
    """One metric's contribution to a sub-score (why the score isn't 100)."""

    metric: str
    value: float
    target: str  # human-readable good range, e.g. "<= 1/min"
    points_lost: float  # on the sub-score's 0-100 scale


class SubScore(BaseModel):
    score: float  # 0-100
    drivers: list[ScoreDriver] = Field(default_factory=list)  # biggest loss first


class Scores(BaseModel):
    fluency: Optional[SubScore] = None
    delivery: Optional[SubScore] = None
    eye_contact: Optional[SubScore] = None
    posture: Optional[SubScore] = None
    composure: Optional[SubScore] = None
    overall: Optional[float] = None  # rule-based confidence score, 0-100
    weights_used: dict[str, float] = Field(default_factory=dict)
    ml_overall: Optional[float] = None  # only if a trained model file exists
    ml_model: Optional[str] = None


class Segment(BaseModel):
    start: float
    end: float
    words_per_min: Optional[float] = None
    fillers: int = 0
    repetitions: int = 0
    pauses: int = 0
    long_pauses: int = 0
    eye_contact_pct: Optional[float] = None
    look_away_s: Optional[float] = None
    slouch_s: Optional[float] = None
    fidget_s: Optional[float] = None
    face_touches: Optional[int] = None


class DisfluencyCluster(BaseModel):
    """Several disfluencies close together: where the speaker struggled."""

    start: float
    end: float
    counts: dict[str, int]  # e.g. {"um": 2, "hesitation_pause": 1}
    concurrent_video: dict[str, int] = Field(default_factory=dict)  # video events overlapping it


class SessionReport(BaseModel):
    """Output of phase 4 (session_report.json); the input to phase 5."""

    run_id: str
    duration_s: float
    transcript: Optional[str] = None
    events: list[Event]  # merged audio + video timeline, sorted by start
    audio: Optional[AudioMetrics] = None
    vision: Optional[VisionMetrics] = None
    segments: list[Segment] = Field(default_factory=list)
    clusters: list[DisfluencyCluster] = Field(default_factory=list)
    correlations: dict[str, Any] = Field(default_factory=dict)
    scores: Scores
    features: dict[str, Optional[float]] = Field(default_factory=dict)  # flat vector for ML
    warnings: list[str] = Field(default_factory=list)


# ---------------- phase 5: feedback ----------------

class Issue(BaseModel):
    """One thing to improve, ranked by how many overall-score points it costs."""

    id: str  # e.g. "filler_words", "low_eye_contact"
    title: str
    impact: float  # overall-score points lost because of this
    severity: str  # "high" | "medium" | "low"
    evidence: list[str] = Field(default_factory=list)  # facts with numbers and timestamps
    moments: list[tuple[float, float]] = Field(default_factory=list)  # for "jump to" in the UI
    advice: str = ""
    drill: Optional[str] = None
    tips: list[str] = Field(default_factory=list)  # knowledge-base ids used


class WordSuggestion(BaseModel):
    word: str
    count: int
    alternatives: list[str]


class VocabularyFeedback(BaseModel):
    lexical_diversity: Optional[float] = None  # MATTR, 0-1
    diversity_label: Optional[str] = None  # varied | moderate | repetitive
    overused: list[WordSuggestion] = Field(default_factory=list)
    filler_alternatives: list[WordSuggestion] = Field(default_factory=list)
    topic_coverage: Optional[dict[str, Any]] = None  # only when key points were supplied


class SourceRef(BaseModel):
    id: str
    title: str


class Feedback(BaseModel):
    summary: str
    strengths: list[str] = Field(default_factory=list)
    issues: list[Issue] = Field(default_factory=list)
    practice_plan: list[str] = Field(default_factory=list)
    vocabulary: VocabularyFeedback = Field(default_factory=VocabularyFeedback)
    sources: list[SourceRef] = Field(default_factory=list)
    generator: str = "template"  # or "llm:<model>"


class FinalReport(BaseModel):
    """Everything the frontend needs for one session (final_report.json)."""

    run_id: str
    topic: Optional[str] = None
    report: SessionReport
    feedback: Feedback
