"""Kiểm tra ngoại tuyến pipeline làm sạch và tạo văn bản của issue #7."""

import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "data" / "scripts"))

from clean_movies import clean_movie, process_file  # noqa: E402


class CleanMoviesTests(unittest.TestCase):
    def test_issue_6_sample_produces_one_text_per_movie(self):
        source = ROOT / "data" / "seeds" / "imdb_tmdb_sample.jsonl"
        with TemporaryDirectory() as directory:
            folder = Path(directory)
            output = folder / "movies.jsonl"
            report = process_file(source, output, folder / "report.json", folder / "rejected.jsonl")
            rows = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
            self.assertEqual((report["input_rows"], report["output_rows"], report["rejected_rows"]), (3, 3, 0))
            self.assertEqual(len({row["imdb_id"] for row in rows}), 3)
            self.assertTrue(all(row["embedding_text"].startswith(f'Title: {row["title"]}') for row in rows))
            self.assertTrue(all(row["text_template_version"] == "movie_text_v1" for row in rows))
            self.assertTrue(all(row["movie_id"] is None for row in rows))

            first_pass = output.read_bytes()
            self.assertEqual(
                first_pass,
                (ROOT / "data" / "seeds" / "movies_cleaned_sample.jsonl").read_bytes(),
            )
            process_file(source, output, folder / "report.json", folder / "rejected.jsonl")
            self.assertEqual(output.read_bytes(), first_pass)

    def test_missing_fields_normalization_and_text_order(self):
        source = {
            "imdb_id": " tt1234567 ", "tmdb_id": "42", "title": "  Café\n  Movie ",
            "original_title": None, "overview": "\\N", "tagline": "  ",
            "genres": [{"name": " Drama "}, {"name": "Action"}, {"name": "Action"}],
            "keywords": None,
            "directors": [{"name": "Zoë"}, {"name": " Ana "}],
            "cast": [{"name": "Second", "order": 1}, {"name": "First", "order": 0}, {"name": "First", "order": 2}],
            "production_countries": [{"iso_3166_1": "us", "name": "United States"}],
            "imdb_genres": None, "imdb_year": 2024, "runtime_minutes": 99,
            "imdb_rating": 8.2, "imdb_vote_count": 120,
        }
        movie = clean_movie(source)
        self.assertEqual(movie["title"], "Café Movie")
        self.assertEqual([item["name"] for item in movie["genres"]], ["Action", "Drama"])
        self.assertEqual(movie["imdb_genres"], [])
        self.assertEqual(movie["missing_fields"], ["overview", "tagline", "keywords", "original_language", "poster_path", "backdrop_path", "trailer"])
        self.assertEqual(movie["embedding_text"].splitlines(), [
            "Title: Café Movie", "Genres: Action, Drama", "Director: Ana, Zoë",
            "Top Cast: First, Second", "Production Countries: United States",
        ])
        self.assertNotIn("2024", movie["embedding_text"])
        self.assertNotIn("8.2", movie["embedding_text"])
        self.assertNotIn("99", movie["embedding_text"])

    def test_rejects_bad_records_and_duplicate_external_ids(self):
        rows = [
            {"imdb_id": "tt1234567", "tmdb_id": 1, "title": "One"},
            {"imdb_id": "tt1234567", "tmdb_id": 2, "title": "Duplicate IMDb"},
            {"imdb_id": "tt7654321", "tmdb_id": 1, "title": "Duplicate TMDB"},
            {"imdb_id": "bad", "tmdb_id": 3, "title": "Bad ID"},
            {"imdb_id": "tt7654321", "tmdb_id": 4, "title": " "},
        ]
        with TemporaryDirectory() as directory:
            folder = Path(directory)
            source = folder / "source.jsonl"
            source.write_text("\n".join(json.dumps(row) for row in rows) + "\n{bad json\n", encoding="utf-8")
            report = process_file(source, folder / "output.jsonl", folder / "report.json", folder / "rejected.jsonl")
            rejected = [json.loads(line) for line in (folder / "rejected.jsonl").read_text(encoding="utf-8").splitlines()]
            self.assertEqual((report["input_rows"], report["output_rows"], report["rejected_rows"], report["duplicate_rows"]), (6, 1, 5, 2))
            self.assertEqual([item["reason"] for item in rejected], [
                "duplicate_id", "duplicate_id", "invalid_imdb_id", "missing_title", "invalid_json",
            ])


if __name__ == "__main__":
    unittest.main()
