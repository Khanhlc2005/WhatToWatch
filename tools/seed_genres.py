#!/usr/bin/env python3
"""Build the genre seed for the catalogue.

Writes backend/src/main/resources/seed/{genres.csv,movie_genres.csv.gz}, which the backend's GenreSeeder loads on
startup when `movie_genres` is empty (nothing to run by hand). With --sql it also writes an SQL script for a manual load.

Reads the cleaned catalogue JSONL (each row has `tmdb_id` and `genres: [{name, tmdb_id}]`).
Genre ids are the TMDB genre ids, because the Discover filter (frontend/config/genres.ts)
sends those ids in `genreIds`. Movies are matched through `movies.tmdb_id`.
Only rerun it when the catalogue changes.
"""

import argparse
import gzip
import json
from pathlib import Path

BATCH = 2000


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, nargs="?", default=Path("data/raw/movies_cleaned_full.jsonl"))
    parser.add_argument("--seed-dir", type=Path, default=Path("backend/src/main/resources/seed"))
    parser.add_argument("--sql", type=Path, help="also write a manual SQL load script")
    args = parser.parse_args()

    genres: dict[int, str] = {}
    pairs: set[tuple[int, int]] = set()
    movies = 0
    for line in args.source.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        movies += 1
        tmdb_id = row.get("tmdb_id")
        for genre in row.get("genres") or []:
            genre_id, name = genre.get("tmdb_id"), (genre.get("name") or "").strip()
            if not isinstance(genre_id, int) or not name:
                continue
            genres[genre_id] = name
            if isinstance(tmdb_id, int):
                pairs.add((tmdb_id, genre_id))

    args.seed_dir.mkdir(parents=True, exist_ok=True)
    (args.seed_dir / "genres.csv").write_text(
        "".join(f"{i},{n}\n" for i, n in sorted(genres.items())), encoding="utf-8")
    with open(args.seed_dir / "movie_genres.csv.gz", "wb") as raw, \
            gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as gz:
        gz.write("".join(f"{m},{g}\n" for m, g in sorted(pairs)).encode())
    print(f"{movies} movies, {len(genres)} genres, {len(pairs)} links -> {args.seed_dir}")
    if not args.sql:
        return

    out = ["SET NAMES utf8mb4;", ""]
    values = ",\n".join(f"  ({i}, '{n.replace(chr(39), chr(39) * 2)}')" for i, n in sorted(genres.items()))
    out.append(f"INSERT IGNORE INTO genres (id, name) VALUES\n{values};\n")
    out.append("DROP TEMPORARY TABLE IF EXISTS tmp_movie_genres;")
    out.append("CREATE TEMPORARY TABLE tmp_movie_genres (tmdb_id BIGINT NOT NULL, genre_id BIGINT NOT NULL);")
    ordered = sorted(pairs)
    for start in range(0, len(ordered), BATCH):
        chunk = ",".join(f"({m},{g})" for m, g in ordered[start:start + BATCH])
        out.append(f"INSERT INTO tmp_movie_genres VALUES {chunk};")
    out.append("INSERT IGNORE INTO movie_genres (movie_id, genre_id)\n"
               "SELECT m.id, t.genre_id FROM tmp_movie_genres t JOIN movies m ON m.tmdb_id = t.tmdb_id;")
    out.append("DROP TEMPORARY TABLE tmp_movie_genres;")
    args.sql.write_text("\n".join(out) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
