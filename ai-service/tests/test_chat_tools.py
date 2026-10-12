from app.schemas.chat import ChatHistoryMessage
from app.schemas.rag import MovieContext
from app.services import chat_tools

MOVIES = [
    MovieContext(movie_id="1", title="Film One", year=2010, director="A Director", runtime_minutes=100),
    MovieContext(movie_id="2", title="Film Two", year=2020, director="B Director", runtime_minutes=120),
]


def test_detail_tool_reads_canonical_catalog_and_never_uses_model(monkeypatch) -> None:
    monkeypatch.setattr(chat_tools, "build_context_for_movie_ids", lambda ids: [MOVIES[0]])
    history = [ChatHistoryMessage(role="assistant", content="Film One", movie_ids=[1])]
    result = chat_tools.answer_with_detail_tool("Phim đó phát hành năm nào?", MOVIES, history)
    assert result.status == "answered"
    assert result.movies[0].movie_id == "1"
    assert "2010" in result.answer


def test_compare_tool_requires_two_known_movies(monkeypatch) -> None:
    monkeypatch.setattr(chat_tools, "build_context_for_movie_ids", lambda ids: MOVIES)
    result = chat_tools.answer_with_comparison_tool("So sánh Film One và Film Two", MOVIES, [])
    assert result.status == "answered"
    assert [movie.movie_id for movie in result.movies] == ["1", "2"]
    assert "2010" in result.answer and "2020" in result.answer


def test_compare_tool_does_not_guess_missing_second_movie() -> None:
    result = chat_tools.answer_with_comparison_tool("So sánh Film One với phim khác", MOVIES, [])
    assert result.status == "insufficient_context"
    assert result.movies == []


def test_compare_can_combine_named_movie_with_previous_recommendation(monkeypatch) -> None:
    monkeypatch.setattr(chat_tools, "build_context_for_movie_ids", lambda ids: [MOVIES[1], MOVIES[0]])
    history = [ChatHistoryMessage(role="assistant", content="Film One", movie_ids=[1])]
    result = chat_tools.answer_with_comparison_tool("So sánh Film Two với phim đó", MOVIES, history)
    assert result.status == "answered"
    assert [movie.movie_id for movie in result.movies] == ["2", "1"]
