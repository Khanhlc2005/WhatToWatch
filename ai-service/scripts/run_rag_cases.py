"""Run reproducible baseline questions and save both successes and failures."""

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "ai-service"))

from app.llm_client import OllamaClient  # noqa: E402
from app.schemas.rag import RAGAnswer  # noqa: E402
from app.services.rag import answer_question, load_sample_context  # noqa: E402

OUTPUT = PROJECT_ROOT / "docs" / "evidence" / "rag_baseline_results.jsonl"


def main() -> None:
    sample = load_sample_context()
    cases = [
        ("space_recommendation", "Gợi ý phim khoa học viễn tưởng về du hành vũ trụ.", sample, "answered", ["tmdb:157336"], None),
        ("director_fact", "Ai đạo diễn Interstellar?", sample, "answered", ["tmdb:157336"], "Christopher Nolan"),
        ("no_match", "Có phim hài lãng mạn nào trong danh sách này không?", sample, "no_match", [], None),
        ("unknown_title", "Trong danh sách này có phim The Matrix không?", sample, "no_match", [], None),
        ("empty_context", "Gợi ý một phim bất kỳ.", [], "insufficient_context", [], None),
    ]
    client = OllamaClient()
    failed = False
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8") as file:
        for name, question, context, expected_status, expected_ids, expected_answer_contains in cases:
            raw_response = ""

            def generate(prompt: str, system: str) -> str:
                nonlocal raw_response
                raw_response = client.generate(
                    prompt,
                    system_prompt=system,
                    response_format=RAGAnswer.model_json_schema(),
                )
                return raw_response

            started = time.monotonic()
            record = {
                "case": name,
                "tested_at_utc": datetime.now(timezone.utc).isoformat(),
                "model": client.model_name if context else "not_called",
                "question": question,
                "context_ids": [movie.movie_id for movie in context],
                "expected_status": expected_status,
                "expected_movie_ids": expected_ids,
                "expected_answer_contains": expected_answer_contains,
            }
            try:
                result = answer_question(question, context, generate)
                actual = result.model_dump()
                actual_ids = [movie["movie_id"] for movie in actual["movies"]]
                record["actual"] = actual
                record["passed"] = actual["status"] == expected_status and all(
                    movie_id in actual_ids for movie_id in expected_ids
                ) and (bool(actual_ids) == bool(expected_ids)) and (
                    expected_answer_contains is None or expected_answer_contains in actual["answer"]
                )
            except Exception as exc:
                record["error"] = {"type": type(exc).__name__, "message": str(exc)}
                record["raw_response"] = raw_response
                record["passed"] = False
            record["elapsed_ms"] = round((time.monotonic() - started) * 1000)
            failed = failed or not record["passed"]
            file.write(json.dumps(record, ensure_ascii=False) + "\n")
            file.flush()
            print(f"{name}: {'PASS' if record['passed'] else 'FAIL'} ({record['elapsed_ms']} ms)")
    print(f"Saved {len(cases)} results to {OUTPUT}")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
