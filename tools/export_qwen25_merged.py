"""Merge the English-v1 PEFT adapter into its exact Hugging Face base checkpoint.

Run on a CUDA machine with enough free VRAM (for example Kaggle T4) and the
same Transformers/PEFT stack recorded in the training artifact. The output is
an ordinary Safetensors model directory for Ollama import, not a QLoRA adapter.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def verify_artifacts(artifacts: Path) -> tuple[dict, dict, Path]:
    lock = json.loads((artifacts / "model_lock.json").read_text(encoding="utf-8"))
    training = json.loads((artifacts / "train_complete.json").read_text(encoding="utf-8"))
    adapter = artifacts / "adapter"
    if lock["model_id"] != "Qwen/Qwen2.5-3B-Instruct" or len(lock["revision"]) != 40:
        raise ValueError("Unexpected base model lock")
    if training.get("test_used_for_selection") is not False:
        raise ValueError("Training selection contract is not verified")
    for name, expected in training["adapter_files"].items():
        path = adapter / name
        if not path.is_file() or sha256(path) != expected:
            raise ValueError(f"Adapter file missing or modified: {path}")
    adapter_config = json.loads((adapter / "adapter_config.json").read_text(encoding="utf-8"))
    if adapter_config.get("peft_type") != "LORA" or lock["revision"] not in adapter_config.get(
        "base_model_name_or_path", ""
    ):
        raise ValueError("Adapter does not identify the locked base revision")
    return lock, training, adapter


def export(artifacts: Path, output: Path) -> None:
    lock, training, adapter = verify_artifacts(artifacts)
    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    if not torch.cuda.is_available():
        raise RuntimeError("A CUDA GPU is required for this export")
    free_bytes, _ = torch.cuda.mem_get_info(0)
    if free_bytes < 9 * 2**30:
        raise RuntimeError("At least 9 GiB free GPU memory is required before merging")
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"Choose an empty output directory: {output}")
    output.mkdir(parents=True, exist_ok=True)

    base = AutoModelForCausalLM.from_pretrained(
        lock["model_id"], revision=lock["revision"], torch_dtype=torch.float16,
        device_map={"": 0}, attn_implementation="sdpa", trust_remote_code=False,
    )
    peft_model = PeftModel.from_pretrained(base, adapter, is_trainable=False)
    merged = peft_model.merge_and_unload(safe_merge=True)
    merged.save_pretrained(output, safe_serialization=True, max_shard_size="2GB")
    AutoTokenizer.from_pretrained(adapter, use_fast=True).save_pretrained(output)

    files = {path.name: sha256(path) for path in sorted(output.iterdir()) if path.is_file()}
    if not any(name.endswith(".safetensors") for name in files):
        raise RuntimeError("Export created no Safetensors weights")
    manifest = {
        "base_model": lock["model_id"], "base_revision": lock["revision"],
        "adapter_sha256": training["adapter_files"]["adapter_model.safetensors"],
        "precision": "float16 merged weights", "files": files,
    }
    (output / "export_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Merged model exported to {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    if args.verify_only:
        lock, _, _ = verify_artifacts(args.artifacts.resolve())
        print(f"Verified adapter for {lock['model_id']} at {lock['revision']}")
    elif args.output is None:
        parser.error("--output is required unless --verify-only is set")
    else:
        export(args.artifacts.resolve(), args.output.resolve())
