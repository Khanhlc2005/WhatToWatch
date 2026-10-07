import json
from pathlib import Path

import pytest

from app.schemas.rag import MovieContext, RAGAnswer
from app.services.rag import (
    RAGFormatError,
    RAGGroundingError,
    RAGInputError,
    answer_question,
    build_user_prompt,
    load_sample_context,
    parse_answer,
)


def _output(movie: MovieContext) -> str:
    return json.dumps({
        "status": "answered",
        "answer": "Phim này có chủ đề du hành không gian trong dữ liệu được cung cấp.",
        "movies": [{"movie_id": movie.movie_id, "title": movie.title, "reason": movie.genres[0]}],
    })


def test_sample_context_matches_checked_in_source() -> None:
    source = Path(__file__).resolve().parents[2] / "data" / "seeds" / "movies_cleaned_sample.jsonl"
    rows = [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines()]
    samples = load_sample_context()
    assert len(samples) == len(rows) == 3
    for movie, row in zip(samples, rows):
        assert movie.movie_id == f"tmdb:{row['tmdb_id']}"
        assert movie.title == row["title"]
        assert movie.overview == row["overview"]
        assert movie.director == row["directors"][0]["name"]
        assert movie.genres == [item["name"] for item in row["genres"]]


def test_prompt_contains_question_and_exact_context() -> None:
    movie = load_sample_context()[0]
    prompt = build_user_prompt("Ai đạo diễn phim này?", [movie])
    assert "Ai đạo diễn phim này?" in prompt
    assert movie.movie_id in prompt
    assert movie.director in prompt


def test_ollama_schema_requires_all_output_fields() -> None:
    assert set(RAGAnswer.model_json_schema()["required"]) == {"status", "answer", "movies"}


def test_valid_answer_is_parsed_and_grounded() -> None:
    movie = load_sample_context()[2]
    result = parse_answer("```json\n" + _output(movie) + "\n```", [movie])
    assert result.status == "answered"
    assert result.movies[0].movie_id == "tmdb:157336"


@pytest.mark.parametrize("raw", [
    "not json",
    '{"status":"answered","answer":"ok","movies":[]}',
    '{"status":"no_match","answer":"none","movies":[{"movie_id":"x","title":"x","reason":"x"}]}',
    '{"status":"no_match","answer":"none","movies":[],"unexpected":true}',
    '{"status":"no_match","answer":"none","answer":"duplicate","movies":[]}',
])
def test_malformed_model_output_fails_closed(raw: str) -> None:
    with pytest.raises(RAGFormatError):
        parse_answer(raw, load_sample_context())


def test_unknown_movie_or_mismatched_title_is_rejected() -> None:
    context = load_sample_context()
    for changed in (
        _output(context[0]).replace(context[0].movie_id, "tmdb:999"),
        _output(context[0]).replace(context[0].title, "Invented film"),
    ):
        with pytest.raises(RAGGroundingError):
            parse_answer(changed, context)


def test_fallback_and_malformed_answer_text_are_normalized() -> None:
    movie = load_sample_context()[2]
    no_match = parse_answer(
        '{"status":"no_match","answer":"no_match only","movies":[]}', [movie]
    )
    assert no_match.answer.startswith("Không tìm thấy")
    payload = json.loads(_output(movie))
    payload["answer"] = "movies: [{movie_id: tmdb:157336}]"
    answered = parse_answer(json.dumps(payload), [movie])
    assert answered.answer.startswith("Mình tìm thấy")


def test_invalid_first_response_is_retried_once() -> None:
    movie = load_sample_context()[2]
    replies = iter(['{"status":"answered","answer":"wrong","movies":[]}', _output(movie)])
    prompts = []

    def generate(prompt: str, system: str) -> str:
        prompts.append(prompt)
        return next(replies)

    result = answer_question("Gợi ý phim không gian", [movie], generate)
    assert result.movies[0].movie_id == movie.movie_id
    assert len(prompts) == 2
    assert "previous response failed" in prompts[1]


def test_empty_context_returns_fallback_without_calling_model() -> None:
    def unexpected_call(prompt: str, system: str) -> str:
        raise AssertionError("model should not be called")

    result = answer_question("Gợi ý phim khoa học viễn tưởng", [], unexpected_call)
    assert result.status == "insufficient_context"
    assert result.movies == []


def test_sparse_context_returns_insufficient_without_calling_model() -> None:
    movie = MovieContext(movie_id="custom:1", title="Unknown Film")

    def unexpected_call(prompt: str, system: str) -> str:
        raise AssertionError("model should not be called for missing facts")

    result = answer_question("Ai đạo diễn phim này?", [movie], unexpected_call)
    assert result.status == "insufficient_context"
    assert result.movies == []


def test_duplicate_context_ids_are_input_errors() -> None:
    movie = load_sample_context()[0]
    with pytest.raises(RAGInputError):
        answer_question("Gợi ý phim", [movie, movie], lambda *_: "")


def test_selected_movie_without_requested_fact_is_retried_then_rejected() -> None:
    with_director = load_sample_context()[0]
    without_director = MovieContext(
        movie_id="custom:1", title="Unknown Film", genres=["Drama"]
    )
    model_reply = json.dumps({
        "status": "answered", "answer": "Không có dữ kiện đáng tin cậy.",
        "movies": [{"movie_id": "custom:1", "title": "Unknown Film", "reason": "Drama"}],
    })
    calls = []

    def generate(prompt: str, system: str) -> str:
        calls.append(prompt)
        return model_reply

    with pytest.raises(RAGGroundingError):
        answer_question("Ai đạo diễn phim này?", [with_director, without_director], generate)
    assert len(calls) == 2


def test_public_answer_and_reason_are_derived_from_context() -> None:
    movie = load_sample_context()[2]
    model_reply = json.dumps({
        "status": "answered",
        "answer": "Watch The Matrix instead.",
        "movies": [{
            "movie_id": movie.movie_id,
            "title": movie.title,
            "reason": "The Matrix is better.",
        }],
    })
    result = answer_question("Gợi ý phim khoa học viễn tưởng", [movie], lambda *_: model_reply)
    assert "The Matrix" not in result.model_dump_json()
    assert result.movies[0].title == "Interstellar"
    assert "Science Fiction" in result.movies[0].reason


def test_no_matching_film_returns_empty_list() -> None:
    result = answer_question(
        "Có phim hài lãng mạn nào không?",
        load_sample_context(),
        lambda prompt, system: json.dumps({
            "status": "no_match", "answer": "Không có phim phù hợp trong ngữ cảnh hiện có.", "movies": []
        }),
    )
    assert result.status == "no_match"
    assert result.movies == []
