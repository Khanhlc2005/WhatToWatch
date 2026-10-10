# Mapping và index catalog đã nhận từ MySQL

Việc integration MySQL/backend/search → detail đang tạm hoãn theo yêu cầu: xem [pending_search_integration_vi.md](pending_search_integration_vi.md) để tiếp tục đúng trạng thái.

## Kết quả kiểm tra ngày 2026-10-10

- GPU RTX 3050 đã hoạt động; index đủ 46.923 phim.
- Audit CSV ↔ JSONL ↔ Qdrant: PASS, không có issue. Chạy lại: 0 phim cần index.
- FastAPI tại `127.0.0.1:8010`: health, dense/sparse search và filter Drama/năm 1970–1980 đều PASS; ID kết quả khớp CSV. Tiến trình API dùng GPU (1.206 MiB tại thời điểm kiểm tra).
- 100 tests PASS trên từng môi trường Python 3.14 GPU và Python 3.11 Docker.
- SHA256 hai file nguồn và mapped output giữ nguyên sau index.
- MySQL/backend/frontend chưa kiểm chứng end-to-end trong lần này; MySQL/backend được bỏ qua theo yêu cầu.

Evidence: `docs/evidence/integration/mapping_qdrant_audit.json`, `retrieval_smoke.json`, `test_results.json`.

## Nguồn đã xác nhận

Người dùng xác nhận CSV và JSONL do đồng đội gửi, CSV chứa ID từ bảng `movies`.

- `data/raw/movies_cleaned_full.jsonl`: 46.923 phim.
- `data/processed/movies_id_mapping.csv`: 46.923 dòng, `id,imdb_id,tmdb_id,title`.
- `data/processed/movies_with_mysql_ids.jsonl`: đã tạo, chỉ thay `movie_id` theo CSV.
- File cùng tên `movies_cleaned_full.jsonl` trong `data/processed` là snapshot cũ 11.347 phim.

Không import MySQL để làm bước mapping. Không dùng `init.sql`/`import_legacy_movies.sql` cho database của đồng đội: chúng dành cho bảng legacy `movie`. Không chuyển nhánh chỉ vì tài liệu cũ yêu cầu.

## Mapping có kiểm tra

Đã chạy lệnh dưới. Chạy lại với output giống hệt sẽ báo `status=unchanged`; nếu nội dung khác, script từ chối ghi đè:

```bash
python data/scripts/map_mysql_ids.py \
  --movies data/raw/movies_cleaned_full.jsonl \
  --mysql-csv data/processed/movies_id_mapping.csv \
  --output data/processed/movies_with_mysql_ids.jsonl
```

Ghép theo IMDb, kiểm tra thêm TMDB, từ chối ID thiếu/trùng/xung đột. Hai file nguồn không bị sửa. Evidence: `docs/evidence/integration/mapping_offline.json`.

## Đồng bộ lại `movie_id` trong payload Qdrant

Script dưới kiểm tra toàn bộ CSV ↔ processed JSONL ↔ Qdrant, bao gồm IMDb, TMDB, UUID point và số lượng. Mặc định chỉ lập kế hoạch đọc dữ liệu:

```bash
ai-service/.venv-gpu/bin/python qdrant/scripts/sync_movie_ids.py
```

Nếu có `to_update > 0`, chạy `--apply`. Script tạo snapshot collection Qdrant trước lần ghi đầu tiên, sau đó chỉ dùng `SetPayload` cho trường `movie_id`; point ID và dense/sparse vectors giữ nguyên. Nếu không có thay đổi, `--apply` là no-op và không tạo snapshot.

```bash
ai-service/.venv-gpu/bin/python qdrant/scripts/sync_movie_ids.py --apply
ai-service/.venv-gpu/bin/python data/scripts/validate_movie_links.py \
  --movies data/processed/movies_with_mysql_ids.jsonl \
  --mysql-csv data/processed/movies_id_mapping.csv \
  --qdrant-url http://127.0.0.1:6335 --collection movies
curl -sS http://127.0.0.1:6335/collections/movies
```

Lần kiểm tra 2026-10-11: `records=46923`, `to_update=0`, `updated=0`, `failed=0`, `status=PASS`; audit toàn bộ trả `PASS`, không issue. Vì không có ghi dữ liệu Qdrant nên không cần snapshot mới.

## Môi trường GPU trên máy hiện tại

`ai-service/.venv-gpu` dùng `--system-site-packages` của Conda WhatToWatch (Python 3.14, torch 2.14.0+cu130); ba dependencies ghi đè được cài riêng theo file local `ai-service/requirements-gpu-overlay.txt` (không đưa lên GitHub). Môi trường này phụ thuộc bản Conda nền; không phải virtualenv tự chứa độc lập để mang sang máy khác. Docker/CI của repo vẫn dùng Python 3.11.

```bash
ai-service/.venv-gpu/bin/python -m pip check
ai-service/.venv-gpu/bin/python -c 'import torch; print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0))'
```

Cache model dành riêng cho task: `data/model_cache`, bị Git bỏ qua. Model BAAI/bge-m3 revision `5617a9f61b028005a4858fdac845db406aefb181`; max length 512, dense 1024/Cosine + sparse. Preflight cả catalog: max 472 tokens, không có dòng bị cắt.

## Index và audit

```bash
docker compose up -d qdrant
bash qdrant/scripts/run_catalog_gpu.sh --preflight-only
bash qdrant/scripts/run_catalog_gpu.sh
```

Runner yêu cầu CUDA thật và không fallback CPU. Batch mặc định 4, upsert theo chunk 64; smoke test đã đạt trên RTX 3050 4 GB. Khi chạy lại, chỉ tiếp tục các point thiếu; payload hoặc vector đã có không đúng sẽ làm dừng thay vì ghi đè. Không chạy đồng thời index sample hoặc indexer khác vào cùng collection. UUID point và MySQL `movie_id` là hai định danh khác nhau.

Sau full run, script audit toàn bộ CSV ↔ mapped JSONL ↔ Qdrant và ghi `data/processed/mapping_qdrant_audit.json`. Chỉ `status=PASS`, đủ 46.923 points và không có issue mới chứng minh full index hoàn tất. `--limit N` là smoke test có chủ đích, không chứng nhận catalog đầy đủ.

## FastAPI dùng GPU

Sau khi index kết thúc, chạy từ repo root để không giữ hai bản model trong VRAM:

```bash
HF_HOME="$PWD/data/model_cache" HF_HUB_OFFLINE=1 \
EMBEDDING_MODEL_PATH="$PWD/data/model_cache/hub/models--BAAI--bge-m3/snapshots/5617a9f61b028005a4858fdac845db406aefb181" \
EMBEDDING_DEVICE=cuda:0 QDRANT_URL=http://localhost:6335 \
ai-service/.venv-gpu/bin/python -m uvicorn app.main:app \
  --app-dir ai-service --host 127.0.0.1 --port 8010
```

```bash
curl -f http://localhost:8010/internal/qdrant/health
curl -f http://localhost:8010/internal/qdrant/search \
  -H 'Content-Type: application/json' \
  -d '{"query":"space exploration","mode":"dense","limit":5}'
```

Đổi mode thành `sparse` để kiểm tra lexical search. `/internal/health` không tự chứng minh model chạy được; phải kiểm tra request search thật.

## Integration với đồng đội

Người dùng đã xác nhận nguồn CSV và yêu cầu bỏ qua việc xin dump/dựng MySQL–backend local. Mapping và index không cần kết nối MySQL. Phạm vi kiểm chứng của đợt này là CSV đã xác nhận ↔ mapped JSONL ↔ Qdrant ↔ FastAPI; không tuyên bố đã kiểm tra live MySQL hoặc backend hydrate movie detail.

Compose chính đã thêm `AI_SERVICE_URL=http://ai-service:8010` cho trường hợp backend và AI cùng mạng Compose. Nếu chạy GPU FastAPI trên host, backend Docker cần `AI_SERVICE_URL=http://host.docker.internal:8010`, cấu hình host-gateway trên Linux và bind FastAPI vào interface mà container truy cập được. Nếu khác máy, dùng địa chỉ máy AI mà máy backend truy cập được; `localhost` không trỏ đến máy còn lại. Không mở internal AI ra Internet.

Chat còn cần Qwen2.5:3b trong Ollama; chưa tự thay bằng model khác.

## GPU repair completed on this machine

Kernel `7.0.0-34` previously had no NVIDIA module (only kernel `7.0.0-31` had one). Driver 595.99.02 and DKMS now provide the module; CUDA FP16 computation passed without a reboot. Docker CDI was also verified:

```bash
docker run --rm --device nvidia.com/gpu=all --entrypoint nvidia-smi whattowatch-ai:local
```

This proves container device access, not GPU-enabled PyTorch in that CPU image. Use the native GPU runner above for embedding. The machine-specific diagnosis and environment freeze remain local (ignored by Git); shared CUDA evidence is in `docs/evidence/integration/cuda_smoke.json`.
