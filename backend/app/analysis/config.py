from dataclasses import dataclass
from pathlib import Path

# backend/app/analysis/config.py -> backend/
BACKEND_DIR = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class AnalysisConfig:
    """Tunable settings for the analysis pipeline. No env or DB access."""

    runs_dir: Path = BACKEND_DIR / "data" / "runs"
    audio_sample_rate: int = 16000
    frame_fps: int = 10
    frame_ext: str = "jpg"
    frame_quality: int = 3  # ffmpeg -q:v, 2 (best) .. 31 (worst)
    max_duration_s: float = 6 * 60  # sessions are 1/3/5 min; allow a little slack
    ffmpeg_bin: str = "ffmpeg"
    ffprobe_bin: str = "ffprobe"

    # --- phase 2: audio ---
    # tiny/base/small/medium. "small" is more accurate but needs ~1.5 GB free RAM;
    # "base" runs in ~500 MB (this dev machine has 8 GB total).
    whisper_model: str = "base"
    whisper_device: str = "cpu"
    whisper_compute_type: str = "int8"
    language: str | None = "en"  # None = auto-detect
    # Whisper "cleans" transcripts and drops um/uh; a verbatim-style prompt
    # nudges it to keep them. Not fully reliable (see docs / CrisperWhisper).
    asr_initial_prompt: str = (
        "Umm, let me think, like, hmm... Okay, so, uh, here's what I'm, you know, thinking."
    )
    pause_vad_threshold: float = 0.5
    pause_min_s: float = 0.3  # shorter gaps are normal articulation
    long_pause_s: float = 2.0  # at/above this a pause counts as "long"
    ambiguous_gap_s: float = 0.25  # isolation gap for words like "like"/"so"
    repetition_max_gap_s: float = 1.0

    # --- phase 3: vision ---
    # Baseline ("looking at camera, sitting straight") comes from the first
    # calibration_s seconds. The frontend should ask the user to do exactly that
    # before they start speaking. 0 = use the median of the whole clip instead.
    calibration_s: float = 3.0
    gap_fill_s: float = 0.5  # interpolate detector dropouts shorter than this
    smooth_s: float = 0.5  # median-filter window for all signals
    merge_gap_s: float = 0.5  # merge events separated by less than this

    # eye contact: gaze deviation (degrees) from the baseline
    gaze_enter_deg: float = 20.0
    gaze_exit_deg: float = 12.0  # hysteresis: must come back below this
    gaze_gain_h: float = 60.0  # degrees of gaze per unit of horizontal iris offset
    gaze_gain_v: float = 40.0  # ... vertical (heuristic, tune with the debug video)
    look_away_min_s: float = 1.0  # shorter glances are not counted
    reading_notes_min_s: float = 2.0  # sustained look-down = reading notes
    face_lost_min_s: float = 1.0

    # posture, as a fraction of the baseline neck ratio / degrees of shoulder tilt
    slouch_enter_drop: float = 0.15
    slouch_exit_drop: float = 0.08
    slouch_min_s: float = 2.0
    lean_enter_deg: float = 8.0
    lean_exit_deg: float = 5.0
    lean_min_s: float = 2.0

    # hands / movement (distances in shoulder-widths)
    face_touch_min_s: float = 0.4
    fidget_enter_speed: float = 1.5  # shoulder-widths per second, smoothed
    fidget_exit_speed: float = 1.0
    fidget_window_s: float = 1.5
    fidget_min_s: float = 2.0
    sway_window_s: float = 3.0
    sway_enter: float = 0.15
    sway_exit: float = 0.10
    sway_min_s: float = 3.0

    # --- phase 4: fusion ---
    segment_s: float = 30.0  # timeline breakdown window
    cluster_gap_s: float = 3.0  # disfluencies closer than this form one "struggle moment"
    cluster_min_events: int = 3
    min_rate_span_s: float = 10.0  # per-minute rates use at least this much speaking time


DEFAULT_CONFIG = AnalysisConfig()
