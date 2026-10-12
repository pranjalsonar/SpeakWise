"""Retrieval over the speaking-tips knowledge base (knowledge/tips.json).

Plain BM25 (no ML dependency). Each tip carries `issues` tags, so retrieval is
"filter by the detected issue, then rank by relevance to the issue's evidence".
That keeps the RAG step precise on a small, curated corpus. If the corpus grows
into the hundreds, swap `Retriever.search` for an embedding index
(sentence-transformers + FAISS/pgvector) with the same interface.
"""
import json
import math
import re
from collections import Counter
from functools import lru_cache
from pathlib import Path
from typing import Optional

KNOWLEDGE_DIR = Path(__file__).resolve().parent / "knowledge"
_TOKEN = re.compile(r"[a-z]+")
_STOP = {"a", "an", "the", "and", "or", "of", "to", "in", "on", "for", "is", "are", "it", "you",
         "your", "with", "that", "this", "as", "at", "be", "by", "from", "can", "not", "more"}


def _stem(token: str) -> str:
    """Very light stemming so "gesture" matches "gestures" / "pauses" matches "pause"."""
    if len(token) > 4 and token.endswith("ies"):
        return token[:-3] + "y"
    if len(token) > 3 and token.endswith("s") and not token.endswith("ss"):
        return token[:-1]
    return token


def tokenize(text: str) -> list[str]:
    return [_stem(t) for t in _TOKEN.findall(text.lower()) if t not in _STOP and len(t) > 1]


class Retriever:
    def __init__(self, tips: list[dict], k1: float = 1.5, b: float = 0.75):
        self.tips = tips
        self.k1, self.b = k1, b
        self._docs = [Counter(tokenize(f'{t["title"]} {t["text"]} {t.get("drill", "")}')) for t in tips]
        self._lens = [sum(d.values()) for d in self._docs]
        self._avg = sum(self._lens) / max(len(self._lens), 1)
        df: Counter = Counter()
        for d in self._docs:
            df.update(d.keys())
        n = len(tips)
        self._idf = {w: math.log(1 + (n - c + 0.5) / (c + 0.5)) for w, c in df.items()}

    def _score(self, query: list[str], i: int) -> float:
        doc, length = self._docs[i], self._lens[i]
        score = 0.0
        for w in set(query):
            f = doc.get(w, 0)
            if f:
                denom = f + self.k1 * (1 - self.b + self.b * length / self._avg)
                score += self._idf.get(w, 0.0) * f * (self.k1 + 1) / denom
        return score

    def search(self, query: str, k: int = 2, issue: Optional[str] = None) -> list[dict]:
        """Top-k tips. With `issue`, only tips tagged with it are considered (falling
        back to all tips if none are tagged). The tip curated as primary for the issue
        always comes first; the rest are ranked by BM25 against the query, then KB order."""
        q = tokenize(query)
        candidates = [i for i, t in enumerate(self.tips) if issue is None or issue in t["issues"]]
        if not candidates:
            candidates = list(range(len(self.tips)))
        def rank(i: int) -> tuple[int, float, int]:
            primary = bool(issue and issue in self.tips[i].get("primary_for", []))
            return (0 if primary else 1, -self._score(q, i), i)

        ranked = sorted(candidates, key=rank)
        return [self.tips[i] for i in ranked[:k]]


@lru_cache(maxsize=1)
def default_retriever() -> Retriever:
    tips = json.loads((KNOWLEDGE_DIR / "tips.json").read_text(encoding="utf-8"))
    return Retriever(tips)


@lru_cache(maxsize=1)
def vocabulary_data() -> dict:
    return json.loads((KNOWLEDGE_DIR / "vocabulary.json").read_text(encoding="utf-8"))
