"""Groq chat completions with strict JSON output, validation and graceful degradation.

Every call:
- sends a system prompt + user prompt from app/prompts (data wrapped in tags, injection-safe);
- asks for a JSON-schema response at temperature 0;
- validates the reply with pydantic and makes one repair attempt if it is invalid;
- retries once on rate limits / server errors, honouring Retry-After (max 8 s);
- falls back to plain JSON mode if the model rejects json_schema or reasoning_effort.
Callers treat LLMError as "feature unavailable" and continue without it.
"""
import json
import logging
import re
import time

import requests
from pydantic import BaseModel, Field, ValidationError, field_validator

from app.core.config import settings
from app.prompts import coach, judge

log = logging.getLogger(__name__)

URL = "https://api.groq.com/openai/v1/chat/completions"
TIMEOUT = (30, 90)
MATERIAL_WORD_LIMIT = 3500


class LLMError(Exception):
    pass


# ---- response models ---------------------------------------------------------
def _trim(items: list[str], n: int) -> list[str]:
    return [s.strip() for s in items if isinstance(s, str) and s.strip()][:n]


class Judgement(BaseModel):
    score: int = Field(ge=0, le=100)
    verdict: str = ""
    covered_points: list[str] = []
    missed_points: list[str] = []
    off_topic: list[str] = []
    factual_issues: list[str] = []

    @field_validator("score", mode="before")
    @classmethod
    def clamp(cls, v):
        return max(0, min(100, int(round(float(v)))))

    def cleaned(self) -> dict:
        return {
            "score": self.score,
            "verdict": self.verdict.strip(),
            "covered_points": _trim(self.covered_points, 5),
            "missed_points": _trim(self.missed_points, 3),
            "off_topic": _trim(self.off_topic, 3),
            "factual_issues": _trim(self.factual_issues, 3),
        }


class Improvement(BaseModel):
    area: str
    advice: str


class CoachFeedback(BaseModel):
    headline: str
    strengths: list[str]
    improvements: list[Improvement]
    encouragement: str

    def cleaned(self) -> dict:
        return {
            "headline": self.headline.strip(),
            "strengths": _trim(self.strengths, 3),
            "improvements": [i.model_dump() for i in self.improvements[:3]],
            "encouragement": self.encouragement.strip(),
        }


# ---- transport -------------------------------------------------------------------
def _request(payload: dict) -> requests.Response:
    for attempt in range(2):
        try:
            resp = requests.post(URL, headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}"},
                                 json=payload, timeout=TIMEOUT)
        except requests.RequestException as exc:
            if attempt == 0:
                time.sleep(1.5)
                continue
            raise LLMError(f"network error: {exc}") from exc
        if (resp.status_code == 429 or resp.status_code >= 500) and attempt == 0:
            time.sleep(min(float(resp.headers.get("retry-after", 2) or 2), 8.0))
            continue
        return resp
    raise LLMError("no response")


def _chat_json(system: str, user: str, schema_name: str, schema: dict, model_cls, max_tokens: int):
    if not settings.GROQ_API_KEY:
        raise LLMError("GROQ_API_KEY missing")
    messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    payload = {
        "model": settings.GROQ_LLM_MODEL,
        "messages": messages,
        "temperature": 0,
        "max_completion_tokens": max_tokens,
        "reasoning_effort": "low",
        "response_format": {"type": "json_schema",
                            "json_schema": {"name": schema_name, "schema": schema, "strict": True}},
    }
    degraded = 0
    repaired = False
    while True:
        resp = _request(payload)
        if resp.status_code == 400 and degraded < 2:
            # Older/other models may not support these options; degrade step by step.
            body = resp.text.lower()
            if degraded == 0 and ("json_schema" in body or "response_format" in body or "strict" in body):
                payload["response_format"] = {"type": "json_object"}
                payload["messages"][0]["content"] = system + "\n\nJSON schema:\n" + json.dumps(schema)
            else:
                payload.pop("reasoning_effort", None)
            degraded += 1
            continue
        if resp.status_code == 429:
            raise LLMError("rate limited")
        if not resp.ok:
            raise LLMError(f"HTTP {resp.status_code}: {resp.text[:200]}")

        content = resp.json()["choices"][0]["message"].get("content") or ""
        try:
            match = re.search(r"\{.*\}", content, re.DOTALL)
            return model_cls.model_validate(json.loads(match.group(0) if match else content))
        except (ValueError, ValidationError) as exc:
            if repaired:
                raise LLMError(f"invalid JSON after repair: {exc}") from exc
            repaired = True
            payload["messages"] = messages + [
                {"role": "assistant", "content": content[:4000]},
                {"role": "user", "content": f"That reply did not match the schema ({str(exc)[:300]}). "
                                            "Reply again with only the corrected JSON object."},
            ]


# ---- features -------------------------------------------------------------------
def judge_relevance(topic: str, material: str, transcript: str) -> dict:
    words = material.split()
    if len(words) > MATERIAL_WORD_LIMIT:
        material = " ".join(words[:MATERIAL_WORD_LIMIT])
    user = judge.USER_TEMPLATE.format(topic=topic, material=material, transcript=transcript)
    result = _chat_json(judge.SYSTEM, user, "speech_relevance", judge.SCHEMA, Judgement, 1200)
    return {**result.cleaned(), "prompt_version": judge.VERSION, "model": settings.GROQ_LLM_MODEL}


def coach_feedback(results: dict) -> dict:
    user = coach.USER_TEMPLATE.format(results=json.dumps(results, ensure_ascii=False, indent=1))
    result = _chat_json(coach.SYSTEM, user, "coach_feedback", coach.SCHEMA, CoachFeedback, 1200)
    return {**result.cleaned(), "prompt_version": coach.VERSION, "model": settings.GROQ_LLM_MODEL}
