"""Pipeline configuration: models, thresholds, resource limits and paths.

Every tunable number lives here with its rationale. Load overrides from a JSON file
(`PipelineConfig.from_json`) or pass a dict (`PipelineConfig.from_dict`); unknown
keys raise an error so typos don't silently fall back to defaults.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path
from typing import Any, Optional

PACKAGE_ROOT = Path(__file__).resolve().parents[2]  # speakwise_pipeline/


@dataclass
class PipelineConfig:
    # ------------------------------------------------------------------ general
    language: Optional[str] = "en"  # Whisper language code; None = auto-detect (see README: Hinglish)
    enabled_modules: tuple[str, ...] = ("audio", "video", "context")
    output_dir: Path = PACKAGE_ROOT / "outputs"
    work_dir: Optional[Path] = None  # temp root; None = system temp
    keep_artifacts: bool = False  # keep extracted audio / debug files after the run
    models_dir: Path = PACKAGE_ROOT / "models"
    allow_downloads: bool = True  # False = fail clearly instead of downloading a missing model

    # --------------------------------------------------------- preprocessing
    audio_sample_rate: int = 16000  # what Whisper and Silero VAD expect; documented as a transformation
    audio_channels: int = 1
    min_duration_s: float = 3.0
    max_duration_s: float = 15 * 60
    duration_tolerance_s: float = 2.0  # container vs decoded duration mismatch allowed
    silence_rms_dbfs: float = -55.0  # whole-recording RMS below this = silent / unusably quiet
    av_offset_warn_s: float = 0.25  # audio/video start-time or length mismatch worth a warning

    # ---------------------------------------------------------- transcription
    asr_model: str = "auto"  # auto | tiny | base | small | medium | large-v3-turbo | <path>
    asr_device: str = "auto"  # auto | cpu | cuda
    asr_compute_type: str = "auto"  # auto -> float16 on GPU, int8 on CPU
    asr_beam_size: int = 5
    asr_cpu_threads: int = 0  # 0 = library default; set 1-2 on low-RAM machines
    # Whisper tends to drop "um/uh"; a verbatim-style prompt helps partly (documented limitation).
    asr_initial_prompt: str = "Umm, let me think, like, hmm... Okay, so, uh, here's what I'm, you know, thinking."
    low_confidence_word_prob: float = 0.5  # word probability below this = uncertain recognition

    # ------------------------------------------------------------- audio metrics
    vad_threshold: float = 0.5
    short_pause_min_s: float = 0.5  # gaps < 0.5 s are normal articulation/breaths (not reported)
    long_pause_min_s: float = 2.0  # >= 2 s is a noticeable break for listeners
    pause_energy_margin_db: float = 6.0  # a "pause" this close to speech level is treated as uncertain
    contextual_filler_gap_s: float = 0.25  # isolation needed to call "like/so/well" a filler
    repetition_max_gap_s: float = 1.0
    unclear_min_words: int = 3  # consecutive low-confidence words forming an unclear segment
    untranscribed_speech_min_s: float = 1.2  # VAD speech with no words for this long = unclear
    hesitation_sound_max_s: float = 1.2  # shorter untranscribed voiced bits = possible dropped filler
    low_volume_dbfs: float = -35.0  # speech RMS below this = quiet recording
    noisy_snr_db: float = 10.0  # estimated speech-to-noise below this = noisy recording
    clipping_warn_ratio: float = 0.001

    # -------------------------------------------------------------- video
    video_sample_fps: float = 5.0  # face/gaze change slowly; 5 fps keeps CPU cost low (measured in README)
    video_max_width: int = 640
    min_face_width_ratio: float = 0.08  # smaller faces are "not usable"
    gaze_cone_deg: float = 15.0  # estimated gaze within this cone of the camera axis = camera-directed
    head_cone_deg: float = 20.0  # head orientation within this cone = facing the camera
    iris_gain_h_deg: float = 60.0  # degrees of gaze per unit of iris offset (heuristic, unvalidated)
    iris_gain_v_deg: float = 40.0
    smooth_s: float = 0.6
    min_event_s: float = 1.0  # face-not-visible / looking-away shorter than this is ignored
    dark_frame_mean: float = 50.0  # mean luminance (0-255) below this = poorly lit
    pose_enabled: bool = True
    shoulder_visibility_min: float = 0.5
    posture_drop_ratio: float = 0.15  # head-to-shoulder distance this far below the median = slumped

    # ------------------------------------------------------------- context
    embed_model: str = "all-MiniLM-L6-v2"
    nli_model: str = "nli-deberta-v3-xsmall"
    ctx_sim_floor: float = 0.12  # cosine at/below = unrelated (anchors measured on seed data; see README)
    ctx_sim_full: float = 0.50  # cosine at/above = clearly the same subject
    ctx_unit_min_words: int = 12
    ctx_unit_max_words: int = 45
    ctx_min_content_words: int = 4
    ctx_transition_max_words: int = 12  # short bridging units between on-topic units are transitions
    ctx_offtopic_relevance: float = 0.25  # unit relevance below this can be off-topic
    ctx_keypoint_cover_sim: float = 0.50  # sentence-level; tuned on seed data, not validated
    ctx_keypoint_margin: float = 0.02  # key point must be (nearly) the sentence's best match
    ctx_key_points_max: int = 10
    ctx_points_per_minute: float = 1.5  # expected key points a speaker can cover per minute
    ctx_claim_min_words: int = 6
    ctx_retrieval_k: int = 3
    ctx_retrieval_min_sim: float = 0.35  # claim must be at least this close to a passage to be checked
    ctx_entail_min: float = 0.60
    ctx_contradict_min: float = 0.70
    ctx_contradict_min_sim: float = 0.45
    ctx_min_speech_words: int = 30
    ctx_low_asr_conf: float = 0.6  # mean word probability below this = context result unreliable
    ctx_relevance_weight: float = 0.6  # composite = 0.6 relevance + 0.4 duration-adjusted coverage
    ctx_threshold: float = 70.0  # PROVISIONAL target, not validated against human ratings

    # ----------------------------------------------------------------- helpers
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PipelineConfig":
        known = {f.name for f in fields(cls)}
        unknown = set(data) - known
        if unknown:
            raise ValueError(f"Unknown config keys: {sorted(unknown)}")
        cfg = cls()
        for k, v in data.items():
            current = getattr(cfg, k)
            if v is not None and (isinstance(current, Path) or k == "work_dir"):
                v = Path(v)
            elif isinstance(current, tuple):
                v = tuple(v)
            setattr(cfg, k, v)
        cfg.validate()
        return cfg

    @classmethod
    def from_json(cls, path: str | Path) -> "PipelineConfig":
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))

    def validate(self) -> None:
        bad = set(self.enabled_modules) - {"audio", "video", "context"}
        if bad:
            raise ValueError(f"Unknown modules in enabled_modules: {sorted(bad)}")
        if not 0 < self.short_pause_min_s < self.long_pause_min_s:
            raise ValueError("Need 0 < short_pause_min_s < long_pause_min_s")
        if self.video_sample_fps <= 0:
            raise ValueError("video_sample_fps must be positive")
        if not self.ctx_sim_floor < self.ctx_sim_full:
            raise ValueError("ctx_sim_floor must be below ctx_sim_full")

    def to_dict(self) -> dict[str, Any]:
        return {k: (str(v) if isinstance(v, Path) else list(v) if isinstance(v, tuple) else v)
                for k, v in asdict(self).items()}
