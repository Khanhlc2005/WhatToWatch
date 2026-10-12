"""Read-only catalog tools for factual and comparison questions."""

from app.schemas.chat import ChatHistoryMessage
from app.schemas.rag import AnswerMovie, MovieContext, RAGAnswer
from app.services.context_builder import build_context_for_movie_ids


def is_comparison(question: str) -> bool:
    return any(term in question.casefold() for term in ("so sánh", "khác nhau", "compare", "versus", " vs "))


def is_detail(question: str) -> bool:
    if any(term in question.casefold() for term in (
        "gợi ý", "đề xuất", "tìm phim", "recommend", "suggest", "phim có diễn viên", "phim do đạo diễn",
    )):
        return False
    return any(term in question.casefold() for term in (
        "đạo diễn", "diễn viên", "năm phát hành", "năm nào", "thời lượng",
        "điểm imdb", "rating", "thể loại", "director", "actor", "cast",
        "runtime", "release year", "genre", "nội dung", "tóm tắt", "plot", "summary",
    ))


def _selected_ids(question: str, context: list[MovieContext], history: list[ChatHistoryMessage]) -> list[int]:
    text = question.casefold()
    named = [int(movie.movie_id) for movie in context
             if movie.movie_id.isdecimal() and movie.title.casefold() in text]
    if any(term in text for term in ("phim đó", "phim này", "hai phim", "2 phim", "the movie", "those movies")):
        for turn in reversed(history):
            if turn.role == "assistant" and turn.movie_ids:
                return list(dict.fromkeys(named + turn.movie_ids))
    return named


def _catalog_movies(ids: list[int], context: list[MovieContext]) -> list[MovieContext]:
    hydrated = build_context_for_movie_ids(ids)
    by_id = {movie.movie_id: movie for movie in context}
    return [movie.model_copy(update={"genres": by_id[movie.movie_id].genres})
            if movie.movie_id in by_id else movie for movie in hydrated]


def _fact(question: str, movie: MovieContext) -> tuple[str, str] | None:
    text = question.casefold()
    if any(term in text for term in ("đạo diễn", "director")) and movie.director:
        return "đạo diễn", movie.director
    if any(term in text for term in ("diễn viên", "actor", "cast")) and movie.cast:
        return "diễn viên", ", ".join(movie.cast[:5])
    if any(term in text for term in ("năm phát hành", "năm nào", "release year")) and movie.year:
        return "năm phát hành", str(movie.year)
    if any(term in text for term in ("thời lượng", "runtime")) and movie.runtime_minutes:
        return "thời lượng", f"{movie.runtime_minutes} phút"
    if any(term in text for term in ("điểm imdb", "rating")) and movie.imdb_rating is not None:
        return "điểm IMDb", str(movie.imdb_rating)
    if any(term in text for term in ("thể loại", "genre")) and movie.genres:
        return "thể loại", ", ".join(movie.genres)
    if any(term in text for term in ("nội dung", "tóm tắt", "plot", "summary")) and movie.overview:
        return "nội dung", movie.overview
    return None


def answer_with_detail_tool(question: str, context: list[MovieContext], history: list[ChatHistoryMessage]) -> RAGAnswer:
    ids = _selected_ids(question, context, history)
    if len(ids) != 1:
        return RAGAnswer(status="insufficient_context", answer="Bạn muốn hỏi chi tiết phim nào?", movies=[])
    movies = _catalog_movies(ids, context)
    if not movies:
        return RAGAnswer(status="no_match", answer="Không tìm thấy phim này trong catalog hiện có.", movies=[])
    movie = movies[0]
    fact = _fact(question, movie)
    if fact is None:
        return RAGAnswer(status="insufficient_context", answer="Catalog chưa có dữ kiện cần hỏi về phim này.", movies=[])
    label, value = fact
    return RAGAnswer(
        status="answered", answer=f"{label.capitalize()} của {movie.title}: {value}.",
        movies=[AnswerMovie(movie_id=movie.movie_id, title=movie.title, reason=f"{label.capitalize()}: {value}")],
    )


def answer_with_comparison_tool(question: str, context: list[MovieContext], history: list[ChatHistoryMessage]) -> RAGAnswer:
    ids = _selected_ids(question, context, history)
    if len(ids) != 2:
        return RAGAnswer(status="insufficient_context", answer="Cần xác định đúng hai phim để so sánh.", movies=[])
    movies = _catalog_movies(ids, context)
    if len(movies) != 2:
        return RAGAnswer(status="no_match", answer="Không tìm thấy đủ hai phim trong catalog hiện có.", movies=[])
    labels = (("năm phát hành", "year"), ("thời lượng", "runtime_minutes"),
              ("đạo diễn", "director"), ("điểm IMDb", "imdb_rating"))
    comparable = [(label, getattr(movies[0], field), getattr(movies[1], field))
                  for label, field in labels if getattr(movies[0], field) is not None
                  and getattr(movies[1], field) is not None]
    if not comparable:
        return RAGAnswer(status="insufficient_context", answer="Catalog chưa có dữ kiện chung để so sánh hai phim.", movies=[])
    lines = [f"{label}: {movies[0].title} {left}; {movies[1].title} {right}."
             for label, left, right in comparable]
    return RAGAnswer(
        status="answered", answer=" ".join(lines),
        movies=[AnswerMovie(movie_id=movie.movie_id, title=movie.title,
                            reason=f"{comparable[0][0].capitalize()}: {comparable[0][index]}")
                for index, movie in enumerate(movies, start=1)],
    )
