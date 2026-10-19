"""Exercise the production RAG prompt and JSON guard against an Ollama tag.

This uses explicit fixture context so model integration can be checked before
Qdrant and MySQL are brought up. It does not replace end-to-end evaluation.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ai-service"))

from app.llm_client import OllamaClient  # noqa: E402
from app.schemas.rag import RAGAnswer  # noqa: E402
from app.services.rag import answer_question, load_sample_context  # noqa: E402


def run(tag: str) -> None:
    context = load_sample_context()
    client = OllamaClient()
    client.model_name = tag
    cases = (
        ("Who directed Interstellar?", "answered", "tmdb:157336"),
        ("What genres does The Godfather belong to?", "answered", "tmdb:238"),
        ("Suggest a Western movie from these options.", "no_match", None),
    )
    failures = []
    for question, expected_status, expected_id in cases:
        raw_outputs = []

        def generate(prompt: str, system: str) -> str:
            raw = client.generate(prompt, system_prompt=system,
                                  response_format=RAGAnswer.model_json_schema())
            raw_outputs.append(raw)
            return raw

        try:
            answer = answer_question(question, context, generate)
            actual_ids = [movie.movie_id for movie in answer.movies]
            passed = answer.status == expected_status and (
                actual_ids == ([] if expected_id is None else [expected_id])
            )
            result = {"question": question, "status": answer.status,
                      "movie_ids": actual_ids, "passed": passed,
                      "model_calls": len(raw_outputs)}
            if not passed:
                failures.append(result)
        except Exception as exc:
            result = {"question": question, "passed": False,
                      "error": f"{type(exc).__name__}: {exc}",
                      "model_calls": len(raw_outputs)}
            failures.append(result)
        print(json.dumps(result, ensure_ascii=False), flush=True)
    if failures:
        raise SystemExit(f"{len(failures)} smoke case(s) failed for {tag}")
    print(f"RAG smoke passed for {tag}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, help="Installed Ollama model tag")
    args = parser.parse_args()
    run(args.model)
