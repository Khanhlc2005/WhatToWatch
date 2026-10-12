import json

import pytest

from finetuning.scripts.build_sft_v1 import build


def test_grounded_examples_and_split_isolation(tmp_path):
    source = tmp_path / "catalog.jsonl"
    source.write_text("".join(json.dumps({
        "movie_id": movie_id, "title": f"Movie {movie_id}",
        "directors": [{"name": f"Director {movie_id}"}],
        "genres": [{"name": "Drama"}],
    }) + "\n" for movie_id in range(1, 101)), encoding="utf-8")
    output = tmp_path / "sft"
    manifest = build(source, output, max_movies=100)
    assert sum(manifest["examples"].values()) == 200
    ids = {}
    for split in ("train", "validation", "test"):
        rows = [json.loads(line) for line in (output / f"{split}.jsonl").read_text(encoding="utf-8").splitlines()]
        ids[split] = {row["provenance"]["source_movie_id"] for row in rows}
        for row in rows:
            assert row["provenance"]["origin"] == "synthetic_template_from_catalog_facts"
            target = json.loads(row["messages"][2]["content"])
            assert target["movies"][0]["movie_id"] == str(row["provenance"]["source_movie_id"])
            assert row["messages"][0]["role"] == "system"
    assert not (ids["train"] & ids["validation"] or ids["train"] & ids["test"]
                or ids["validation"] & ids["test"])
    assert build(source, output, max_movies=100) == manifest


def test_duplicate_source_ids_are_rejected(tmp_path):
    source = tmp_path / "catalog.jsonl"
    row = json.dumps({"movie_id": 1, "title": "A", "genres": [{"name": "Drama"}]})
    source.write_text(row + "\n" + row + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate movie_id"):
        build(source, tmp_path / "sft")
