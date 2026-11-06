import pytest

from app.schemas.chat import ChatHistoryMessage
from app.schemas.rag import MovieContext
from app.services import chat_tools

MOVIES = [
    MovieContext(movie_id="1", title="Film One", year=2010, director="A Director", runtime_minutes=100),
    MovieContext(movie_id="2", title="Film Two", year=2020, director="B Director", runtime_minutes=120),
]


@pytest.fixture(autouse=True)
def title_catalog(monkeypatch) -> None:
    def lookup(title):
        return [{"id": int(movie.movie_id), "title": movie.title, "originalTitle": None,
                 "releaseYear": movie.year}
                for movie in MOVIES if movie.title.casefold() == title.casefold()]

    monkeypatch.setattr(chat_tools, "find_exact_movie_titles", lookup)
    monkeypatch.setattr(chat_tools, "find_similar_titles", lambda title: [])


def test_detail_tool_reads_canonical_catalog_and_never_uses_model(monkeypatch) -> None:
    monkeypatch.setattr(chat_tools, "build_context_for_movie_ids", lambda ids: [MOVIES[0]])
    history = [ChatHistoryMessage(role="assistant", content="Film One", movie_ids=[1])]
    result = chat_tools.answer_with_detail_tool("Phim đó phát hành năm nào?", MOVIES, history)
    assert result.status == "answered"
    assert result.movies[0].movie_id == "1"
    assert "2010" in result.answer
    assert result.answer.startswith("Release year")


def test_compare_tool_requires_two_known_movies(monkeypatch) -> None:
    monkeypatch.setattr(chat_tools, "build_context_for_movie_ids", lambda ids: MOVIES)
    result = chat_tools.answer_with_comparison_tool("So sánh Film One và Film Two", MOVIES, [])
    assert result.status == "answered"
    assert [movie.movie_id for movie in result.movies] == ["1", "2"]
    assert "2010" in result.answer and "2020" in result.answer
    assert result.answer.startswith("Release year")


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


def test_compare_resolves_titles_missing_from_retrieval_context(monkeypatch) -> None:
    calls = []

    def hydrate(ids):
        calls.append(ids)
        return [MOVIES[0], MOVIES[1]]

    monkeypatch.setattr(chat_tools, "build_context_for_movie_ids", hydrate)
    result = chat_tools.answer_with_comparison_tool("Compare Film One and Film Two", [MOVIES[0]], [])
    assert calls == [[1, 2]]
    assert [movie.movie_id for movie in result.movies] == ["1", "2"]


def test_compare_recognizes_titles_before_comparison_phrase(monkeypatch) -> None:
    monkeypatch.setattr(chat_tools, "build_context_for_movie_ids", lambda ids: MOVIES)
    result = chat_tools.answer_with_comparison_tool("Film One và Film Two khác nhau thế nào?", [], [])
    assert [movie.movie_id for movie in result.movies] == ["1", "2"]


def test_compare_recognizes_with_connector(monkeypatch) -> None:
    monkeypatch.setattr(chat_tools, "build_context_for_movie_ids", lambda ids: MOVIES)
    result = chat_tools.answer_with_comparison_tool("Compare Film One with Film Two", [], [])
    assert [movie.movie_id for movie in result.movies] == ["1", "2"]


def test_compare_does_not_confuse_nested_titles(monkeypatch) -> None:
    movies = [
        MovieContext(movie_id="10", title="The Matrix", year=1999),
        MovieContext(movie_id="11", title="The Matrix Reloaded", year=2003),
    ]
    monkeypatch.setattr(chat_tools, "find_exact_movie_titles", lambda title: [
        {"id": int(movie.movie_id), "title": movie.title, "originalTitle": None, "releaseYear": movie.year}
        for movie in movies if movie.title.casefold() == title.casefold()
    ])
    monkeypatch.setattr(chat_tools, "build_context_for_movie_ids", lambda ids: [
        next(movie for movie in movies if movie.movie_id == str(movie_id)) for movie_id in ids
    ])
    result = chat_tools.answer_with_comparison_tool("The Matrix vs. The Matrix Reloaded", [], [])
    assert [movie.movie_id for movie in result.movies] == ["10", "11"]


def test_compare_requires_year_for_ambiguous_title(monkeypatch) -> None:
    monkeypatch.setattr(chat_tools, "find_exact_movie_titles", lambda title: (
        [{"id": 1, "title": "Film One", "releaseYear": 2000},
         {"id": 3, "title": "Film One", "releaseYear": 2020}]
        if title == "Film One" else [{"id": 2, "title": "Film Two", "releaseYear": 2010}]
    ))
    monkeypatch.setattr(chat_tools, "build_context_for_movie_ids", lambda ids: [
        MovieContext(movie_id=str(movie_id), title="Film One" if movie_id != 2 else "Film Two",
                     year=2020 if movie_id == 3 else 2010)
        for movie_id in ids
    ])
    ambiguous = chat_tools.answer_with_comparison_tool("Compare Film One and Film Two", [], [])
    assert ambiguous.status == "insufficient_context"
    disambiguated = chat_tools.answer_with_comparison_tool("Compare Film One (2020) and Film Two", [], [])
    assert [movie.movie_id for movie in disambiguated.movies] == ["3", "2"]


def test_compare_follow_up_uses_exactly_two_prior_movie_ids(monkeypatch) -> None:
    monkeypatch.setattr(chat_tools, "build_context_for_movie_ids", lambda ids: MOVIES)
    history = [ChatHistoryMessage(role="assistant", content="Two films", movie_ids=[1, 2])]
    result = chat_tools.answer_with_comparison_tool("So sánh hai phim đó", [], history)
    assert [movie.movie_id for movie in result.movies] == ["1", "2"]


def _fuzzy(monkeypatch, candidates) -> None:
    monkeypatch.setattr(chat_tools, "find_similar_titles", lambda title: candidates)
    monkeypatch.setattr(chat_tools, "build_context_for_movie_ids", lambda ids: [
        MovieContext(movie_id=str(i), title=f"Movie {i}", year=2000 + i) for i in ids])


def test_compare_matches_title_typed_without_spaces(monkeypatch) -> None:
    _fuzzy(monkeypatch, [{"id": 7, "title": "La La Land"}, {"id": 8, "title": "Landscape"}])
    ids, ask = chat_tools._comparison_ids("compare Film One and lalaland", [])
    assert ids == [1, 7] and ask is None


def test_compare_ignores_punctuation_and_case(monkeypatch) -> None:
    _fuzzy(monkeypatch, [{"id": 9, "title": "Spider-Man: Homecoming"}])
    ids, _ = chat_tools._comparison_ids("compare Film Two and SPIDERMAN homecoming", [])
    assert ids == [2, 9]


def test_compare_accepts_small_typo_when_clearly_ahead(monkeypatch) -> None:
    _fuzzy(monkeypatch, [{"id": 5, "title": "Interstellar"}, {"id": 6, "title": "Interstitial Zone"}])
    ids, _ = chat_tools._comparison_ids("compare Film One and intersteller", [])
    assert ids == [1, 5]


def test_compare_asks_again_when_fuzzy_titles_tie(monkeypatch) -> None:
    _fuzzy(monkeypatch, [{"id": 3, "title": "Dune"}, {"id": 4, "title": "Dune"}])
    result = chat_tools.answer_with_comparison_tool("compare Film One and dune", MOVIES, [])
    assert result.status == "insufficient_context" and result.movies == []
    assert "Which movie did you mean" in result.answer and "Dune" in result.answer


def test_compare_asks_again_when_only_weak_matches(monkeypatch) -> None:
    _fuzzy(monkeypatch, [{"id": 3, "title": "Inception"}])
    ids, ask = chat_tools._comparison_ids("compare Film One and incestion zzz", [])
    assert ids == []


def test_compare_never_guesses_unrelated_title(monkeypatch) -> None:
    _fuzzy(monkeypatch, [{"id": 3, "title": "Casablanca"}])
    ids, ask = chat_tools._comparison_ids("compare Film One and xyzzy", [])
    assert ids == [] and ask is None
