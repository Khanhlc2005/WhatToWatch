# Integration search → card → detail: tạm hoãn

Cập nhật: 2026-10-11. Người dùng yêu cầu lưu việc dang dở để làm sau và chuyển bước khác.
Branch hiện tại: `feature/movie-id-qdrant-sync`. Không add/commit/push.

## Đã xác nhận

- 46.923 records CSV mapping đã được người dùng xác nhận ↔ processed JSONL ↔ Qdrant: PASS, không missing/mismatch. Đây là kiểm tra với bản export, chưa phải MySQL live.
- Processed dataset: `data/processed/movies_with_mysql_ids.jsonl`; mapping: `data/processed/movies_id_mapping.csv`.
- Qdrant collection `movies` tại `http://127.0.0.1:6335`, giữ point ID và dense/sparse vectors. Lần sync gần nhất: 0 cần cập nhật, 0 thất bại.
- 15 tests mapping/index/sync PASS trong lượt kiểm tra integration gần nhất.
- `frontend/lib/movies.ts` chuyển MySQL `id` sang ID của UI; MovieRow giữ thứ tự mảng, MovieCard mở `/movies/{id}`.
- Backend `/movies/search` hiện tìm tên trong MySQL; chưa nối Qdrant retrieval → hydrate từ MySQL theo ranking.
- Repo đã có service MySQL/backend trong Docker Compose và `.env.example`; không cần xin lại chỉ vì chưa khởi chạy.
- Khi kiểm tra Docker gần nhất, chỉ Qdrant của repo đang chạy; chưa có MySQL/backend của WhatToWatch. Cần kiểm tra lại ở session sau.

## Cần bổ sung trước khi kiểm thử live

1. Dump database thật từ đồng đội, gồm schema + data, giữ nguyên ID bảng `movies` khớp CSV đã gửi; hoặc migration tương ứng và dump dữ liệu. Có thể thay bằng quyền truy cập dịch vụ thật đang chạy.
2. Hướng dẫn import/migration nếu cần. Không gửi mật khẩu trong chat; dùng cấu hình local.
3. Xác nhận API contract retrieval search. Đề xuất thêm `mode=dense|sparse` vào `/movies/search`, giữ response `PageResponse<MovieSummaryResponse>` mới chỉ là đề xuất, chưa được chấp thuận. Cần chốt cả phân trang vì API AI hiện chỉ có `limit` tối đa 100, không có offset/total.
4. Quyền import/dựng dữ liệu local trước khi thực hiện: chưa có quyền import MySQL trong session này.

Compose hiện mount `data/mysql/init.sql`, dùng bảng legacy `movie`. Không dùng file đó để suy ra schema thật hoặc dựng thay database bảng `movies` của đồng đội. Kiểm tra và điều chỉnh cấu hình init/migration theo bộ dữ liệu thật trước khi chạy; không xóa volume để ép init lại.

## Công việc tiếp tục

- [ ] Kiểm tra branch và dịch vụ; giữ các thay đổi working tree hiện có.
- [ ] Backup dữ liệu hiện có trước mọi lần ghi/import; dựng backend/MySQL đúng schema sau khi được phép.
- [ ] Đối chiếu toàn bộ Qdrant `movie_id` với MySQL live; báo missing/mismatch.
- [ ] Dùng API/code hiện có để hydrate retrieval bằng MySQL `movie_id`; giữ thứ tự ranking, thống nhất xử lý ID thiếu/trùng và lỗi dịch vụ.
- [ ] Nối search theo contract đã chốt vào adapter MovieCard/MovieRow và detail; không dùng IMDb/TMDB/point ID thay MySQL ID.
- [ ] Viết/chạy integration tests với dữ liệu thật: mapping, ranking sau hydrate, API contract, search → card → detail và các lỗi liên quan.
- [ ] Ghi evidence, files thay đổi, kết quả test, lỗi còn lại và hướng dẫn demo thực tế.

Chưa tuyên bố luồng end-to-end PASS. Chưa sửa frontend/backend trong lượt kiểm tra này. Không fake dữ liệu/kết quả test, không rewrite frontend/backend, không rebuild vectors hoặc xóa collection.

## Lệnh kiểm tra đã có

```bash
git branch --show-current
ai-service/.venv-gpu/bin/python data/scripts/validate_movie_links.py \
  --movies data/processed/movies_with_mysql_ids.jsonl \
  --mysql-csv data/processed/movies_id_mapping.csv \
  --qdrant-url http://127.0.0.1:6335 --collection movies
ai-service/.venv-gpu/bin/python -m pytest -q \
  data/tests/test_map_mysql_ids.py data/tests/test_sync_movie_ids.py \
  data/tests/test_index_catalog.py
```

Lệnh audit trên dùng CSV, không chứng minh MySQL live. Hướng dẫn GPU/Qdrant: [mapped_catalog_run_vi.md](mapped_catalog_run_vi.md).
