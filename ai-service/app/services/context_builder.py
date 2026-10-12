"""Turn Qdrant movie IDs into bounded, verified RAG context from MySQL."""

import logging

import requests
from pydantic import ValidationError

from app.core.config import settings
from app.schemas.rag import MovieContext
from app.schemas.retrieval import MovieSearchHit, MovieSearchResponse

logger = logging.getLogger(__name__)

MAX_CONTEXT_MOVIES = 5
MAX_RETRIEVAL_CANDIDATES = 10
MAX_OVERVIEW_CHARS = 1200
CATALOG_TIMEOUT_SECONDS = 5


class MovieCatalogUnavailable(RuntimeError):
    """The backend catalog could not be read reliably."""


def fetch_movie_detail(movie_id: int) -> dict | None:
    """Read the canonical MySQL movie via Spring Boot; missing IDs are skipped."""
    url = f"{settings.backend_base_url.rstrip('/')}/movies/{movie_id}"
    try:
        response = requests.get(url, timeout=CATALOG_TIMEOUT_SECONDS)
        if response.status_code == 404:
            return None
        if response.status_code == 400:
            error = response.json()
            if isinstance(error, dict) and error.get("code") == 2001:
                return None
        response.raise_for_status()
        body = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise MovieCatalogUnavailable("Movie catalog is unavailable") from exc

    if not isinstance(body, dict) or body.get("code") != 1000 or not isinstance(body.get("result"), dict):
        raise MovieCatalogUnavailable("Movie catalog returned an invalid response")
    return body["result"]


def _year(release_date: object) -> int | None:
    if isinstance(release_date, str) and len(release_date) >= 4 and release_date[:4].isdigit():
        year = int(release_date[:4])
        if 1888 <= year <= 2100:
            return year
    return None


def _director(crew: object) -> str | None:
    if not isinstance(crew, list):
        return None
    names = []
    for member in crew:
        if not isinstance(member, dict) or str(member.get("job", "")).strip().casefold() != "director":
            continue
        name = member.get("name")
        if isinstance(name, str) and name.strip() and name.strip() not in names:
            names.append(name.strip())
    return ", ".join(names[:3]) or None


def _to_context(hit: MovieSearchHit, detail: dict) -> MovieContext | None:
    if detail.get("id") != hit.movie_id:
        logger.warning("Skipping movie %s: backend ID does not match Qdrant", hit.movie_id)
        return None
    if hit.imdb_id and detail.get("imdbId") and hit.imdb_id != detail["imdbId"]:
        logger.warning("Skipping movie %s: IMDb ID does not match Qdrant", hit.movie_id)
        return None
    if hit.tmdb_id and detail.get("tmdbId") and hit.tmdb_id != detail["tmdbId"]:
        logger.warning("Skipping movie %s: TMDB ID does not match Qdrant", hit.movie_id)
        return None

    title = detail.get("title")
    if not isinstance(title, str) or not title.strip():
        return None
    overview = detail.get("overview")
    overview = " ".join(overview.split())[:MAX_OVERVIEW_CHARS] if isinstance(overview, str) else None
    runtime = detail.get("runtimeMinutes")
    runtime = runtime if type(runtime) is int and runtime > 0 else None
    rating = detail.get("imdbRating")
    rating = float(rating) if type(rating) in (int, float) and 0 <= rating <= 10 else None
    cast = detail.get("cast")
    cast_names = [member.get("name") for member in cast if isinstance(member, dict)
                  and isinstance(member.get("name"), str)] if isinstance(cast, list) else []
    genres = list(dict.fromkeys(genre for genre in hit.genres if genre))[:8]
    try:
        return MovieContext(
            movie_id=str(hit.movie_id),
            title=title.strip(),
            year=_year(detail.get("releaseDate")),
            genres=genres,
            overview=overview or None,
            director=_director(detail.get("crew")),
            runtime_minutes=runtime,
            cast=list(dict.fromkeys(cast_names))[:10],
            imdb_rating=rating,
            original_language=detail.get("originalLanguage") or None,
        )
    except ValidationError:
        logger.warning("Skipping movie %s: invalid catalog fields", hit.movie_id)
        return None


def build_movie_context(search: MovieSearchResponse, director: str | None = None, actor: str | None = None) -> list[MovieContext]:
    """Preserve retrieval order while omitting missing or inconsistent movies."""
    context = []
    seen = set()
    for hit in search.hits:
        if len(context) >= MAX_CONTEXT_MOVIES:
            break
        if hit.id_status != "present_unverified" or hit.movie_id is None or hit.movie_id in seen:
            continue
        seen.add(hit.movie_id)
        detail = fetch_movie_detail(hit.movie_id)
        if detail is None:
            continue
        if actor:
            cast = detail.get("cast")
            if not isinstance(cast, list) or not any(
                isinstance(member, dict) and isinstance(member.get("name"), str)
                and actor.casefold() in member["name"].casefold() for member in cast
            ):
                continue
        movie = _to_context(hit, detail)
        if movie is not None and director and (not movie.director or director.casefold() not in movie.director.casefold()):
            continue
        if movie is not None:
            context.append(movie)
    return context


def build_context_for_movie_ids(movie_ids: list[int]) -> list[MovieContext]:
    """Rehydrate prior recommendations from the canonical catalog for follow-up questions."""
    context = []
    for movie_id in dict.fromkeys(movie_ids[:MAX_CONTEXT_MOVIES]):
        detail = fetch_movie_detail(movie_id)
        if detail is None:
            continue
        hit = MovieSearchHit(
            point_id=str(movie_id), movie_id=movie_id, imdb_id=None, tmdb_id=None,
            title=None, score=0.0, id_status="present_unverified",
        )
        movie = _to_context(hit, detail)
        if movie is not None:
            context.append(movie)
    return context
