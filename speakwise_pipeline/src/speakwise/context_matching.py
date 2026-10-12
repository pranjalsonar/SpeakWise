"""Context evaluation: compare what was said with the assigned topic and reading material.

RUBRIC (version 0.1-provisional). Four separate dimensions, never merged silently:

1. Reliability gate. Unavailable if the speech has < ctx_min_speech_words content words or
   no reading material was supplied; a warning if mean recognition confidence is low or
   the material is very short.

2. Topic relevance (0-100). The speech is cut into units (12-45 words, at sentence ends).
   For each unit, s = max cosine similarity (MiniLM embeddings) to (a) the closest
   material passage, (b) the material centroid, (c) the topic statement. Relevance
   r = clip((s - floor) / (full - floor), 0, 1) with floor=0.12 and full=0.50, anchors
   measured on seed examples (README). Exact shared terminology can raise r via an
   IDF-weighted word-overlap score. Topic relevance = word-weighted mean r x 100.
   Units are labelled on_topic (r >= 0.5), related (0.25 <= r < 0.5, or a weak unit
   that opens the talk or sits between on-topic units: introductions, transitions,
   personal examples; a short bridging unit counts as a transition even if it shares no
   wording), off_topic (otherwise, including long digressions) or too_short.

3. Key-point coverage. Key points are supplied, or extracted from the material (the most
   representative sentence of each section, at most ctx_key_points_max, chosen for
   diversity). A key point is covered when a spoken sentence has cosine >= 0.50 with it
   AND it is that sentence's best-matching key point (margin 0.02). Thresholds were tuned
   on the author-written seed set and still need validation on human-rated data.
   raw = covered / all key points; adjusted = covered / expected, where
   expected = clip(round(minutes x ctx_points_per_minute), 1, K) for the speaking
   duration, so a 1-minute talk is not penalised for skipping a 2,000-word text.

4. Reference consistency (per claim, never a score). Declarative transcript sentences
   (>= 6 words) are matched to the 3 closest material passages; an NLI model compares
   each (passage -> claim):
     supported              entailment >= 0.60
     potentially_inconsistent contradiction >= 0.70 with a closely related passage
                              (cosine >= 0.45) and entailment < 0.30
     not_addressed          no related passage (cosine < 0.35) or neither label decisive
     unable_to_evaluate     words recognised with low confidence, or no NLI model
   "Not addressed" is not "wrong": speakers may add valid outside knowledge.

Composite context_alignment = 0.6 x relevance + 0.4 x adjusted coverage (weights in
config). The 70/100 threshold is PROVISIONAL until compared with human ratings.
"""
from __future__ import annotations

import math
import re
from collections import Counter
from typing import Any, Optional, Sequence, Union

import numpy as np

from speakwise.config import PipelineConfig
from speakwise.schemas import (Claim, ContextEvaluation, KeyPoint, Metric, SpeechUnit, Status, TimedEvent,
                               Transcription, WordToken)

RUBRIC_VERSION = "0.1-provisional"
STOP = set("""a about above after again against all am an and any are as at be because been before being below
between both but by can could did do does doing down during each few for from further had has have having he
her here hers him his how i if in into is it its itself just me more most my myself no nor not of off on once
only or other our ours out over own same she should so some such than that the their them then there these
they this those through to too under until up us was we were what when where which while who whom why will
with would you your yours yeah okay also like um uh er hmm shall may might must one two going get got thing
things way people make made use used many much even well really very lot lots good bad know think say said
""".split())
_WORD = re.compile(r"[A-Za-z][A-Za-z'\-]*")
_SENT = re.compile(r"(?<=[.!?])\s+|\n+")
_HESITATION = re.compile(r"^(u+h*m+|u+h+|e+r+m*|a+h+|h+m+|m{2,})[,.!?]*$", re.IGNORECASE)


def _stem(w: str) -> str:
    for suf in ("ing", "ed", "es", "s", "ly"):
        if w.endswith(suf) and len(w) - len(suf) >= 4:
            return w[: -len(suf)]
    return w


def content_stems(text: str) -> list[str]:
    return [_stem(w) for w in (x.lower() for x in _WORD.findall(text)) if w not in STOP and len(w) > 2]


def sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENT.split(text) if s and s.strip()]


def _scale(x: float, lo: float, hi: float) -> float:
    return float(min(1.0, max(0.0, (x - lo) / (hi - lo))))


def _snip(t: str, n: int = 160) -> str:
    return t if len(t) <= n else t[: n - 3].rstrip() + "..."


# ------------------------------------------------------------------ material
def split_material(material: str) -> tuple[list[str], list[int], list[list[str]]]:
    """-> (passages, section index of each passage, sentences of each section). Sections are
    paragraphs (tiny ones merged); a text without blank lines is chunked every 4 sentences."""
    text = re.sub(r"[#*_`>|]+", " ", material).strip()
    paras = [p for p in (sentences(x) for x in re.split(r"\n\s*\n", text) if x.strip()) if p]
    if len(paras) == 1:
        paras = [paras[0][i:i + 4] for i in range(0, len(paras[0]), 4)]
    sections: list[list[str]] = []
    carry: list[str] = []
    for p in paras:
        p = carry + p
        if sum(len(s.split()) for s in p) < 20:
            carry = p
            continue
        sections.append(p)
        carry = []
    if carry:
        (sections[-1].extend(carry) if sections else sections.append(carry))
    passages, owner = [], []
    for k, sents in enumerate(sections):
        i = 0
        while i < len(sents):
            chunk = [sents[i]]
            if len(sents[i].split()) < 18 and i + 1 < len(sents):
                chunk.append(sents[i + 1])
                i += 1
            passages.append(" ".join(chunk))
            owner.append(k)
            i += 1
    return passages, owner, sections


class Lexical:
    """IDF-weighted share of a text's topical words that occur in the material."""

    def __init__(self, passages: list[str], extra: str = ""):
        docs = [set(content_stems(p)) for p in passages]
        df: Counter = Counter()
        for d in docs:
            df.update(d)
        n = max(len(docs), 1)
        self.idf = {t: math.log(1 + n / c) for t, c in df.items()}
        self.default = (sum(self.idf.values()) / len(self.idf)) if self.idf else 1.0
        for t in content_stems(extra):
            self.idf.setdefault(t, self.default)

    def containment(self, text: str) -> float:
        u = set(content_stems(text))
        tot = sum(self.idf.get(t, self.default) for t in u)
        return sum(self.idf[t] for t in u if t in self.idf) / tot if tot else 0.0


# -------------------------------------------------------------- transcript
def build_units(words: Sequence[WordToken], cfg: PipelineConfig) -> list[tuple[Optional[float], Optional[float], str]]:
    """Speech units (start, end, text) at sentence ends, hesitation sounds removed."""
    kept = [w for w in words if not _HESITATION.match(w.text.strip())]
    units, cur = [], []
    for w in kept:
        cur.append(w)
        end = w.text.rstrip()[-1:] in ".?!"
        if len(cur) >= cfg.ctx_unit_max_words or (end and len(cur) >= cfg.ctx_unit_min_words):
            units.append((cur[0].start, cur[-1].end, " ".join(x.text for x in cur)))
            cur = []
    if cur:
        if units and len(cur) < cfg.ctx_unit_min_words // 2:
            s, _, t = units.pop()
            units.append((s, cur[-1].end, t + " " + " ".join(x.text for x in cur)))
        else:
            units.append((cur[0].start, cur[-1].end, " ".join(x.text for x in cur)))
    return units


def text_to_words(text: str) -> list[WordToken]:
    """Untimed transcript -> pseudo-words (times are None in the output)."""
    return [WordToken(text=t, start=float(i), end=float(i)) for i, t in enumerate(text.split())]


# ----------------------------------------------------------------- evaluate
def evaluate_context(
    topic: str,
    reading_material: str,
    transcript: Union[str, Transcription],
    config: Optional[PipelineConfig] = None,
    speaking_duration_s: Optional[float] = None,
    key_points: Optional[list[str]] = None,
    embedder: Any = "auto",
    nli: Any = "auto",
) -> ContextEvaluation:
    """Evaluate a transcript against the topic and the exact reading material.

    embedder / nli: objects with .encode(list[str]) / .predict(list[(premise, hypothesis)]),
    "auto" to load the configured ONNX models, or None to disable (documented fallback)."""
    cfg = config or PipelineConfig()
    timed = isinstance(transcript, Transcription)
    words = list(transcript.words) if timed else text_to_words(transcript or "")
    probs = [w.probability for w in words if w.probability is not None]
    mean_prob = float(np.mean(probs)) if probs else None
    material = reading_material or ""
    method = {"rubric": __doc__.split("RUBRIC", 1)[1].strip() if __doc__ else "", "embedder": None, "nli": None}
    missing = lambda u, r: Metric.missing(u, r)  # noqa: E731

    ce = ContextEvaluation(
        status=Status.ok, rubric_version=RUBRIC_VERSION, method=method,
        topic_relevance=missing("score_0_100", "not evaluated"),
        key_point_coverage_raw=missing("percent", "not evaluated"),
        key_point_coverage_adjusted=missing("percent", "not evaluated"),
        context_alignment=missing("score_0_100", "not evaluated"),
        provisional_threshold=cfg.ctx_threshold,
        limitations=[
            "Scores measure semantic closeness to the material, not factual correctness.",
            f"The {cfg.ctx_threshold:.0f}/100 target is provisional until validated against human ratings.",
            "Errors in the transcript propagate into every context dimension."])

    # ---- 1. reliability gate
    content_n = len(content_stems(" ".join(w.text for w in words)))
    reasons, rel_status = [], Status.ok
    if not material.strip():
        reasons.append("No reading material was provided.")
        rel_status = Status.unavailable
    elif len(material.split()) < 80:
        reasons.append(f"The reading material is very short ({len(material.split())} words).")
        rel_status = Status.warning
    if content_n < cfg.ctx_min_speech_words:
        reasons.append(f"Only {content_n} topical words were recognised (need {cfg.ctx_min_speech_words}).")
        rel_status = Status.unavailable
    if mean_prob is not None and mean_prob < cfg.ctx_low_asr_conf and rel_status != Status.unavailable:
        reasons.append(f"Low transcript confidence (mean word probability {mean_prob:.2f}).")
        rel_status = Status.warning
    ce.reliability = {"status": rel_status.value, "content_words": content_n,
                      "mean_word_probability": round(mean_prob, 3) if mean_prob is not None else None,
                      "reasons": reasons}
    if rel_status == Status.unavailable:
        ce.status = Status.unavailable
        ce.warnings = reasons
        return ce

    # ---- models
    if embedder == "auto":
        from speakwise.onnx_models import OnnxEmbedder

        embedder = OnnxEmbedder(cfg)
    if nli == "auto":
        try:
            from speakwise.onnx_models import OnnxNLI

            nli = OnnxNLI(cfg)
        except Exception as exc:  # noqa: BLE001 - consistency degrades, other dimensions continue
            ce.warnings.append(f"NLI model unavailable ({type(exc).__name__}); consistency was not evaluated.")
            nli = None
    method["embedder"] = getattr(embedder, "name", None) if embedder is not None else "word-overlap fallback"
    method["nli"] = getattr(nli, "name", None) if nli is not None else None

    passages, owner, sections = split_material(material)
    units_raw = build_units(words, cfg)
    unit_text = [u[2] for u in units_raw]
    lex = Lexical(passages, topic)

    # ---- 2. relevance
    if embedder is not None:
        P = embedder.encode(passages)
        U = embedder.encode(unit_text)
        UP = U @ P.T
        centroid = P.mean(0)
        centroid /= max(np.linalg.norm(centroid), 1e-9)
        sims = np.maximum(UP.max(1), U @ centroid)
        if topic.strip():
            sims = np.maximum(sims, (U @ embedder.encode([topic]).T)[:, 0])
        rel = np.array([_scale(s, cfg.ctx_sim_floor, cfg.ctx_sim_full) for s in sims])
        lex_rel = np.array([_scale(lex.containment(t), 0.15, 0.55) for t in unit_text])
        rel = np.maximum(rel, 0.85 * lex_rel)
        closest = UP.argmax(1)
    else:
        ce.warnings.append("Embedding model unavailable; relevance uses word overlap, which under-rates paraphrases.")
        rel = np.array([_scale(lex.containment(t), 0.15, 0.55) for t in unit_text])
        closest = np.full(len(unit_text), -1)
        UP = None

    n_content = np.array([len(content_stems(t)) for t in unit_text], dtype=float)
    counted = n_content >= cfg.ctx_min_content_words
    labels = []
    for i in range(len(unit_text)):
        if not counted[i]:
            labels.append("too_short")
        elif rel[i] >= 0.5:
            labels.append("on_topic")
        elif rel[i] >= cfg.ctx_offtopic_relevance:
            labels.append("related")
        else:
            labels.append("pending")
    for i, lab in enumerate(labels):  # context smoothing: intros / transitions / personal examples
        if lab != "pending":
            continue
        prev_on = i > 0 and labels[i - 1] == "on_topic"
        next_on = i + 1 < len(labels) and labels[i + 1] == "on_topic"
        bridging = (prev_on and next_on) or (i == 0 and next_on)  # transition or introduction
        if bridging and (rel[i] >= 0.1 or n_content[i] <= cfg.ctx_transition_max_words):
            labels[i] = "related"
        else:
            labels[i] = "off_topic"

    for i, (s, e, t) in enumerate(units_raw):
        ce.units.append(SpeechUnit(start=s if timed else None, end=e if timed else None, text=_snip(t, 300),
                                   relevance=round(float(rel[i]), 3), label=labels[i],
                                   closest_passage=_snip(passages[closest[i]]) if closest[i] >= 0 else None))
        if labels[i] == "off_topic":
            ce.off_topic_segments.append(TimedEvent(type="off_topic", start=s if timed else 0.0,
                                                    end=e if timed else 0.0, text=_snip(t, 200),
                                                    details={"relevance": round(float(rel[i]), 3),
                                                             "timestamps": timed}))
    if counted.any():
        w = n_content * counted
        ce.topic_relevance = Metric.measured(float((rel * w).sum() / w.sum() * 100), "score_0_100",
                                             denominator=f"{int(counted.sum())} speech units, weighted by topical words",
                                             warn=rel_status == Status.warning)

    # ---- 3. key points
    kp_texts, source = (list(key_points), "provided") if key_points else (_extract_key_points(sections, embedder, cfg), "extracted")
    duration = speaking_duration_s or ((words[-1].end - words[0].start) if timed and words else None)
    if kp_texts:
        # Sentence-level and specific: a key point is covered when a spoken sentence is close to it
        # AND it is that sentence's best-matching key point (within a small margin). Whole units
        # were too coarse: any on-topic unit looked "close" to every key point of the material.
        sents = [c for c in speech_sentences(words) if len(c) >= 5]
        sent_text = [" ".join(w.text for w in c) for c in sents] or unit_text
        if embedder is not None and sent_text:
            K = embedder.encode(kp_texts)
            S = embedder.encode(sent_text) @ K.T  # sentences x key points
            ok = (S >= cfg.ctx_keypoint_cover_sim) & (S >= S.max(1, keepdims=True) - cfg.ctx_keypoint_margin)
            masked = np.where(ok, S, -1.0)
            covered = ok.any(0)
            best_u = np.where(covered, masked.argmax(0), S.argmax(0))
            best_s = S.max(0)
        else:
            spoken = set(content_stems(" ".join(sent_text)))
            best_s = np.array([len(set(content_stems(k)) & spoken) / max(len(set(content_stems(k))), 1) for k in kp_texts])
            covered, best_u = best_s >= 0.5, np.full(len(kp_texts), -1)
        for j, k in enumerate(kp_texts):
            u = int(best_u[j])
            has_ev = bool(covered[j]) and 0 <= u < len(sent_text)
            ce.key_points.append(KeyPoint(
                id=j + 1, text=_snip(k, 220), source=source, covered=bool(covered[j]), similarity=round(float(best_s[j]), 3),
                evidence_start=sents[u][0].start if has_ev and timed and sents else None,
                evidence_text=_snip(sent_text[u], 160) if has_ev else None))
        n_cov, K_n = int(covered.sum()), len(kp_texts)
        ce.key_point_coverage_raw = Metric.measured(100 * n_cov / K_n, "percent", denominator=f"{K_n} key points ({source})")
        if duration:
            expected = int(min(K_n, max(1, round(duration / 60 * cfg.ctx_points_per_minute))))
            ce.key_point_coverage_adjusted = Metric.measured(
                min(100.0, 100 * n_cov / expected), "percent",
                denominator=f"{expected} key points expected for {duration / 60:.1f} min at {cfg.ctx_points_per_minute}/min")
        else:
            ce.key_point_coverage_adjusted = Metric.missing("percent", "speaking duration unknown")

    # ---- 4. consistency
    ce.claims = _evaluate_claims(words, timed, passages, embedder, nli, cfg)
    ce.consistency_counts = dict(Counter(c.label for c in ce.claims))
    if nli is None:
        ce.limitations.append("Consistency with the material was not evaluated (no NLI model).")

    # ---- composite (documented, provisional)
    if ce.topic_relevance.status.has_value and ce.key_point_coverage_adjusted.status.has_value:
        w = cfg.ctx_relevance_weight
        val = w * ce.topic_relevance.value + (1 - w) * ce.key_point_coverage_adjusted.value
        ce.context_alignment = Metric.measured(
            val, "score_0_100", warn=True,
            denominator=f"{w:.1f} x topic relevance + {1 - w:.1f} x adjusted key-point coverage",
            note=f"provisional rubric {RUBRIC_VERSION}; not validated against human ratings")
        ce.verdict = "meets_provisional_target" if val >= cfg.ctx_threshold else "below_provisional_target"

    if ce.consistency_counts.get("potentially_inconsistent"):
        ce.warnings.append(f"{ce.consistency_counts['potentially_inconsistent']} statement(s) may conflict with the "
                           "reading material; check them against the source.")
    ce.warnings += [r for r in reasons if r not in ce.warnings]
    ce.status = Status.warning if (ce.warnings or rel_status == Status.warning) else Status.ok
    return ce


def _extract_key_points(sections: list[list[str]], embedder, cfg: PipelineConfig) -> list[str]:
    """Most representative sentence per section; if too many sections, a diverse subset."""
    if not sections:
        return []
    if embedder is None:
        reps = [s[0] for s in sections]
    else:
        reps = []
        for sents in sections:
            E = embedder.encode(sents)
            c = E.mean(0)
            reps.append(sents[int((E @ c).argmax())])
    if len(reps) <= cfg.ctx_key_points_max:
        return reps
    if embedder is None:
        idx = np.linspace(0, len(reps) - 1, cfg.ctx_key_points_max).round().astype(int)
        return [reps[i] for i in idx]
    E = embedder.encode(reps)
    centroid = E.mean(0)
    chosen = [int((E @ centroid).argmax())]
    while len(chosen) < cfg.ctx_key_points_max:  # maximal marginal relevance
        score = 0.5 * (E @ centroid) - 0.5 * (E @ E[chosen].T).max(1)
        score[chosen] = -np.inf
        chosen.append(int(score.argmax()))
    return [reps[i] for i in sorted(chosen)]


def speech_sentences(words: Sequence[WordToken]) -> list[list[WordToken]]:
    """Transcript words grouped into sentences (hesitation sounds removed)."""
    out: list[list[WordToken]] = []
    cur: list[WordToken] = []
    for w in words:
        if _HESITATION.match(w.text.strip()):
            continue
        cur.append(w)
        if w.text.rstrip()[-1:] in ".?!":
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return out


def _evaluate_claims(words, timed, passages, embedder, nli, cfg: PipelineConfig, max_claims: int = 60) -> list[Claim]:
    claims_w = speech_sentences(words)
    cands = [c for c in claims_w if len(c) >= cfg.ctx_claim_min_words and not c[-1].text.rstrip().endswith("?")
             and len(content_stems(" ".join(w.text for w in c))) >= 3][:max_claims]
    if not cands:
        return []
    texts = [" ".join(w.text for w in c) for c in cands]
    out: list[Claim] = []

    def make(i, label, **kw):
        c = cands[i]
        return Claim(text=_snip(texts[i], 300), start=c[0].start if timed else None,
                     end=c[-1].end if timed else None, label=label, **kw)

    if embedder is None or nli is None:
        return [make(i, "unable_to_evaluate", reason="NLI or embedding model unavailable") for i in range(len(cands))]

    C = embedder.encode(texts)
    P = embedder.encode(passages)
    S = C @ P.T
    pairs, owners = [], []
    for i in range(len(cands)):
        top = np.argsort(-S[i])[: cfg.ctx_retrieval_k]
        for j in top:
            if S[i, j] >= cfg.ctx_retrieval_min_sim:
                pairs.append((passages[j], texts[i]))
                owners.append((i, j))
    preds = nli.predict(pairs) if pairs else []
    by_claim: dict[int, list[tuple[int, dict]]] = {}
    for (i, j), p in zip(owners, preds):
        by_claim.setdefault(i, []).append((j, p))

    for i, c in enumerate(cands):
        best_j = int(S[i].argmax())
        best_sim = float(S[i, best_j])
        probs = [w.probability for w in c if w.probability is not None]
        if timed and probs and float(np.mean(probs)) < cfg.low_confidence_word_prob:
            out.append(make(i, "unable_to_evaluate", retrieval_similarity=round(best_sim, 3),
                            reason="these words were recognised with low confidence"))
            continue
        results = by_claim.get(i, [])
        if not results:
            out.append(make(i, "not_addressed", retrieval_similarity=round(best_sim, 3),
                            reason="no closely related passage in the material"))
            continue
        ent_j, ent = max(((j, p.get("entailment", 0.0)) for j, p in results), key=lambda x: x[1])
        close = [(j, p.get("contradiction", 0.0)) for j, p in results if S[i, j] >= cfg.ctx_contradict_min_sim]
        con_j, con = max(close, key=lambda x: x[1]) if close else (best_j, 0.0)
        if ent >= cfg.ctx_entail_min:
            out.append(make(i, "supported", evidence=_snip(passages[ent_j], 240), retrieval_similarity=round(float(S[i, ent_j]), 3),
                            entailment=round(ent, 3), contradiction=round(con, 3)))
        elif con >= cfg.ctx_contradict_min and ent < 0.3:
            out.append(make(i, "potentially_inconsistent", evidence=_snip(passages[con_j], 240),
                            retrieval_similarity=round(float(S[i, con_j]), 3), entailment=round(ent, 3),
                            contradiction=round(con, 3),
                            reason="a closely related passage appears to say something different"))
        else:
            out.append(make(i, "not_addressed", evidence=_snip(passages[best_j], 240), retrieval_similarity=round(best_sim, 3),
                            entailment=round(ent, 3), contradiction=round(con, 3),
                            reason="related passage neither clearly supports nor contradicts it"))
    return out
