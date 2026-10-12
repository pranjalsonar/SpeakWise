import json

import pytest
from pydantic import ValidationError

from speakwise.config import PipelineConfig
from speakwise.schemas import Metric, SessionReport, Status


def test_metric_distinguishes_zero_from_missing():
    zero = Metric.measured(0, "count")
    assert zero.value == 0 and zero.status == Status.ok
    missing = Metric.missing("count", "no speech")
    assert missing.value is None and missing.status == Status.unavailable
    with pytest.raises(ValidationError):
        Metric(value=None, unit="count", status=Status.ok)  # ok needs a value
    with pytest.raises(ValidationError):
        Metric(value=0, unit="count", status=Status.failed)  # failed must not carry a value


def test_schema_has_required_sections_and_forbids_unknown_fields():
    schema = SessionReport.model_json_schema()
    for section in ("session_metadata", "input_validation", "preprocessing", "transcription", "audio_analysis",
                    "video_analysis", "context_evaluation", "improvement_suggestions", "processing_metadata",
                    "warnings", "errors"):
        assert section in schema["properties"]
    with pytest.raises(ValidationError):
        Metric(value=1, unit="count", status=Status.ok, surprise=True)
    json.dumps(schema)


def test_config_rejects_typos_and_bad_values():
    with pytest.raises(ValueError, match="Unknown config keys"):
        PipelineConfig.from_dict({"long_pause_s": 3})
    with pytest.raises(ValueError):
        PipelineConfig.from_dict({"short_pause_min_s": 3, "long_pause_min_s": 2})
    cfg = PipelineConfig.from_dict({"enabled_modules": ["audio"], "video_sample_fps": 2})
    assert cfg.enabled_modules == ("audio",) and cfg.to_dict()["enabled_modules"] == ["audio"]
