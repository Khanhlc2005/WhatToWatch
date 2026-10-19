"""Verify merged weights and import them as a separate Ollama model tag."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path


DEFAULT_TAG = "whattowatch-qwen25-3b-sft:english-v1"


def verify(model_dir: Path) -> dict:
    manifest = json.loads((model_dir / "export_manifest.json").read_text(encoding="utf-8"))
    if manifest.get("base_model") != "Qwen/Qwen2.5-3B-Instruct":
        raise ValueError("Unexpected base model in export manifest")
    config = json.loads((model_dir / "config.json").read_text(encoding="utf-8"))
    if config.get("model_type") != "qwen2":
        raise ValueError("Ollama export must contain a Qwen2 architecture")
    files = manifest.get("files")
    if not isinstance(files, dict) or not any(name.endswith(".safetensors") for name in files):
        raise ValueError("Manifest has no Safetensors weights")
    for name, expected in files.items():
        if Path(name).name != name:
            raise ValueError(f"Invalid file name in export manifest: {name}")
        path = model_dir / name
        if not path.is_file():
            raise FileNotFoundError(path)
        with path.open("rb") as handle:
            actual = hashlib.file_digest(handle, "sha256").hexdigest()
        if actual != expected:
            raise ValueError(f"Export file checksum mismatch: {path}")
    return manifest


def import_model(model_dir: Path, tag: str, quantize: str) -> None:
    verify(model_dir)
    if not tag or any(char.isspace() for char in tag):
        raise ValueError("Model tag must be nonempty and contain no spaces")
    with tempfile.TemporaryDirectory(prefix="wtw-ollama-") as temp:
        modelfile = Path(temp) / "Modelfile"
        modelfile.write_text(f"FROM {model_dir}\n", encoding="utf-8")
        command = ["ollama", "create", tag, "-f", str(modelfile)]
        if quantize != "none":
            command += ["--quantize", quantize]
        subprocess.run(command, check=True)
    subprocess.run(["ollama", "show", tag], check=True)
    print(f"Created {tag}. Run the RAG smoke check before setting OLLAMA_MODEL_NAME.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--tag", default=DEFAULT_TAG)
    parser.add_argument("--quantize", choices=("none", "int4", "int8"), default="int4")
    args = parser.parse_args()
    import_model(args.model_dir.resolve(), args.tag, args.quantize)
