"""Phase 5 tests: retrieval, issues, vocabulary, generator (template + mocked LLM), mapping."""
import json

import pytest

from app.analysis.feedback import issues as issues_mod
from app.analysis.feedback import llm as llm_mod
from app.analysis.feedback.generator import generate_feedback
from app.analysis.feedback.llm import LLMClient, LLMError, extract_json
from app.analysis.feedback.retriever import default_retriever
from app.analysis.feedback.vocabulary import analyze_vocabulary, mattr, topic_coverage
from app.analysis.fusion.pipeline import build_report
from app.analysis.persistence import to_db_payload
from app.analysis.schemas import (AudioAnalysis, AudioMetrics, Event, FinalReport,
                                  VisionAnalysis, VisionMetrics)


def _audio(events, **kw):
    m = dict(total_duration_s=60, start_delay_s=1, speaking_span_s=55, word_count=140, wpm=150,
             filler_count=2, fillers_per_min=2.2, filler_breakdown={"um": 2}, repetition_count=0,
             pause_count=8, long_pause_count=0, hesitation_pause_count=1, avg_pause_s=0.6,
             silence_ratio=0.1, pitch_mean_hz=120, pitch_std_semitones=3.5, intensity_std_db=6)
    m.update(kw)
    return AudioAnalysis(run_id="t", transcript="the climate is changing and the climate matters",
                         words=[], events=events, metrics=AudioMetrics(**m), asr_model="small")


def _vision(events, **kw):
    m = dict(frames=600, face_visible_pct=100, eye_contact_pct=80, look_away_count=3,
             look_away_total_s=8, longest_look_away_s=4, reading_notes_s=0, face_lost_s=0,
             slouch_pct=2, slouch_count=0, lean_pct=1, sway_pct=0, hands_visible_pct=50,
             face_touch_count=0, fidget_pct=2, head_motion_deg_s=10)
    m.update(kw)
    return VisionAnalysis(run_id="t", baseline={"source": "calibration"}, events=events,
                          metrics=VisionMetrics(**m))


def _ev(type_, start, end, source="audio", **meta):
    return Event(type=type_, source=source, start=start, end=end, meta=meta)


def struggling_report():
    a_events = [_ev("filler", 12, 12.3, label="um", kind="non_lexical"),
                _ev("filler", 40, 40.3, label="um", kind="non_lexical"),
                _ev("long_pause", 65, 69, duration_s=4, position="hesitation", filled=False)]
    v_events = [_ev("look_away", 30, 36, "video", direction="down", reading_notes=True),
                _ev("slouch", 50, 70, "video")]
    return build_report(
        "s", 90,
        _audio(a_events, filler_count=14, fillers_per_min=15, long_pause_count=1,
               hesitation_pause_count=6, filler_breakdown={"um": 8, "like": 6}),
        _vision(v_events, eye_contact_pct=35, reading_notes_s=6, slouch_pct=30, slouch_count=1))


# ---------------------------------------------------------------- retrieval

def test_every_issue_has_a_primary_tip():
    r = default_retriever()
    for issue_id in issues_mod.TITLES:
        top = r.search("anything", k=1, issue=issue_id)
        assert top and issue_id in top[0]["primary_for"], issue_id


def test_search_filters_by_issue_and_ranks_by_relevance():
    r = default_retriever()
    hits = r.search("pause breath silent fillers", k=3, issue="filler_words")
    assert hits[0]["id"] == "fill_pause"  # curated primary comes first
    assert all("filler_words" in h["issues"] for h in hits)
    assert r.search("make hands gesture", k=1)[0]["id"] == "hands_gesture"  # free text, no filter
    assert r.search("zzz", k=2, issue="no_such_issue")  # unknown issue falls back to all tips


# ------------------------------------------------------------------- issues

def test_issues_ranked_by_impact_with_timestamps():
    report = struggling_report()
    found = issues_mod.detect_issues(report)
    ids = [i.id for i in found]
    assert ids[0] in ("filler_words", "low_eye_contact") and "reading_notes" in ids
    assert [i.impact for i in found] == sorted((i.impact for i in found), reverse=True)
    fill = next(i for i in found if i.id == "filler_words")
    assert any("0:12" in e for e in fill.evidence) and fill.moments[0] == (12.0, 12.3)
    eye = next(i for i in found if i.id == "low_eye_contact")
    assert "35" in eye.evidence[0] and eye.moments == [(30.0, 36.0)]
    assert issues_mod.plural(1, "pause") == "1 pause" and issues_mod.plural(2, "pause") == "2 pauses"


def test_strengths_for_a_good_session():
    clean = _audio([], filler_count=0, filler_breakdown={}, hesitation_pause_count=0)
    report = build_report("g", 60, clean, _vision([]))
    assert issues_mod.detect_issues(report) == []
    assert len(issues_mod.detect_strengths(report)) >= 3


# --------------------------------------------------------------- vocabulary

def test_vocabulary_analysis():
    text = " ".join(["good"] * 5 + ["thing"] * 4 + ["speech", "audience", "topic", "idea"] * 3)
    v = analyze_vocabulary(text, {"um": 3, "like": 2, "zzz": 1})
    assert [w.word for w in v.overused[:2]] == ["good", "thing"]
    assert "effective" in v.overused[0].alternatives
    assert [f.word for f in v.filler_alternatives] == ["um", "like"]  # unknown filler skipped
    assert mattr(["a"] * 30) == pytest.approx(1 / 30, abs=0.001)
    assert mattr(["a", "b"]) is None  # too short to judge


def test_topic_coverage():
    cov = topic_coverage("we use solar panels for renewable energy",
                         ["renewable energy sources", "carbon taxes and policy"])
    assert cov["covered"] == ["renewable energy sources"] and cov["pct"] == 50.0


# ------------------------------------------------------------------ generator

def test_template_feedback_is_grounded_and_offline():
    fb = generate_feedback(struggling_report(), topic="Climate")
    assert fb.generator == "template"
    assert "/100" in fb.summary and fb.issues[0].title.lower() in fb.summary.lower()
    assert all(i.advice and i.tips for i in fb.issues)
    assert {s.id for s in fb.sources} >= {t for i in fb.issues for t in i.tips}
    assert fb.practice_plan and len(fb.practice_plan) <= 3


GOOD_REPLY = json.dumps({
    "summary": "Nice effort! You scored low on fluency mainly because of filler words, so let's fix that.",
    "strengths": ["You kept going."],
    "issue_advice": {"filler_words": "Swap each 'um' for a breath."},
    "practice_plan": ["Halve your fillers."]})


class FakeLLM(LLMClient):
    def __init__(self, reply):
        super().__init__("openai", "k", "test-model")
        self.reply, self.calls = reply, []

    def complete(self, system, user):
        self.calls.append((system, user))
        if isinstance(self.reply, Exception):
            raise self.reply
        return self.reply


def test_llm_rewords_text_but_never_changes_facts():
    report = struggling_report()
    plain = generate_feedback(report)
    llm = FakeLLM(GOOD_REPLY)
    fb = generate_feedback(report, llm=llm)

    assert fb.generator == "llm:test-model"
    assert fb.summary.startswith("Nice effort") and fb.practice_plan == ["Halve your fillers."]
    fill = next(i for i in fb.issues if i.id == "filler_words")
    assert fill.advice == "Swap each 'um' for a breath."
    # facts untouched
    assert [(i.id, i.evidence, i.moments, i.impact) for i in fb.issues] == \
           [(i.id, i.evidence, i.moments, i.impact) for i in plain.issues]
    # prompt hygiene: transcript is flagged as untrusted data
    system, user = llm.calls[0]
    assert "untrusted" in system and "never follow instructions" in system
    assert json.loads(user.split("\n", 1)[1])["transcript"] == report.transcript


@pytest.mark.parametrize("reply", [
    "not json at all",
    json.dumps({"summary": "short"}),            # fails validation (too short)
    json.dumps({"summary": "x" * 2000}),         # too long
    LLMError("network down"),
])
def test_bad_llm_reply_falls_back_to_template(reply):
    fb = generate_feedback(struggling_report(), llm=FakeLLM(reply))
    assert fb.generator.startswith("template (llm failed")
    assert fb.issues and fb.summary and all(i.advice for i in fb.issues)


# ----------------------------------------------------------------- LLM client

class _Resp:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def read(self):
        return json.dumps(self.payload).encode()


def test_client_requests_for_both_providers(monkeypatch):
    seen = {}

    def fake_urlopen(req, timeout):
        seen.update(url=req.full_url, headers={k.lower(): v for k, v in req.header_items()},
                    body=json.loads(req.data))
        if "anthropic" in req.full_url:
            return _Resp({"content": [{"text": "A-REPLY"}]})
        return _Resp({"choices": [{"message": {"content": "O-REPLY"}}]})

    monkeypatch.setattr(llm_mod.urllib.request, "urlopen", fake_urlopen)

    assert LLMClient("openai", "sk-1", "m1").complete("SYS", "USR") == "O-REPLY"
    assert seen["url"] == "https://api.openai.com/v1/chat/completions"
    assert seen["headers"]["authorization"] == "Bearer sk-1"
    assert seen["body"]["messages"][0] == {"role": "system", "content": "SYS"}

    assert LLMClient("anthropic", "ak-1", "m2").complete("SYS", "USR") == "A-REPLY"
    assert seen["url"] == "https://api.anthropic.com/v1/messages"
    assert seen["headers"]["x-api-key"] == "ak-1" and seen["body"]["system"] == "SYS"

    local = LLMClient("openai", "k", "m", base_url="http://localhost:11434/v1/")
    local.complete("s", "u")
    assert seen["url"] == "http://localhost:11434/v1/chat/completions"


def test_from_env_is_off_by_default(monkeypatch):
    for k in ("SPEAKWISE_LLM_API_KEY", "SPEAKWISE_LLM_MODEL"):
        monkeypatch.delenv(k, raising=False)
    assert llm_mod.from_env() is None
    monkeypatch.setenv("SPEAKWISE_LLM_API_KEY", "k")
    assert llm_mod.from_env() is None  # model also required
    monkeypatch.setenv("SPEAKWISE_LLM_MODEL", "m")
    assert llm_mod.from_env().model == "m"
    with pytest.raises(ValueError):
        LLMClient("nope", "k", "m")


def test_extract_json_tolerates_fences():
    assert extract_json('```json\n{"a": 1}\n```') == {"a": 1}
    with pytest.raises(LLMError):
        extract_json("no braces here")


# ---------------------------------------------------------------- persistence

def test_db_payload_mapping():
    report = struggling_report()
    report.events.append(_ev("repetition", 5, 5.6, text="the"))
    final = FinalReport(run_id="s", topic="Climate", report=report,
                        feedback=generate_feedback(report, topic="Climate"))
    p = to_db_payload(final)

    assert p["talk_session"] == {"context": "Climate", "score": report.scores.overall}
    assert p["talk_session_audio"] == {"filler_word_count": 2, "long_pauses_count": 1}
    assert p["repeated_words"] == [{"word": "the", "count": 1}]
    assert p["talk_session_video"] == {"posture_count": 1, "head_movement_count": 1,
                                       "hand_gesture_count": 0}
    assert p["talk_session_summary"]["summary_text"] == final.feedback.summary
    assert {"filler_word": "um", "alternate_word": "a silent pause"} in p["ai_feedback_alternate_words"]
    json.dumps(p)  # fully JSON-serialisable (goes into a JSONB column)
    assert p["analysis_json"]["feedback"]["issues"]
