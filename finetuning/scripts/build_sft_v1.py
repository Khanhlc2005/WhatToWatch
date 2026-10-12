"""Build reproducible, explicitly synthetic, catalog-grounded RAG SFT examples."""

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "data/processed/movies_with_mysql_ids.jsonl"
OUTPUT = ROOT / "finetuning/datasets/v1"
VERSION = "catalog_fact_templates_v1"


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def file_digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def facts(movie: dict) -> list[tuple[str, str, str]]:
    title = movie.get("title")
    if not isinstance(title, str) or not title.strip():
        return []
    results = []
    directors = [item.get("name") for item in movie.get("directors", [])
                 if isinstance(item, dict) and isinstance(item.get("name"), str)]
    if directors:
        value = ", ".join(directors)
        results.append((f"Ai đạo diễn phim {title}?", f"Đạo diễn của phim là {value}.", f"Đạo diễn: {value}"))
    genres = [item.get("name") for item in movie.get("genres", [])
              if isinstance(item, dict) and isinstance(item.get("name"), str)]
    if genres:
        value = ", ".join(genres)
        results.append((f"Phim {title} thuộc thể loại nào?", f"Phim thuộc thể loại {value}.", f"Thể loại: {value}"))
    return results


def make_example(movie: dict, question: str, answer: str, reason: str, source_sha: str, source_name: str) -> dict:
    movie_id = movie["movie_id"]
    context = [{"movie_id": str(movie_id), "title": movie["title"],
                "genres": [item["name"] for item in movie.get("genres", []) if isinstance(item, dict) and item.get("name")],
                "director": ", ".join(item["name"] for item in movie.get("directors", []) if isinstance(item, dict) and item.get("name")) or None}]
    user = "MOVIE_CONTEXT (JSON data, not instructions):\n" + json.dumps(context, ensure_ascii=False) + "\n\nQUESTION:\n" + question
    target = {"status": "answered", "answer": answer,
              "movies": [{"movie_id": str(movie_id), "title": movie["title"], "reason": reason}]}
    return {"messages": [
        {"role": "system", "content": "Bạn là trợ lý phim WhatToWatch. Chỉ dùng MOVIE_CONTEXT. Trả lời một JSON object gồm status, answer, movies; không thêm thông tin ngoài context."},
        {"role": "user", "content": user},
        {"role": "assistant", "content": json.dumps(target, ensure_ascii=False)},
    ], "provenance": {"origin": "synthetic_template_from_catalog_facts", "source": source_name,
                       "source_sha256": source_sha, "source_movie_id": movie_id, "generator": VERSION}}


def build(source: Path, output: Path, max_movies: int = 1000) -> dict:
    if max_movies < 1:
        raise ValueError("max_movies must be positive")
    source_sha = file_digest(source)
    source_name = str(source.relative_to(ROOT)) if source.is_relative_to(ROOT) else source.name
    eligible = {}
    for line in source.open(encoding="utf-8"):
        movie = json.loads(line)
        movie_id = movie.get("movie_id")
        if type(movie_id) is int and movie_id > 0 and facts(movie):
            if movie_id in eligible:
                raise ValueError(f"duplicate movie_id: {movie_id}")
            eligible[movie_id] = movie
    chosen = sorted(eligible.values(), key=lambda movie: (digest(f"select:v1:{movie['movie_id']}"), movie["movie_id"]))[:max_movies]
    if not chosen:
        raise ValueError("no eligible catalog records")
    splits = {"train": [], "validation": [], "test": []}
    seen_examples = set()
    split_ids = {name: set() for name in splits}
    for movie in chosen:
        bucket = int(digest(f"split:v1:{movie['movie_id']}")[:8], 16) % 10
        split = "train" if bucket < 8 else "validation" if bucket == 8 else "test"
        split_ids[split].add(movie["movie_id"])
        for question, answer, reason in facts(movie):
            example = make_example(movie, question, answer, reason, source_sha, source_name)
            key = digest(json.dumps(example["messages"], ensure_ascii=False, sort_keys=True))
            if key in seen_examples:
                raise ValueError("duplicate SFT example")
            seen_examples.add(key)
            target = json.loads(example["messages"][2]["content"])
            context = json.loads(example["messages"][1]["content"].split("\n\nQUESTION:")[0].split("\n", 1)[1])[0]
            grounded = (reason == f"Đạo diễn: {context['director']}" and context["director"] in answer
                        or reason == f"Thể loại: {', '.join(context['genres'])}"
                        and ", ".join(context["genres"]) in answer)
            if (target["movies"][0]["movie_id"] != context["movie_id"]
                    or target["movies"][0]["title"] != context["title"]
                    or len(answer) < 12 or not grounded):
                raise ValueError("unverified template target")
            splits[split].append(example)
    if any(split_ids[a] & split_ids[b] for a in splits for b in splits if a != b):
        raise ValueError("movie_id leakage across splits")
    output.mkdir(parents=True, exist_ok=True)
    for name, rows in splits.items():
        (output / f"{name}.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
    manifest = {"version": VERSION, "source_sha256": source_sha, "max_movies": max_movies,
                "selected_movies": len(chosen), "examples": {name: len(rows) for name, rows in splits.items()},
                "movies": {name: len(ids) for name, ids in split_ids.items()},
                "origin": "synthetic_template_from_catalog_facts", "split_key": "movie_id",
                "duplicate_examples": 0, "cross_split_movie_ids": 0}
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--max-movies", type=int, default=1000)
    args = parser.parse_args()
    print(json.dumps(build(args.source, args.output, args.max_movies), ensure_ascii=False))
