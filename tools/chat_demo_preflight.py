#!/usr/bin/env python3
"""Read-only release preflight for the local WhatToWatch chat demo.

Records concrete inputs and running service versions. It does not start Docker,
import a model, restore a snapshot, log in, or claim chat quality is validated.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from export_qwen25_merged import verify_artifacts
from import_qwen25_ollama import verify as verify_merged_model


SNAPSHOT_SHA256 = "9f98db41930a8d70f11692afb74e6b5dac5638cefb2d86b9dd6f03d30c3bf975"
DEFAULT_TUNED_TAG = "whattowatch-qwen25-3b-sft:english-v1"


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def command(*args: str, timeout: int = 15, cwd: Path | None = None) -> str:
    result = subprocess.run(args, capture_output=True, text=True, timeout=timeout, cwd=cwd)
    if result.returncode:
        detail = (result.stderr or result.stdout).strip()[-350:]
        raise RuntimeError(f"{' '.join(args)} exited {result.returncode}: {detail}")
    return result.stdout.strip()


def request_json(url: str, body: dict | None = None) -> dict:
    payload = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=8) as response:
        return json.load(response)


def run(root: Path, merged_dir: Path | None, tuned_tag: str, qdrant_url: str) -> dict:
    checks: dict[str, dict] = {}

    def check(name: str, action) -> None:
        try:
            detail = action()
            checks[name] = {"ok": True, "detail": detail}
        except Exception as exc:
            checks[name] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

    def adapter() -> dict:
        lock, training, _ = verify_artifacts(root / "w2w_english_v1_artifacts")
        return {**lock, "adapter_sha256": training["adapter_files"]["adapter_model.safetensors"]}

    def merged() -> dict:
        if merged_dir is None:
            raise FileNotFoundError("Provide --merged-model-dir to verify export_manifest.json")
        manifest = verify_merged_model(merged_dir)
        lock, training, _ = verify_artifacts(root / "w2w_english_v1_artifacts")
        if manifest.get("base_revision") != lock["revision"] or (
            manifest.get("adapter_sha256") != training["adapter_files"]["adapter_model.safetensors"]
        ):
            raise ValueError("Merged model provenance does not match the verified adapter")
        return {"path": str(merged_dir), "base_model": manifest["base_model"],
                "base_revision": manifest.get("base_revision"),
                "adapter_sha256": manifest.get("adapter_sha256")}

    def snapshot() -> dict:
        path = root / "data/processed/movies-46923-2026-10-11.snapshot"
        actual = digest(path)
        if actual != SNAPSHOT_SHA256:
            raise ValueError(f"Snapshot SHA-256 mismatch: {actual}")
        return {"path": str(path), "sha256": actual}

    def sql() -> dict:
        path = root / "data/mysql/movies_data.sql"
        if not path.is_file() or path.stat().st_size == 0:
            raise FileNotFoundError(path)
        return {"path": str(path), "size_bytes": path.stat().st_size}

    def compose() -> dict:
        data = json.loads(command("docker", "compose", "--profile", "ai", "config",
                                  "--format", "json", cwd=root))
        actual = data["services"]["ai-service"]["environment"]["OLLAMA_MODEL_NAME"]
        if actual != tuned_tag:
            raise ValueError(f"Compose AI model is {actual!r}, expected {tuned_tag!r}")
        return {"ollama_model_name": actual}

    def tags() -> dict:
        models = request_json("http://127.0.0.1:11434/api/tags")["models"]
        found = {model["name"]: model.get("digest") for model in models}
        required = ("qwen2.5:3b", tuned_tag)
        missing = [tag for tag in required if tag not in found]
        if missing:
            raise ValueError(f"Missing Ollama tag(s): {', '.join(missing)}")
        return {tag: found[tag] for tag in required}

    def mysql() -> dict:
        count = int(command("docker", "exec", "-e", "MYSQL_PWD=root", "whattowatch-mysql",
                            "mysql", "-u", "root", "-N", "whattowatch_db", "-e",
                            "SELECT COUNT(*) FROM movies;"))
        if count != 46923:
            raise ValueError(f"MySQL has {count} movies, expected 46923")
        return {"movies": count}

    def qdrant() -> dict:
        collection = request_json(qdrant_url + "/collections/movies")["result"]
        count = request_json(qdrant_url + "/collections/movies/points/count",
                             {"exact": True})["result"]["count"]
        if count != 46923 or collection.get("status") != "green":
            raise ValueError(f"Qdrant status={collection.get('status')}, count={count}; expected green/46923")
        return {"status": collection["status"], "movies": count}

    def ai() -> dict:
        result = request_json("http://127.0.0.1:8010/internal/health")
        if result.get("status") != "ok":
            raise ValueError(f"AI health status is {result.get('status')!r}")
        return result

    def frontend() -> dict:
        with urllib.request.urlopen("http://127.0.0.1:3000/chat", timeout=8) as response:
            return {"http_status": response.status, "url": response.url}

    check("git_commit", lambda: {"sha": command("git", "rev-parse", "HEAD", cwd=root)})
    check("adapter", adapter)
    check("merged_model", merged)
    check("mysql_dump", sql)
    check("qdrant_snapshot", snapshot)
    check("docker", lambda: {"server_version": command("docker", "info", "--format", "{{.ServerVersion}}")})
    check("compose_model", compose)
    check("ollama_tags", tags)
    check("mysql_catalog", mysql)
    check("qdrant_catalog", qdrant)
    check("ai_health", ai)
    check("frontend", frontend)
    return {"checked_at_utc": datetime.now(timezone.utc).isoformat(),
            "ready": all(item["ok"] for item in checks.values()), "checks": checks,
            "note": "Preflight only; run E2E smoke and human quality review separately."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--merged-model-dir", type=Path)
    parser.add_argument("--tuned-tag", default=DEFAULT_TUNED_TAG)
    parser.add_argument("--qdrant-url", default="http://127.0.0.1:6335")
    parser.add_argument("--output", type=Path, help="Optional JSON report path; must not already exist")
    args = parser.parse_args()
    report = run(args.repo.resolve(), args.merged_model_dir, args.tuned_tag,
                 args.qdrant_url.rstrip("/"))
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        with args.output.open("x", encoding="utf-8") as stream:
            stream.write(rendered)
    print(rendered, end="")
    raise SystemExit(0 if report["ready"] else 2)
