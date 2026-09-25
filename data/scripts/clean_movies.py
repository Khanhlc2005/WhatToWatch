"""Làm sạch bản ghi JSONL từ issue #6 và tạo văn bản truy hồi chuẩn cho phim.

Cách chạy: python3 data/scripts/clean_movies.py
"""

import argparse
from collections import Counter
from datetime import date
import json
import math
from pathlib import Path
import re
import unicodedata

from embedding_template import TEXT_TEMPLATE_VERSION, build_embedding_text


DEFAULT_INPUT = Path("data/seeds/imdb_tmdb_sample.jsonl")
DEFAULT_OUTPUT = Path("data/processed/movies_cleaned.jsonl")
IMDB_ID_PATTERN = re.compile(r"tt\d{7,}$")
MISSING_CHECK_FIELDS = (
    "overview", "tagline", "genres", "keywords", "directors", "cast",
    "production_countries", "original_language", "poster_path",
    "backdrop_path", "trailer",
)


def clean_string(value):
    if value is None or not isinstance(value, str):
        return None
    value = " ".join(unicodedata.normalize("NFC", value).split())
    return value if value and value not in {"\\N", "null"} else None


def clean_int(value, minimum=0):
    if isinstance(value, bool) or value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return int(number) if math.isfinite(number) and number.is_integer() and number >= minimum else None


def clean_float(value, minimum=0, maximum=None):
    if isinstance(value, bool) or value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) and number >= minimum and (maximum is None or number <= maximum) else None


def clean_bool(value):
    if isinstance(value, bool):
        return value
    if value in (0, "0", "false", "False"):
        return False
    if value in (1, "1", "true", "True"):
        return True
    return None


def clean_date(value):
    value = clean_string(value)
    if value is None:
        return None
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError:
        return None


def clean_named_list(value):
    """Loại mục TMDB trùng và sắp xếp theo tên để tái tạo cùng văn bản."""
    terms = {}
    for item in value if isinstance(value, list) else []:
        if isinstance(item, str):
            item = {"name": item}
        if not isinstance(item, dict):
            continue
        name = clean_string(item.get("name"))
        if not name:
            continue
        tmdb_id = clean_int(item.get("tmdb_id"), minimum=1)
        key = ("id", tmdb_id) if tmdb_id else ("name", name.casefold())
        terms.setdefault(key, {"name": name, "tmdb_id": tmdb_id})
    return sorted(terms.values(), key=lambda item: (item["name"].casefold(), item["tmdb_id"] or 0))


def clean_cast(value):
    cast = {}
    for item in value if isinstance(value, list) else []:
        if not isinstance(item, dict):
            continue
        name = clean_string(item.get("name"))
        if not name:
            continue
        tmdb_id = clean_int(item.get("tmdb_id"), minimum=1)
        actor = {
            "name": name,
            "tmdb_id": tmdb_id,
            "character": clean_string(item.get("character")),
            "order": clean_int(item.get("order")),
        }
        key = ("id", tmdb_id) if tmdb_id else ("name", name.casefold())
        current_order = cast[key]["order"] if key in cast else None
        new_rank = actor["order"] if actor["order"] is not None else math.inf
        old_rank = current_order if current_order is not None else math.inf
        if key not in cast or new_rank < old_rank:
            cast[key] = actor
    return sorted(
        cast.values(),
        key=lambda item: (
            item["order"] if item["order"] is not None else math.inf,
            item["name"].casefold(),
        ),
    )


def clean_countries(value):
    countries = {}
    for item in value if isinstance(value, list) else []:
        if not isinstance(item, dict):
            continue
        code = clean_string(item.get("iso_3166_1"))
        name = clean_string(item.get("name"))
        if not code or not name:
            continue
        code = code.upper()
        countries.setdefault(code, {"iso_3166_1": code, "name": name})
    return [countries[code] for code in sorted(countries)]


def clean_trailer(value):
    if not isinstance(value, dict):
        return None
    key = clean_string(value.get("key"))
    site = clean_string(value.get("site"))
    if not key or not site:
        return None
    return {
        "key": key,
        "site": site,
        "type": clean_string(value.get("type")),
        "official": clean_bool(value.get("official")),
    }


def clean_movie(source):
    if not isinstance(source, dict):
        raise ValueError("record_not_object")
    imdb_id = clean_string(source.get("imdb_id"))
    tmdb_id = clean_int(source.get("tmdb_id"), minimum=1)
    title = clean_string(source.get("title"))
    if not imdb_id or not IMDB_ID_PATTERN.fullmatch(imdb_id):
        raise ValueError("invalid_imdb_id")
    if tmdb_id is None:
        raise ValueError("invalid_tmdb_id")
    if title is None:
        raise ValueError("missing_title")

    directors = clean_named_list(source.get("directors"))
    directors = [{**person, "job": "Director"} for person in directors]
    imdb_genres = source.get("imdb_genres")
    imdb_genres = imdb_genres if isinstance(imdb_genres, list) else []
    movie = {
        "movie_id": clean_int(source.get("movie_id"), minimum=1),
        "imdb_id": imdb_id,
        "tmdb_id": tmdb_id,
        "title": title,
        "original_title": clean_string(source.get("original_title")),
        "imdb_title": clean_string(source.get("imdb_title")),
        "overview": clean_string(source.get("overview")),
        "tagline": clean_string(source.get("tagline")),
        "genres": clean_named_list(source.get("genres")),
        "imdb_genres": sorted(
            {name for name in (clean_string(item) for item in imdb_genres) if name},
            key=lambda name: (name.casefold(), name),
        ),
        "keywords": clean_named_list(source.get("keywords")),
        "directors": directors,
        "cast": clean_cast(source.get("cast")),
        "production_countries": clean_countries(source.get("production_countries")),
        "original_language": clean_string(source.get("original_language")),
        "release_date": clean_date(source.get("release_date")),
        "imdb_year": clean_int(source.get("imdb_year"), minimum=1800),
        "runtime_minutes": clean_int(source.get("runtime_minutes"), minimum=1),
        "adult": clean_bool(source.get("adult")),
        "imdb_rating": clean_float(source.get("imdb_rating"), maximum=10),
        "imdb_vote_count": clean_int(source.get("imdb_vote_count")),
        "tmdb_vote_average": clean_float(source.get("tmdb_vote_average"), maximum=10),
        "tmdb_popularity": clean_float(source.get("tmdb_popularity")),
        "status": clean_string(source.get("status")),
        "poster_path": clean_string(source.get("poster_path")),
        "backdrop_path": clean_string(source.get("backdrop_path")),
        "trailer": clean_trailer(source.get("trailer")),
    }
    movie["missing_fields"] = [field for field in MISSING_CHECK_FIELDS if not movie[field]]
    movie["text_template_version"] = TEXT_TEMPLATE_VERSION
    movie["embedding_text"] = build_embedding_text(movie)
    return movie


def process_file(input_path, output_path, report_path, rejected_path):
    paths = (input_path, output_path, report_path, rejected_path)
    if len({path.resolve() for path in paths}) != len(paths):
        raise ValueError("input, output, report and rejected paths must differ")
    for path in (output_path, report_path, rejected_path):
        path.parent.mkdir(parents=True, exist_ok=True)
    counts = Counter()
    missing = Counter()
    rejected_reasons = Counter()
    seen_imdb = set()
    seen_tmdb = set()

    with input_path.open(encoding="utf-8") as source, output_path.open("w", encoding="utf-8") as output, rejected_path.open("w", encoding="utf-8") as rejected:
        for line_number, line in enumerate(source, 1):
            if not line.strip():
                continue
            counts["input_rows"] += 1
            raw = None
            try:
                raw = json.loads(line)
                movie = clean_movie(raw)
                if movie["imdb_id"] in seen_imdb or movie["tmdb_id"] in seen_tmdb:
                    raise ValueError("duplicate_id")
            except (json.JSONDecodeError, ValueError) as exc:
                reason = "invalid_json" if isinstance(exc, json.JSONDecodeError) else str(exc)
                counts["rejected_rows"] += 1
                rejected_reasons[reason] += 1
                if reason == "duplicate_id":
                    counts["duplicate_rows"] += 1
                rejected.write(json.dumps({
                    "line": line_number,
                    "imdb_id": raw.get("imdb_id") if isinstance(raw, dict) else None,
                    "tmdb_id": raw.get("tmdb_id") if isinstance(raw, dict) else None,
                    "reason": reason,
                }, ensure_ascii=False) + "\n")
                continue
            seen_imdb.add(movie["imdb_id"])
            seen_tmdb.add(movie["tmdb_id"])
            missing.update(movie["missing_fields"])
            output.write(json.dumps(movie, ensure_ascii=False, sort_keys=True) + "\n")
            counts["output_rows"] += 1

    report = {
        "input_rows": counts["input_rows"],
        "output_rows": counts["output_rows"],
        "rejected_rows": counts["rejected_rows"],
        "duplicate_rows": counts["duplicate_rows"],
        "rejected_by_reason": dict(sorted(rejected_reasons.items())),
        "missing_by_field": dict(sorted(missing.items())),
        "text_template_version": TEXT_TEMPLATE_VERSION,
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=Path("data/processed/movies_cleaned_report.json"))
    parser.add_argument("--rejected", type=Path, default=Path("data/processed/movies_cleaned_rejected.jsonl"))
    args = parser.parse_args()
    print(json.dumps(process_file(args.input, args.output, args.report, args.rejected), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
