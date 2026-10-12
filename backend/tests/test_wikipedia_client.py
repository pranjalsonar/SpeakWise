import httpx
import pytest

from app.integrations.wikipedia import client as client_module
from app.integrations.wikipedia.client import WikipediaClient, WikipediaUnavailable


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    monkeypatch.setattr(client_module.time, "sleep", lambda _seconds: None)


def make_client(handler):
    return WikipediaClient("SpeakWise-tests/1.0", transport=httpx.MockTransport(handler))


def test_page_info_follows_normalization_and_redirects_and_flags_disambiguation():
    def handler(request):
        return httpx.Response(200, json={"query": {
            "normalized": [{"from": "remote work", "to": "Remote work"}],
            "redirects": [{"from": "AI in education", "to": "Artificial intelligence in education"}],
            "pages": [
                {"title": "Remote work", "pageid": 1, "lastrevid": 10, "description": "Working away"},
                {"title": "Artificial intelligence in education", "pageid": 2, "lastrevid": 20},
                {"title": "Mercury", "pageid": 3, "lastrevid": 30, "pageprops": {"disambiguation": ""}},
                {"title": "Nope", "missing": True},
            ],
        }})

    infos = make_client(handler).page_info("en", ["remote work", "AI in education", "Mercury", "Nope"])
    assert infos["remote work"].title == "Remote work"
    assert infos["remote work"].description == "Working away"
    assert infos["AI in education"].page_id == 2
    assert infos["Mercury"].is_disambiguation is True
    assert "Nope" not in infos


def test_user_agent_is_sent():
    seen = {}

    def handler(request):
        seen["ua"] = request.headers["user-agent"]
        return httpx.Response(200, json={"query": {"search": [], "searchinfo": {}}})

    make_client(handler).search("en", "anything")
    assert seen["ua"] == "SpeakWise-tests/1.0"


def test_retries_server_errors_then_succeeds():
    calls = {"n": 0}

    def handler(request):
        calls["n"] += 1
        if calls["n"] < 3:
            return httpx.Response(503)
        return httpx.Response(200, json={"query": {"search": [
            {"title": "Remote work", "pageid": 1, "wordcount": 9000, "snippet": "<span>Remote</span> work"}
        ], "searchinfo": {"suggestion": "remote working"}}})

    hits, suggestion = make_client(handler).search("en", "remote wrk")
    assert calls["n"] == 3
    assert hits[0].snippet == "Remote work"
    assert suggestion == "remote working"


def test_circuit_opens_after_repeated_failures():
    calls = {"n": 0}

    def handler(request):
        calls["n"] += 1
        raise httpx.ConnectError("down")

    client = make_client(handler)
    for _ in range(5):
        with pytest.raises(WikipediaUnavailable):
            client.search("en", "x")
    calls_before = calls["n"]
    with pytest.raises(WikipediaUnavailable, match="circuit open"):
        client.search("en", "x")
    assert calls["n"] == calls_before  # failed fast, no network call


def test_related_uses_unquoted_morelike_query():
    seen = {}

    def handler(request):
        seen["srsearch"] = request.url.params["srsearch"]
        return httpx.Response(200, json={"query": {"search": [], "searchinfo": {}}})

    make_client(handler).related("en", "Car-free city")
    assert seen["srsearch"] == "morelike:Car-free city"


def test_missing_article_text_returns_none():
    def handler(request):
        return httpx.Response(200, json={"query": {"pages": [{"title": "Nope", "missing": True}]}})

    assert make_client(handler).article_text("en", "Nope") is None
