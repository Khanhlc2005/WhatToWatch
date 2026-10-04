#!/usr/bin/env python3
"""Read-only audit of processed movies, a MySQL CSV export and Qdrant points.

CSV columns: id,imdb_id,tmdb_id. No IDs are generated or written to Qdrant.
A Qdrant JSONL snapshot contains {"id": ..., "payload": {...}} per line.
"""
import argparse
from collections import Counter
import csv
import json
from pathlib import Path
import re
from uuid import NAMESPACE_URL, uuid5

ROOT = Path(__file__).resolve().parents[2]


def positive_id(value):
    if isinstance(value, bool) or not re.fullmatch(r"[1-9][0-9]*", str(value)):
        return None
    number = int(value)
    return number if number <= 2**63 - 1 else None


def load_jsonl(path):
    with Path(path).open(encoding="utf-8") as source:
        return [json.loads(line) for line in source if line.strip()]


def audit_links(movies, mysql_rows=None, points=None):
    issues = []

    def issue(code, **context):
        issues.append({"code": code, **context})

    def duplicates(rows, field, source):
        counts = Counter(str(row[field]) for row in rows if row.get(field) is not None)
        for value, count in counts.items():
            if count > 1:
                issue("duplicate", source=source, field=field, value=value, count=count)

    if not movies:
        issue("empty_source")
    for field in ("movie_id", "imdb_id", "tmdb_id"):
        duplicates(movies, field, "processed")
    for movie in movies:
        if not re.fullmatch(r"tt[0-9]+", str(movie.get("imdb_id"))):
            issue("invalid_imdb_id", source="processed", value=movie.get("imdb_id"))
        if positive_id(movie.get("tmdb_id")) is None:
            issue("invalid_tmdb_id", source="processed", imdb_id=movie.get("imdb_id"))
        if positive_id(movie.get("movie_id")) is None:
            issue("missing_or_invalid_movie_id", source="processed", imdb_id=movie.get("imdb_id"))

    mysql_by_imdb = {}
    if mysql_rows is not None:
        for field in ("id", "imdb_id", "tmdb_id"):
            duplicates(mysql_rows, field, "mysql")
        for row in mysql_rows:
            if positive_id(row.get("id")) is None or positive_id(row.get("tmdb_id")) is None:
                issue("invalid_id", source="mysql", imdb_id=row.get("imdb_id"))
            if not re.fullmatch(r"tt[0-9]+", str(row.get("imdb_id"))):
                issue("invalid_imdb_id", source="mysql", value=row.get("imdb_id"))
            mysql_by_imdb[row.get("imdb_id")] = row
        for movie in movies:
            row = mysql_by_imdb.get(movie.get("imdb_id"))
            if row is None:
                issue("missing_mysql_movie", imdb_id=movie.get("imdb_id"))
                continue
            for source_field, target_field in (("tmdb_id", "tmdb_id"), ("movie_id", "id")):
                if positive_id(movie.get(source_field)) != positive_id(row.get(target_field)):
                    issue("mysql_mismatch", imdb_id=movie.get("imdb_id"), field=source_field)

    if points is not None:
        duplicates(points, "id", "qdrant")
        payloads = [point.get("payload") or {} for point in points]
        for field in ("movie_id", "imdb_id", "tmdb_id"):
            duplicates(payloads, field, "qdrant")
        by_imdb = {payload.get("imdb_id"): point for point, payload in zip(points, payloads)}
        for point, payload in zip(points, payloads):
            imdb = payload.get("imdb_id")
            if not re.fullmatch(r"tt[0-9]+", str(imdb)):
                issue("invalid_imdb_id", source="qdrant", value=imdb)
            expected = str(uuid5(NAMESPACE_URL, f"whattowatch:movie:{imdb}"))
            if str(point.get("id")) != expected:
                issue("point_id_mismatch", imdb_id=imdb, point_id=point.get("id"))
            if type(payload.get("movie_id")) is not int or positive_id(payload.get("movie_id")) is None:
                issue("missing_or_invalid_movie_id", source="qdrant", imdb_id=imdb)
            if mysql_rows is not None:
                row = mysql_by_imdb.get(imdb)
                if row is None:
                    issue("orphan_qdrant_point", imdb_id=imdb)
                else:
                    for field, target in (("movie_id", "id"), ("tmdb_id", "tmdb_id")):
                        if positive_id(payload.get(field)) != positive_id(row.get(target)):
                            issue("qdrant_mysql_mismatch", imdb_id=imdb, field=field)
        for movie in movies:
            point = by_imdb.get(movie.get("imdb_id"))
            if point is None:
                issue("missing_qdrant_point", imdb_id=movie.get("imdb_id"))
                continue
            for field in ("movie_id", "tmdb_id"):
                if positive_id((point.get("payload") or {}).get(field)) != positive_id(movie.get(field)):
                    issue("qdrant_processed_mismatch", imdb_id=movie.get("imdb_id"), field=field)

    complete = mysql_rows is not None and points is not None
    return {
        "status": "PASS" if complete and not issues else "FAIL" if complete else "INCOMPLETE",
        "scope": "All supplied points and processed movies; MySQL export may contain additional movies",
        "counts": {"processed": len(movies), "mysql": len(mysql_rows) if mysql_rows is not None else None,
                   "qdrant": len(points) if points is not None else None},
        "not_run": ([] if mysql_rows is not None else ["MySQL: no CSV export supplied"])
                   + ([] if points is not None else ["Qdrant: no snapshot or URL supplied"]),
        "issues": issues,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--movies", type=Path, default=ROOT / "data/seeds/movies_cleaned_sample.jsonl")
    parser.add_argument("--mysql-csv", type=Path)
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--qdrant-jsonl", type=Path)
    source.add_argument("--qdrant-url")
    parser.add_argument("--collection", default="movies")
    args = parser.parse_args()
    rows = None
    if args.mysql_csv:
        with args.mysql_csv.open(encoding="utf-8-sig", newline="") as source_file:
            reader = csv.DictReader(source_file)
            if not {"id", "imdb_id", "tmdb_id"}.issubset(reader.fieldnames or []):
                parser.error("CSV must have columns id,imdb_id,tmdb_id; request a matching export")
            rows = list(reader)
    points = load_jsonl(args.qdrant_jsonl) if args.qdrant_jsonl else None
    if args.qdrant_url:
        from qdrant_client import QdrantClient
        points = []
        client = QdrantClient(url=args.qdrant_url, timeout=30)
        try:
            offset = None
            while True:
                page, offset = client.scroll(args.collection, limit=256, offset=offset,
                                             with_payload=True, with_vectors=False)
                points.extend({"id": str(point.id), "payload": point.payload} for point in page)
                if offset is None:
                    break
        except Exception as exc:
            print(json.dumps({"status": "INCOMPLETE", "not_run": ["Qdrant read failed"],
                              "error": type(exc).__name__}, indent=2))
            return 2
        finally:
            client.close()
    report = audit_links(load_jsonl(args.movies), rows, points)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
