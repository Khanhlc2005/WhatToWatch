#!/usr/bin/env bash
# Uses the verified local Python 3.11 image; no host Python/Conda changes.
set -euo pipefail
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$repo_root"
mkdir -p data/processed
# Serialize runs started through this entrypoint.
exec 9>data/processed/qdrant_index.lock
flock -n 9 || { echo 'Another catalog index/preflight run holds the lock' >&2; exit 1; }
docker run --rm --init --user "$(id -u):$(id -g)" \
  --network whattowatch_whattowatch-network --cpus 4 --memory 4g --memory-swap 6g \
  -e HF_HOME=/cache -e HF_HUB_OFFLINE=1 \
  -e EMBEDDING_MODEL_PATH=/cache/hub/models--BAAI--bge-m3/snapshots/5617a9f61b028005a4858fdac845db406aefb181 -e TOKENIZERS_PARALLELISM=false \
  -e PYTHONDONTWRITEBYTECODE=1 -e PYTHONUNBUFFERED=1 \
  -v "$repo_root:/repo:ro" -v "$repo_root/data/model_cache:/cache:ro" \
  -w /repo --entrypoint python "${AI_RUNTIME_IMAGE:-whattowatch-ai:local}" \
  qdrant/scripts/index_catalog.py \
  --input data/processed/movies_with_mysql_ids.jsonl \
  --url http://qdrant:6333 --device cpu "$@"
# A preflight or deliberately limited run is not a full three-way audit.
for option in "$@"; do
  case "$option" in --preflight-only|--limit|--limit=*) exit 0 ;; esac
done
docker run --rm --user "$(id -u):$(id -g)" \
  --network whattowatch_whattowatch-network -e PYTHONDONTWRITEBYTECODE=1 \
  -v "$repo_root:/repo:ro" -w /repo --entrypoint python \
  "${AI_RUNTIME_IMAGE:-whattowatch-ai:local}" data/scripts/validate_movie_links.py \
  --movies data/processed/movies_with_mysql_ids.jsonl \
  --mysql-csv data/processed/movies_id_mapping.csv \
  --qdrant-url http://qdrant:6333 --collection movies \
  > data/processed/mapping_qdrant_audit.json
cat data/processed/mapping_qdrant_audit.json
