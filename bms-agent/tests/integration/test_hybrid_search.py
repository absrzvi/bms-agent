"""Tests for `DocumentProcessorWrapper.hybrid_search` scoring."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Dict, List

import pytest

from api.processor_wrapper import DocumentProcessorWrapper


class FakeSearchResult:
    def __init__(self, id_: str, score: float, payload: Dict[str, Any]):
        self.id = id_
        self.score = score
        self.payload = payload


class FakeQdrant:
    def __init__(self, results: List[FakeSearchResult]):
        self._results = results

    def search(self, *_, **__):
        return self._results


def make_wrapper(results: List[FakeSearchResult]) -> DocumentProcessorWrapper:
    wrapper = DocumentProcessorWrapper.__new__(DocumentProcessorWrapper)
    wrapper.config = SimpleNamespace(vector_weight=0.7, keyword_weight=0.3)
    wrapper.embedding_model = "snowflake-arctic-embed2"
    wrapper.collection_name = "nomad_bms_documents"
    wrapper.qdrant = FakeQdrant(results)

    async def _fake_embedding(_text: str) -> List[float]:
        return [0.0]

    wrapper.get_embedding = _fake_embedding  # type: ignore[assignment]
    return wrapper


@pytest.mark.asyncio
async def test_hybrid_search_combines_dense_and_keyword_scores():
    results = [
        FakeSearchResult(
            "chunk-1",
            score=0.9,
            payload={
                "term_frequencies": {
                    "emergency": 0.4,
                    "brake": 0.3,
                    "vlan": 0.2,
                }
            },
        ),
        FakeSearchResult(
            "chunk-2",
            score=0.85,
            payload={"term_frequencies": {"vlan": 0.05}},
        ),
    ]
    wrapper = make_wrapper(results)

    response = await wrapper.hybrid_search("emergency brake vlan", limit=2, vector_weight=0.6, keyword_weight=0.4)

    assert response["count"] == 2
    first = response["results"][0]
    expected_keyword = 0.4 + 0.3 + 0.2
    assert pytest.approx(first["keyword_score"], rel=1e-6) == expected_keyword
    expected_combined = 0.6 * 0.9 + 0.4 * expected_keyword
    assert pytest.approx(first["combined_score"], rel=1e-6) == expected_combined
    assert first["combined_score"] >= response["results"][1]["combined_score"]


@pytest.mark.asyncio
async def test_hybrid_search_handles_no_matches():
    wrapper = make_wrapper([])
    response = await wrapper.hybrid_search("no overlap", limit=2)

    assert response["count"] == 0
    assert response["results"] == []
