"""Context matching: how well the speech matches the topic and the reading material.

Ported from the POC's context.py. Embeddings run on CPU with fastembed (ONNX) instead of
sentence-transformers/PyTorch, which keeps the backend install small.
"""
import re
import threading

import numpy as np

from app.core.config import settings

PASS_SCORE = 70.0

LEADING_FILLERS = re.compile(
    r"^\s*(?:(?:uh+|um+|erm+|er|ah+|hmm+|so|well|like|okay|you know)\b[\s,]*)+", re.I
)

_embedder = None
_lock = threading.Lock()


def get_embedder():
    global _embedder
    with _lock:
        if _embedder is None:
            from fastembed import TextEmbedding
            _embedder = TextEmbedding(settings.EMBED_MODEL, cache_dir=str(settings.MODELS_DIR / "fastembed"))
    return _embedder


def _encode(texts: list[str]) -> np.ndarray:
    vecs = np.array(list(get_embedder().embed(texts)), dtype=np.float32)
    return vecs / (np.linalg.norm(vecs, axis=1, keepdims=True) + 1e-9)


def _sentences(text):
    text = re.sub(r"(?m)^\s*#{1,6}\s*", "", text)
    text = re.sub(r"(?m)^\s*[-*•]\s*", "", text)
    text = re.sub(r"[*_`]", "", text)
    parts = re.split(r"(?<=[.!?])\s+|\n+", text.strip())
    return [p.strip() for p in parts if len(p.split()) >= 3]


def _windows(sentences, size, step):
    if len(sentences) <= size:
        return [" ".join(sentences)] if sentences else []
    return [" ".join(sentences[i:i + size]) for i in range(0, len(sentences) - size + 1, step)]


def _scale(x, lo, hi):
    return float(np.clip((x - lo) / (hi - lo), 0.0, 1.0))


def context_match(topic: str, material: str, transcript: str, llm_judgement: dict | None = None) -> dict:
    """Return a 0-100 context score (pass >= 70) plus supporting evidence.

    Embedding score = how semantically close each part of the speech is to the closest
    passage in the material, plus whole-speech similarity to topic and material.
    If the LLM judge produced a score, it is blended in (60% embeddings / 40% LLM).
    """
    judgement = llm_judgement or {}
    speech_sents = [LEADING_FILLERS.sub("", s) for s in _sentences(transcript)]
    speech_sents = [s for s in speech_sents if len(s.split()) >= 3]
    words = len(transcript.split())
    if words < 15 or not speech_sents:
        return {"score": 0.0, "passed": False, "embedding_score": 0.0,
                "llm_score": None, "on_topic_pct": 0.0, "material_coverage_pct": 0.0,
                "topic_similarity": 0.0, "sentences": [], "verdict": "",
                "covered_points": [], "missed_points": [], "off_topic_points": [], "factual_issues": [],
                "note": "Too little speech was detected to judge context."}

    mat_chunks = _windows(_sentences(material), size=3, step=2)
    speech_wins = _windows(speech_sents, size=2, step=1)

    M = _encode(mat_chunks)
    S = _encode(speech_wins)
    T = _encode([topic])[0]
    sims = S @ M.T                                   # (speech windows, material chunks)

    best = sims.max(axis=1)
    per_window = np.array([_scale(b, 0.20, 0.55) for b in best])
    on_topic = best >= 0.40
    s_mean = S.mean(axis=0)
    topic_sim = float(s_mean @ T / (np.linalg.norm(s_mean) + 1e-9))
    doc_sim = float(
        (s_mean / (np.linalg.norm(s_mean) + 1e-9))
        @ (M.mean(axis=0) / (np.linalg.norm(M.mean(axis=0)) + 1e-9))
    )
    coverage = float((sims.max(axis=0) >= 0.45).mean())

    embedding_score = 100 * (
        0.40 * per_window.mean()
        + 0.30 * on_topic.mean()
        + 0.15 * _scale(doc_sim, 0.25, 0.70)
        + 0.15 * _scale(topic_sim, 0.15, 0.55)
    )
    llm_score = judgement.get("score")
    score = embedding_score if llm_score is None else 0.6 * embedding_score + 0.4 * llm_score

    sentence_rows = []
    for i, win in enumerate(speech_wins):
        j = int(sims[i].argmax())
        sentence_rows.append({
            "speech": win,
            "match_pct": round(100 * per_window[i], 1),
            "on_topic": bool(on_topic[i]),
            "closest_material": mat_chunks[j][:220],
        })

    return {
        "score": round(score, 1),
        "passed": score >= PASS_SCORE,
        "embedding_score": round(embedding_score, 1),
        "llm_score": None if llm_score is None else round(float(llm_score), 1),
        "on_topic_pct": round(100 * on_topic.mean(), 1),
        "material_coverage_pct": round(100 * coverage, 1),
        "topic_similarity": round(topic_sim, 3),
        "sentences": sentence_rows,
        "verdict": judgement.get("verdict", ""),
        "covered_points": judgement.get("covered_points", []),
        "missed_points": judgement.get("missed_points", []),
        "off_topic_points": judgement.get("off_topic", []),
        "factual_issues": judgement.get("factual_issues", []),
        "note": "" if llm_score is not None else "AI judge unavailable; score is based on meaning similarity only.",
    }
