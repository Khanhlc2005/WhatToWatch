#!/usr/bin/env bash
set -euo pipefail
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$repo_root"
python_bin="$repo_root/ai-service/.venv-gpu/bin/python"
export HF_HOME="$repo_root/data/model_cache"
export EMBEDDING_MODEL_PATH="$HF_HOME/hub/models--BAAI--bge-m3/snapshots/5617a9f61b028005a4858fdac845db406aefb181"
export HF_HUB_OFFLINE=1 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
mkdir -p data/processed
exec 9>data/processed/qdrant_index.lock
flock -n 9 || { echo 'Another index run holds the lock' >&2; exit 1; }
"$python_bin" -c 'import torch; assert torch.cuda.is_available(), "CUDA unavailable; refusing CPU fallback"; print(torch.cuda.get_device_name(0), flush=True)'
"$python_bin" qdrant/scripts/index_catalog.py \
  --input data/processed/movies_with_mysql_ids.jsonl \
  --url http://localhost:6335 --device cuda:0 --batch-size 4 --chunk-size 64 "$@"
for option in "$@"; do
  case "$option" in --preflight-only|--limit|--limit=*) exit 0 ;; esac
done
"$python_bin" data/scripts/validate_movie_links.py \
  --movies data/processed/movies_with_mysql_ids.jsonl \
  --mysql-csv data/processed/movies_id_mapping.csv \
  --qdrant-url http://localhost:6335 --collection movies \
  > data/processed/mapping_qdrant_audit.json
cat data/processed/mapping_qdrant_audit.json
