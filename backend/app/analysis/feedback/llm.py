"""Minimal LLM client (standard library only) for the optional wording pass.

Off by default. Configure with environment variables (never hard-code keys):

    SPEAKWISE_LLM_API_KEY    required
    SPEAKWISE_LLM_MODEL      required, e.g. a model id from your provider
    SPEAKWISE_LLM_PROVIDER   "openai" (default; any OpenAI-compatible /chat/completions
                             endpoint, including local servers) or "anthropic"
    SPEAKWISE_LLM_BASE_URL   optional override, e.g. http://localhost:11434/v1

PRIVACY: when enabled, the transcript and metrics of the session are sent to the
configured provider. Leave the variables unset to keep everything local.
"""
import json
import os
import re
import urllib.error
import urllib.request
from typing import Optional


class LLMError(Exception):
    pass


class LLMClient:
    def __init__(self, provider: str, api_key: str, model: str,
                 base_url: Optional[str] = None, timeout: float = 60.0):
        if provider not in ("openai", "anthropic"):
            raise ValueError(f"Unknown LLM provider '{provider}' (use 'openai' or 'anthropic').")
        self.provider, self.api_key, self.model = provider, api_key, model
        self.timeout = timeout
        default = "https://api.anthropic.com/v1" if provider == "anthropic" else "https://api.openai.com/v1"
        self.base_url = (base_url or default).rstrip("/")

    def _post(self, url: str, headers: dict, body: dict) -> dict:
        req = urllib.request.Request(
            url, data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json", **headers}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")[:300]
            raise LLMError(f"LLM request failed ({exc.code}): {detail}") from exc
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise LLMError(f"LLM request failed: {exc}") from exc

    def complete(self, system: str, user: str) -> str:
        if self.provider == "anthropic":
            data = self._post(
                f"{self.base_url}/messages",
                {"x-api-key": self.api_key, "anthropic-version": "2023-06-01"},
                {"model": self.model, "max_tokens": 1500, "temperature": 0.3, "system": system,
                 "messages": [{"role": "user", "content": user}]})
            try:
                return data["content"][0]["text"]
            except (KeyError, IndexError, TypeError) as exc:
                raise LLMError("Unexpected response shape from Anthropic.") from exc
        data = self._post(
            f"{self.base_url}/chat/completions",
            {"Authorization": f"Bearer {self.api_key}"},
            {"model": self.model, "temperature": 0.3,
             "response_format": {"type": "json_object"},
             "messages": [{"role": "system", "content": system},
                          {"role": "user", "content": user}]})
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMError("Unexpected response shape from the LLM endpoint.") from exc


def from_env() -> Optional[LLMClient]:
    key, model = os.getenv("SPEAKWISE_LLM_API_KEY"), os.getenv("SPEAKWISE_LLM_MODEL")
    if not key or not model:
        return None
    return LLMClient(os.getenv("SPEAKWISE_LLM_PROVIDER", "openai").lower(), key, model,
                     os.getenv("SPEAKWISE_LLM_BASE_URL"))


def extract_json(text: str) -> dict:
    """Parse the first JSON object in a model reply (tolerates code fences / chatter)."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise LLMError("The model reply contained no JSON object.")
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError as exc:
            raise LLMError(f"The model reply was not valid JSON: {exc}") from exc
