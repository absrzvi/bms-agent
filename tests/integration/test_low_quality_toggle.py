"""Integration tests for T038: Low-quality search toggle implementation."""

import pytest

from tools.bms_search import Tools


class DummyResponse:
    """Simple response object to mimic requests.Response."""

    def __init__(self, status_code=200, json_data=None, text=""):
        self.status_code = status_code
        self._json = json_data or {"results": []}
        self.text = text

    def json(self):
        return self._json


@pytest.fixture()
def tool():
    return Tools()


def test_semantic_includes_toggle(monkeypatch, tool):
    """Ensure semantic search propagates include_low_quality flag."""
    captured_payload = {}

    def fake_post(url, json, timeout):
        captured_payload["url"] = url
        captured_payload["json"] = json
        captured_payload["timeout"] = timeout
        return DummyResponse(json_data={"results": []})

    monkeypatch.setattr("tools.bms_search.requests.post", fake_post)

    tool.search_semantic("maintenance procedures", include_low_quality=True)

    assert captured_payload["json"]["include_low_quality"] is True
    assert captured_payload["url"].endswith("/api/v1/search/semantic")


def test_hybrid_toggle_defaults_from_valves(monkeypatch, tool):
    """Verify hybrid search respects valve default when flag not provided."""
    tool.valves.INCLUDE_LOW_QUALITY = True
    captured_payload = {}

    def fake_post(url, json, timeout):
        captured_payload["json"] = json
        return DummyResponse(json_data={"results": []})

    monkeypatch.setattr("tools.bms_search.requests.post", fake_post)

    tool.search_hybrid("safety checklist")

    assert captured_payload["json"]["include_low_quality"] is True


def test_filters_preserved_with_toggle(monkeypatch, tool):
    """Ensure additional filters remain intact alongside toggle."""
    captured_payload = {}

    def fake_post(url, json, timeout):
        captured_payload["json"] = json
        return DummyResponse(json_data={"results": []})

    monkeypatch.setattr("tools.bms_search.requests.post", fake_post)

    tool.search_documents(
        "quality forms",
        search_type="semantic",
        filters={"document_type": "pdf"},
        include_low_quality=False,
    )

    payload = captured_payload["json"]
    assert payload["include_low_quality"] is False
    assert payload["filters"] == {"document_type": "pdf"}
