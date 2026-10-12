import pytest

from app.services import reranker


def test_score_pairs_uses_query_document_pairs(monkeypatch):
    class FakeModel:
        def compute_score(self, pairs, **kwargs):
            assert pairs == [["query", "title one"], ["query", "title two"]]
            assert kwargs["batch_size"] == 8
            return [2.0, -1.0]
    monkeypatch.setattr(reranker, "get_reranker", lambda: FakeModel())
    assert reranker.score_pairs("query", ["title one", "title two"]) == [2.0, -1.0]


def test_score_pairs_rejects_invalid_scores(monkeypatch):
    class FakeModel:
        def compute_score(self, *_args, **_kwargs):
            return [float("nan")]
    monkeypatch.setattr(reranker, "get_reranker", lambda: FakeModel())
    with pytest.raises(ValueError, match="Invalid reranker scores"):
        reranker.score_pairs("query", ["movie"])
    assert reranker.score_pairs("query", []) == []
