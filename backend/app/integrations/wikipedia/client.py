"""Small, polite Wikipedia API client (Action API + REST).

- One pooled httpx client per process, descriptive User-Agent (Wikimedia policy).
- Retries with backoff on network errors, 5xx, 429 and `maxlag`.
- Circuit breaker: after repeated failures, calls fail fast for a cool-down period so a
  Wikipedia outage doesn't stall every request (callers fall back to cached data).
"""
import logging
import re
import threading
import time
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger("speakwise.wikipedia")

SUPPORTED_LANGS = ("en", "simple")
MAX_TITLES_PER_QUERY = 50


class WikipediaError(Exception):
    """Wikipedia returned an unusable response."""


class WikipediaUnavailable(WikipediaError):
    """Wikipedia couldn't be reached (or the circuit breaker is open)."""


@dataclass(frozen=True)
class SearchHit:
    title: str
    page_id: int
    word_count: int
    snippet: str  # plain text (search highlight markup removed)


@dataclass(frozen=True)
class PageInfo:
    requested_title: str
    title: str  # canonical title after normalization/redirects
    page_id: int
    revision_id: int
    description: str | None
    is_disambiguation: bool
    simple_title: str | None  # Simple English equivalent (from langlinks), if asked for
    length: int = 0           # page size in bytes of wikitext (~7 bytes per word of prose)


@dataclass(frozen=True)
class ArticleText:
    title: str
    page_id: int
    revision_id: int
    description: str | None
    extract: str


def article_url(lang: str, title: str) -> str:
    return f"https://{lang}.wikipedia.org/wiki/{title.replace(' ', '_')}"


class _CircuitBreaker:
    def __init__(self, threshold: int = 5, cooldown_seconds: float = 60.0):
        self.threshold = threshold
        self.cooldown = cooldown_seconds
        self._failures = 0
        self._open_until = 0.0
        self._lock = threading.Lock()

    def check(self) -> None:
        with self._lock:
            if time.monotonic() < self._open_until:
                raise WikipediaUnavailable("Wikipedia is temporarily unavailable (circuit open)")

    def success(self) -> None:
        with self._lock:
            self._failures = 0

    def failure(self) -> None:
        with self._lock:
            self._failures += 1
            if self._failures >= self.threshold:
                self._open_until = time.monotonic() + self.cooldown
                self._failures = 0
                logger.warning("Wikipedia circuit opened for %.0fs", self.cooldown)


class WikipediaClient:
    def __init__(
        self,
        user_agent: str,
        timeout: float = 8.0,
        retries: int = 2,
        transport: httpx.BaseTransport | None = None,
    ):
        self._http = httpx.Client(
            headers={"User-Agent": user_agent, "Accept-Encoding": "gzip"},
            timeout=timeout,
            follow_redirects=True,
            transport=transport,
        )
        self._retries = retries
        self._breaker = _CircuitBreaker()

    # ---- transport ----

    def _get(self, url: str, params: dict[str, Any] | None = None) -> dict[str, Any] | None:
        """GET JSON with retries. Returns None for 404 (missing page)."""
        self._breaker.check()
        last_error: Exception | None = None

        for attempt in range(self._retries + 1):
            if attempt:
                time.sleep(0.5 * 3 ** (attempt - 1))  # 0.5s, 1.5s
            try:
                response = self._http.get(url, params=params)
                if response.status_code == 404:
                    self._breaker.success()
                    return None
                if response.status_code == 429 or response.status_code >= 500:
                    last_error = WikipediaUnavailable(f"HTTP {response.status_code}")
                    continue
                response.raise_for_status()
                data = response.json()
                error = data.get("error") if isinstance(data, dict) else None
                if error and error.get("code") == "maxlag":
                    last_error = WikipediaUnavailable("maxlag")
                    continue
                if error:
                    raise WikipediaError(f"{error.get('code')}: {error.get('info')}")
                self._breaker.success()
                return data
            except (httpx.TransportError, ValueError) as exc:  # network error / bad JSON
                last_error = exc

        self._breaker.failure()
        raise WikipediaUnavailable(f"Wikipedia request failed: {last_error}") from last_error

    def _action(self, lang: str, params: dict[str, Any]) -> dict[str, Any]:
        if lang not in SUPPORTED_LANGS:
            raise ValueError(f"Unsupported Wikipedia language: {lang}")
        data = self._get(
            f"https://{lang}.wikipedia.org/w/api.php",
            {"format": "json", "formatversion": 2, "maxlag": 5, **params},
        )
        if data is None:
            raise WikipediaError("Unexpected 404 from the Action API")
        return data

    # ---- API ----

    def search(self, lang: str, query: str, limit: int = 8) -> tuple[list[SearchHit], str | None]:
        """Full-text search. Returns (hits in relevance order, "did you mean" suggestion)."""
        data = self._action(
            lang,
            {
                "action": "query",
                "list": "search",
                "srsearch": query,
                "srlimit": limit,
                "srinfo": "suggestion",
                "srprop": "wordcount|snippet",
            },
        )
        query_data = data.get("query", {})
        hits = [
            SearchHit(
                title=hit["title"],
                page_id=hit["pageid"],
                word_count=hit.get("wordcount", 0),
                snippet=_strip_tags(hit.get("snippet", "")),
            )
            for hit in query_data.get("search", [])
        ]
        return hits, query_data.get("searchinfo", {}).get("suggestion")

    def related(self, lang: str, title: str, limit: int = 5) -> list[SearchHit]:
        """Articles similar to `title` (CirrusSearch morelike). No quotes: quoting returns nothing."""
        hits, _ = self.search(lang, f"morelike:{title}", limit)
        return hits

    def page_info(
        self, lang: str, titles: list[str], with_simple_title: bool = False
    ) -> dict[str, PageInfo]:
        """Resolve titles (following redirects) in batches. Missing pages are left out.

        Returns {requested_title: PageInfo}.
        """
        results: dict[str, PageInfo] = {}

        for start in range(0, len(titles), MAX_TITLES_PER_QUERY):
            batch = titles[start:start + MAX_TITLES_PER_QUERY]
            props = "info|pageprops|description" + ("|langlinks" if with_simple_title else "")
            params: dict[str, Any] = {
                "action": "query",
                "prop": props,
                "redirects": 1,
                "titles": "|".join(batch),
                "ppprop": "disambiguation",
            }
            if with_simple_title:
                params.update({"lllang": "simple", "lllimit": "max"})
            data = self._action(lang, params)
            query = data.get("query", {})

            # Map each requested title through normalization and redirects to its final title.
            renamed = {n["from"]: n["to"] for n in query.get("normalized", [])}
            redirects = {r["from"]: r["to"] for r in query.get("redirects", [])}
            pages = {p["title"]: p for p in query.get("pages", []) if not p.get("missing")}

            for requested in batch:
                final = renamed.get(requested, requested)
                final = redirects.get(final, final)
                page = pages.get(final)
                if not page or "pageid" not in page:
                    continue
                langlinks = page.get("langlinks", [])
                results[requested] = PageInfo(
                    requested_title=requested,
                    title=page["title"],
                    page_id=page["pageid"],
                    revision_id=page.get("lastrevid", 0),
                    description=page.get("description"),
                    is_disambiguation="disambiguation" in page.get("pageprops", {}),
                    simple_title=langlinks[0]["title"] if langlinks else None,
                    length=page.get("length", 0),
                )

        return results

    def article_text(self, lang: str, title: str) -> ArticleText | None:
        """Full plain-text article (one page per request; the API can't batch full extracts)."""
        data = self._action(
            lang,
            {
                "action": "query",
                "prop": "extracts|info|description",
                "explaintext": 1,
                "exsectionformat": "wiki",
                "redirects": 1,
                "titles": title,
            },
        )
        pages = data.get("query", {}).get("pages", [])
        page = pages[0] if pages else None
        if not page or page.get("missing") or not page.get("extract"):
            return None
        return ArticleText(
            title=page["title"],
            page_id=page["pageid"],
            revision_id=page.get("lastrevid", 0),
            description=page.get("description"),
            extract=page["extract"],
        )


def _strip_tags(html: str) -> str:
    return re.sub(r"<[^>]+>", "", html).replace("&quot;", '"').replace("&amp;", "&").strip()


@lru_cache(maxsize=1)
def get_wikipedia_client() -> WikipediaClient:
    """Shared client (connection pool + circuit breaker) for the whole process."""
    return WikipediaClient(settings.WIKIPEDIA_USER_AGENT)
