"""Exercise the real browser API, Spring chat persistence, and AI service.

Requires a running frontend/backend/AI stack and an existing test account.
Only the conversation created by this script is deleted on exit.
"""

from __future__ import annotations

import argparse
import http.cookiejar
import json
import os
import urllib.error
import urllib.request


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:3000")
    parser.add_argument("--first-message", default="Recommend a movie")
    parser.add_argument("--keep", action="store_true", help="Keep the test conversation for inspection")
    args = parser.parse_args()

    email = os.environ.get("WTW_E2E_EMAIL")
    password = os.environ.get("WTW_E2E_PASSWORD")
    if not email or not password:
        parser.error("Set WTW_E2E_EMAIL and WTW_E2E_PASSWORD for an existing test account")

    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    base = args.base_url.rstrip("/")

    def request(method: str, path: str, payload: dict | None = None):
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            base + path, data=body, method=method,
            headers={"Content-Type": "application/json"},
        )
        try:
            with opener.open(req, timeout=420 if method == "POST" else 15) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:500]
            raise RuntimeError(f"{method} {path} returned HTTP {exc.code}: {detail}") from exc

    request("POST", "/api/auth/login", {"email": email, "password": password})
    conversation_id = None
    try:
        first = request("POST", "/api/chat", {"conversationId": None, "message": args.first_message})
        conversation_id = first["conversationId"]
        assert isinstance(conversation_id, int) and conversation_id > 0
        assert first["status"] in {"answered", "no_match", "insufficient_context"}
        assert isinstance(first["reply"], str) and first["reply"].strip()

        movie_ids = [movie["movie_id"] for movie in first["recommendedMovies"]]
        follow_up = "What year was that movie released?" if movie_ids else "Recommend another movie"
        second = request("POST", "/api/chat", {"conversationId": conversation_id, "message": follow_up})
        assert second["conversationId"] == conversation_id
        assert second["status"] in {"answered", "no_match", "insufficient_context"}
        assert isinstance(second["reply"], str) and second["reply"].strip()

        detail = request("GET", f"/api/chat/conversations/{conversation_id}")
        messages = detail["messages"]
        assert len(messages) == 4, f"Expected two persisted turns; got {len(messages)} messages"
        assert [message["role"] for message in messages] == ["user", "assistant", "user", "assistant"]
        assert messages[0]["content"] == args.first_message
        assert messages[2]["content"] == follow_up
        assert [movie["movie_id"] for movie in messages[1]["recommendedMovies"]] == movie_ids
        assert any(item["id"] == conversation_id for item in request("GET", "/api/chat/conversations"))

        print(json.dumps({
            "conversation_id": conversation_id, "first_status": first["status"],
            "first_movie_ids": movie_ids, "follow_up_status": second["status"],
            "follow_up_movie_ids": [movie["movie_id"] for movie in second["recommendedMovies"]],
            "persisted_messages": len(messages),
        }, indent=2))
    finally:
        if conversation_id is not None and not args.keep:
            request("DELETE", f"/api/chat/conversations/{conversation_id}")


if __name__ == "__main__":
    main()
