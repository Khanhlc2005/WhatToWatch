"""Read-only catalog tools for factual and comparison questions."""

import logging
import re
import unicodedata
from difflib import SequenceMatcher

from app.schemas.chat import ChatHistoryMessage
from app.schemas.rag import AnswerMovie, MovieContext, RAGAnswer
from app.schemas.retrieval import MovieSearchRequest
from app.services.context_builder import (
    build_context_for_movie_ids,
    find_exact_movie_titles,
)
from app.services.retrieval import search_movies

logger = logging.getLogger(__name__)

# A fuzzy title is accepted only when it is very close and clearly ahead of the runner-up;
# anything weaker or tied is returned to the user as a question.
FUZZY_ACCEPT_RATIO = 0.85
FUZZY_MARGIN = 0.08
FUZZY_SUGGEST_RATIO = 0.7
FUZZY_SUGGESTIONS = 3

COMPARISON_LINK = re.compile(r"\s+(?:so với|versus|vs\.?|and|và|với|with|to|against)\s+", re.IGNORECASE)
COMPARISON_START = re.compile(
    r"(?:so sánh|compare|đối chiếu|difference between|khác nhau giữa)", re.IGNORECASE,
)
SINGLE_REFERENCE = {"phim đó", "phim này", "bộ phim đó", "bộ phim này", "that movie",
                    "this movie", "that film", "this film", "the previous movie"}


def is_comparison(question: str) -> bool:
    text = question.casefold()
    return any(term in text for term in ("so sánh", "khác nhau", "compare", "versus", "so với", "difference between")) \
        or re.search(r"(?<!\w)vs\.?(?!\w)", text) is not None


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


def _latest_movie_ids(history: list[ChatHistoryMessage]) -> list[int]:
    for turn in reversed(history):
        if turn.role == "assistant" and turn.movie_ids:
            return list(dict.fromkeys(turn.movie_ids))
    return []


def _title_key(title: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", title).casefold().split())


def _title_variants(fragment: str) -> list[tuple[str, int | None]]:
    clean = fragment.strip().strip(' ?!"“”')
    clean = re.sub(r"\s+(?:for me|giúp tôi|how are they different|khác nhau thế nào)\s*$", "", clean, flags=re.IGNORECASE)
    variants = [clean]
    if clean.endswith("."):
        variants.append(clean[:-1].rstrip())
    without_prefix = re.sub(r"^(?:between|giữa|bộ phim|phim|movie)\s+", "", clean, flags=re.IGNORECASE)
    if without_prefix != clean:
        variants.append(without_prefix)
    result = []
    for value in variants:
        year = re.search(r"\s*\((\d{4})\)$", value)
        if year:
            value = value[:year.start()].rstrip()
        if 1 < len(value) <= 500 and (value, int(year[1]) if year else None) not in result:
            result.append((value, int(year[1]) if year else None))
    return result


def _compact_key(text: str) -> str:
    """Casefolded title with spaces and punctuation removed, so "lalaland" equals "La La Land"."""
    return re.sub(r"[\W_]+", "", unicodedata.normalize("NFKC", text).casefold())


def find_similar_titles(fragment: str) -> list[dict]:
    """Candidate catalog titles for a fragment that did not match exactly (vector + keyword search)."""
    try:
        response = search_movies(MovieSearchRequest(query=fragment, mode="hybrid", limit=15))
    except Exception:
        logger.exception("Fuzzy title lookup failed")
        return []
    seen: dict[int, dict] = {}
    for hit in response.hits:
        if hit.movie_id is not None and hit.title and hit.movie_id not in seen:
            seen[hit.movie_id] = {"id": hit.movie_id, "title": hit.title}
    return list(seen.values())


def _fuzzy_match(fragment: str, candidates: list[dict]) -> tuple[int | None, list[str]]:
    """Return (movie_id, []) for one clear match, else (None, suggested titles) so the caller can ask."""
    key = _compact_key(fragment)
    if len(key) < 3:
        return None, []
    scored: dict[int, tuple[float, str]] = {}
    for movie in candidates:
        titles = [movie["title"], movie.get("originalTitle") or ""]
        ratio = max((1.0 if _compact_key(t) == key else SequenceMatcher(None, key, _compact_key(t)).ratio())
                    for t in titles if t)
        if movie["id"] not in scored or ratio > scored[movie["id"]][0]:
            scored[movie["id"]] = (ratio, movie["title"])
    ranked = sorted(scored.items(), key=lambda item: item[1][0], reverse=True)
    perfect = [item for item in ranked if item[1][0] == 1.0]
    if len(perfect) == 1:
        return perfect[0][0], []
    if len(perfect) > 1:
        return None, [item[1][1] for item in perfect[:FUZZY_SUGGESTIONS]]
    if ranked and ranked[0][1][0] >= FUZZY_ACCEPT_RATIO and (
        len(ranked) == 1 or ranked[0][1][0] - ranked[1][1][0] >= FUZZY_MARGIN
    ):
        return ranked[0][0], []
    return None, [item[1][1] for item in ranked if item[1][0] >= FUZZY_SUGGEST_RATIO][:FUZZY_SUGGESTIONS]


def _comparison_pairs(question: str) -> list[tuple[str, str]]:
    quoted = re.findall(r'"([^"]+)"|“([^”]+)”', question)
    if len(quoted) == 2:
        return [(quoted[0][0] or quoted[0][1], quoted[1][0] or quoted[1][1])]
    command = COMPARISON_START.search(question)
    candidates = [question[command.end():], question[:command.start()]] if command else [question]
    return [(text[:link.start()].strip(), text[link.end():].strip())
            for text in candidates for link in list(COMPARISON_LINK.finditer(text))[:6]]


def _comparison_ids(question: str, history: list[ChatHistoryMessage]) -> tuple[list[int], str | None]:
    """Resolve the two movies being compared; the second value is a clarifying question when unsure."""
    previous = _latest_movie_ids(history)
    text = question.casefold()
    if any(term in text for term in ("first two", "hai phim đầu")) and len(previous) >= 2:
        return previous[:2], None
    if not _comparison_pairs(question):
        if any(term in text for term in ("hai phim", "2 phim", "these two movies", "those two movies")):
            return (previous if len(previous) == 2 else []), None
        return [], None

    cache: dict[str, list[dict]] = {}
    fuzzy_cache: dict[str, tuple[int | None, list[str]]] = {}
    unsure: dict[str, list[str]] = {}

    def resolve(fragment: str) -> int | None:
        if _title_key(fragment.strip(' ?!"“”')) in SINGLE_REFERENCE:
            return previous[0] if len(previous) == 1 else None
        for title, year in _title_variants(fragment):
            if title not in cache:
                cache[title] = find_exact_movie_titles(title)
            matches = [movie for movie in cache[title]
                       if _title_key(title) in (_title_key(movie["title"]),
                                               _title_key(movie.get("originalTitle") or ""))
                       and (year is None or movie.get("releaseYear") == year)]
            ids = list(dict.fromkeys(movie["id"] for movie in matches))
            if len(ids) == 1:
                return ids[0]
            if len(ids) > 1:
                unsure[title] = [f"{movie['title']} ({movie['releaseYear']})" if movie.get("releaseYear")
                                 else movie["title"] for movie in matches]
                return None
        # No exact match: ignore spaces/punctuation and allow small typos, but never guess between ties.
        for title, year in _title_variants(fragment):
            if year is not None:
                continue
            if title not in fuzzy_cache:
                fuzzy_cache[title] = _fuzzy_match(title, find_similar_titles(title))
            movie_id, suggestions = fuzzy_cache[title]
            if movie_id is not None:
                return movie_id
            if suggestions:
                unsure[title] = suggestions
        return None

    pairs = set()
    for left, right in _comparison_pairs(question):
        first, second = resolve(left), resolve(right)
        if first is not None and second is not None and first != second:
            pairs.add((first, second))
    if len(pairs) == 1:
        return list(next(iter(pairs))), None
    if unsure:
        title, options = next(iter(unsure.items()))
        return [], (f'Which movie did you mean by "{title}"? Possible matches: {"; ".join(options)}. '
                    "Please give the exact title, for example with the year: Title (2016).")
    return [], None


def _catalog_movies(ids: list[int], context: list[MovieContext]) -> list[MovieContext]:
    hydrated = build_context_for_movie_ids(ids)
    by_id = {movie.movie_id: movie for movie in context}
    return [movie.model_copy(update={"genres": by_id[movie.movie_id].genres})
            if movie.movie_id in by_id else movie for movie in hydrated]


def _fact(question: str, movie: MovieContext) -> tuple[str, str] | None:
    text = question.casefold()
    if any(term in text for term in ("đạo diễn", "director")) and movie.director:
        return "Director", movie.director
    if any(term in text for term in ("diễn viên", "actor", "cast")) and movie.cast:
        return "Cast", ", ".join(movie.cast[:5])
    if any(term in text for term in ("năm phát hành", "năm nào", "release year")) and movie.year:
        return "Release year", str(movie.year)
    if any(term in text for term in ("thời lượng", "runtime")) and movie.runtime_minutes:
        return "Runtime", f"{movie.runtime_minutes} minutes"
    if any(term in text for term in ("điểm imdb", "rating")) and movie.imdb_rating is not None:
        return "IMDb rating", str(movie.imdb_rating)
    if any(term in text for term in ("thể loại", "genre")) and movie.genres:
        return "Genres", ", ".join(movie.genres)
    if any(term in text for term in ("nội dung", "tóm tắt", "plot", "summary")) and movie.overview:
        return "Overview", movie.overview
    return None


def answer_with_detail_tool(question: str, context: list[MovieContext], history: list[ChatHistoryMessage]) -> RAGAnswer:
    ids = _selected_ids(question, context, history)
    if len(ids) != 1:
        return RAGAnswer(status="insufficient_context", answer="Which movie would you like to ask about?", movies=[])
    movies = _catalog_movies(ids, context)
    if not movies:
        return RAGAnswer(status="no_match", answer="This movie was not found in the catalog.", movies=[])
    movie = movies[0]
    fact = _fact(question, movie)
    if fact is None:
        return RAGAnswer(status="insufficient_context", answer="The catalog does not have the requested fact for this movie.", movies=[])
    label, value = fact
    return RAGAnswer(
        status="answered", answer=f"{label} for {movie.title}: {value}.",
        movies=[AnswerMovie(movie_id=movie.movie_id, title=movie.title, reason=f"{label}: {value}")],
    )


def answer_with_comparison_tool(question: str, context: list[MovieContext], history: list[ChatHistoryMessage]) -> RAGAnswer:
    ids, clarification = _comparison_ids(question, history)
    if len(ids) != 2:
        return RAGAnswer(status="insufficient_context",
                         answer=clarification or "Please identify two movies to compare.", movies=[])
    movies = _catalog_movies(ids, context)
    if len(movies) != 2:
        return RAGAnswer(status="no_match", answer="Both movies could not be found in the catalog.", movies=[])
    labels = (("Release year", "year"), ("Runtime", "runtime_minutes"),
              ("Director", "director"), ("IMDb rating", "imdb_rating"))
    comparable = [(label, getattr(movies[0], field), getattr(movies[1], field))
                  for label, field in labels if getattr(movies[0], field) is not None
                  and getattr(movies[1], field) is not None]
    if not comparable:
        return RAGAnswer(status="insufficient_context", answer="The catalog does not have enough shared facts to compare these movies.", movies=[])
    lines = [f"{label}: {movies[0].title} {left}; {movies[1].title} {right}."
             for label, left, right in comparable]
    return RAGAnswer(
        status="answered", answer=" ".join(lines),
        movies=[AnswerMovie(movie_id=movie.movie_id, title=movie.title,
                            reason=f"{comparable[0][0].capitalize()}: {comparable[0][index]}")
                for index, movie in enumerate(movies, start=1)],
    )
