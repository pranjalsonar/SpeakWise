"""Context-matching tests.

Logic tests use a deterministic bag-of-words stand-in embedder and a rule-based stand-in
NLI (clearly test doubles). One test uses the real MiniLM model when it is downloaded.
"""
import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from speakwise import models
from speakwise.config import PipelineConfig
from speakwise.context_matching import content_stems, evaluate_context, split_material
from speakwise.schemas import Status, Transcription, WordToken

DATA = Path(__file__).resolve().parents[1] / "data" / "context_eval"
CFG = PipelineConfig(ctx_min_speech_words=10)


class BowEmbedder:
    """TEST DOUBLE: hashed bag of word stems -> unit vector. Similar wording = similar vector."""
    name = "bow-test-double"

    def encode(self, texts):
        out = np.zeros((len(texts), 512), np.float32)
        for i, t in enumerate(texts):
            for w in content_stems(t):
                out[i, int(hashlib.md5(w.encode()).hexdigest(), 16) % 512] += 1
        n = np.linalg.norm(out, axis=1, keepdims=True)
        return out / np.maximum(n, 1e-9)


class RuleNLI:
    """TEST DOUBLE: 'not'/'never'/'cools' in the hypothesis -> contradiction, else entailment
    when most hypothesis stems appear in the premise, else neutral."""
    name = "rule-test-double"

    def predict(self, pairs):
        out = []
        for prem, hyp in pairs:
            if any(w in hyp.lower().split() for w in ("not", "never", "cools")):
                out.append({"contradiction": 0.9, "entailment": 0.05, "neutral": 0.05})
                continue
            h, p = set(content_stems(hyp)), set(content_stems(prem))
            ent = len(h & p) / max(len(h), 1)
            out.append({"entailment": ent, "contradiction": 0.0, "neutral": 1 - ent})
        return out


MATERIAL = """Fossil fuels such as coal oil and gas are burned for electricity and release carbon dioxide into the atmosphere every year.

Carbon dioxide traps heat in the atmosphere which raises the global temperature of the planet and melts polar ice.

Solar panels and wind turbines produce renewable electricity without burning fossil fuels and their costs keep falling.

Rising sea levels threaten coastal cities and islands where millions of people live and farm near the water."""


def timed(text, start=0.0, step=0.4, prob=0.9):
    words = [WordToken(text=t, start=round(start + i * step, 2), end=round(start + i * step + 0.3, 2), probability=prob)
             for i, t in enumerate(text.split())]
    return Transcription(status=Status.ok, words=words, text=text)


ON = ("Coal oil and gas are burned for electricity and release carbon dioxide into the atmosphere. "
      "Carbon dioxide traps heat and raises the global temperature and melts the polar ice. ")
OFF = "My favourite cricket player scored a century yesterday and our college team celebrated with pizza and music all night long. "


def run(transcript, **kw):
    return evaluate_context("Climate change", MATERIAL, transcript, CFG, embedder=BowEmbedder(), nli=kw.pop("nli", RuleNLI()), **kw)


def test_split_material_sections():
    passages, owner, sections = split_material(MATERIAL)
    # paragraphs under 20 words are merged with the next one
    assert 2 <= len(sections) <= 4 and len(passages) >= len(sections) and max(owner) == len(sections) - 1


def test_relevant_vs_off_topic_and_timestamps():
    rel = run(timed(ON * 2))
    off = run(timed(OFF * 2))
    assert rel.topic_relevance.value > 70 > off.topic_relevance.value
    assert rel.off_topic_segments == [] and len(off.off_topic_segments) >= 1
    seg = off.off_topic_segments[0]
    assert seg.details["timestamps"] and seg.end > seg.start  # times come from the word timestamps
    assert all(u.label in ("on_topic", "related") for u in rel.units)


def test_weak_unit_between_on_topic_units_is_not_off_topic():
    bridge = "Let me give you one more thing that I noticed in my own home recently. "
    ce = run(timed(ON + bridge + ON))
    labels = [u.label for u in ce.units]
    assert "off_topic" not in labels


def test_unavailable_without_material_or_speech():
    no_mat = evaluate_context("Climate", "", timed(ON), CFG, embedder=BowEmbedder(), nli=None)
    assert no_mat.status == Status.unavailable and no_mat.topic_relevance.value is None
    short = run(timed("Coal burns."))
    assert short.status == Status.unavailable
    assert any("topical words" in r for r in short.reliability["reasons"])


def test_key_point_coverage_raw_and_duration_adjusted():
    kps = ["Burning coal oil and gas releases carbon dioxide.", "Solar panels and wind turbines make renewable electricity.",
           "Rising sea levels threaten coastal cities."]
    ce = run(timed(ON * 2), key_points=kps, speaking_duration_s=60)
    covered = [k.covered for k in ce.key_points]
    assert covered[0] and not covered[1]
    assert ce.key_point_coverage_raw.value == pytest.approx(100 * sum(covered) / 3, abs=1e-3)
    # 1 minute x 1.5 points/min -> 2 expected key points
    assert "2 key points expected" in ce.key_point_coverage_adjusted.denominator
    assert all(k.source == "provided" for k in ce.key_points)
    assert ce.key_points[0].evidence_start is not None


def test_composite_is_documented_and_provisional():
    ce = run(timed(ON * 2), speaking_duration_s=60)
    w = CFG.ctx_relevance_weight
    expect = w * ce.topic_relevance.value + (1 - w) * ce.key_point_coverage_adjusted.value
    assert ce.context_alignment.value == pytest.approx(expect, abs=0.01)
    assert ce.context_alignment.status == Status.warning and "provisional" in ce.context_alignment.note
    assert ce.verdict in ("meets_provisional_target", "below_provisional_target")


def test_claim_labels():
    text = ("Coal oil and gas are burned for electricity and release carbon dioxide. "
            "Carbon dioxide never traps heat in the atmosphere at all. "
            "My cousin bought a new bicycle from the market last weekend. ") * 2
    ce = run(timed(text))
    labels = {c.text.split()[0]: c.label for c in ce.claims}
    assert labels["Coal"] == "supported"
    assert labels["Carbon"] == "potentially_inconsistent"
    assert labels["My"] == "not_addressed"  # absent from the material is NOT "wrong"
    assert ce.consistency_counts["potentially_inconsistent"] >= 1


def test_low_confidence_claims_are_not_judged():
    ce = run(timed(ON * 2, prob=0.3))
    assert ce.claims and all(c.label == "unable_to_evaluate" for c in ce.claims)
    assert ce.reliability["status"] == "warning"


def test_no_nli_model_degrades_gracefully():
    ce = run(timed(ON * 2), nli=None)
    assert ce.topic_relevance.value is not None
    assert all(c.label == "unable_to_evaluate" for c in ce.claims)
    assert any("not evaluated" in l for l in ce.limitations)


def test_untimed_text_transcript():
    ce = run(ON * 2)
    assert ce.units[0].start is None and ce.topic_relevance.value > 70


@pytest.mark.models
def test_real_embedder_orders_seed_examples():
    if not models.is_available("all-MiniLM-L6-v2"):
        pytest.skip("MiniLM not downloaded")
    from speakwise.onnx_models import OnnxEmbedder

    mats = json.loads((DATA / "materials.json").read_text(encoding="utf-8"))
    ex = {json.loads(l)["id"]: json.loads(l) for l in (DATA / "seed.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()}
    m = mats["climate_change"]
    text = (DATA / m["file"]).read_text(encoding="utf-8")
    emb = OnnxEmbedder(PipelineConfig())
    score = {k: evaluate_context(m["topic"], text, ex[k]["transcript"], PipelineConfig(), embedder=emb, nli=None)
             .topic_relevance.value for k in ("cc-01-relevant", "cc-03-paraphrase", "cc-05-offtopic")}
    assert score["cc-01-relevant"] > 70 and score["cc-03-paraphrase"] > 70 and score["cc-05-offtopic"] < 40


def test_long_digression_between_on_topic_units_is_still_off_topic():
    ce = run(timed(ON + OFF * 2 + ON))
    assert any(u.label == "off_topic" for u in ce.units)
