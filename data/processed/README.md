# Dữ liệu hiện có

Cập nhật sau cleanup ngày 14/10/2026. Catalog dùng cho retrieval/SFT/evaluation:
**46.923 phim** trong `movies_with_mysql_ids.jsonl`, cùng `movies_id_mapping.csv`.
Đây là dữ liệu có MySQL IDs; các scripts tuần 6 dùng hai file này.

- `movies-46923-2026-10-11.snapshot`: bản bàn giao Qdrant, giữ để restore trên
  volume mới theo README repo. Cleanup không thay đổi collection đang chạy.
- `catalog.sqlite` + `tmdb_cache/`: checkpoint thu thập cũ với 11.347 succeeded,
  17 failed, 8 unmatched; giữ để resume, đối chiếu raw metadata và tránh tải lại.
- `run_summary.json`, `validation.json`, `movies_cleaned_full_report.json`,
  `catalog_scope.json`: báo cáo lịch sử của checkpoint 11.347 phim, **không phải**
  số lượng catalog 46.923 phim hiện tại. Giữ làm provenance.
- `movies_cleaned_full_rejected.jsonl`, `movies_cleaned_full_unmatched.jsonl`:
  danh sách lỗi và không mapping; không nằm trong catalog thành công.
- `catalog_inventory.json`: thông tin nguồn IMDb/MovieLens.
- `mapping_qdrant_audit.json`: kết quả audit index lịch sử, giữ bằng chứng.
- `hotspot_6gb_usage*`: lịch sử ngân sách mạng/DNS; giữ state.
  `network_history/` đã được Khánh Bùi chủ động xóa sau cleanup.
- `catalog.lock`, `qdrant_index.lock`: files khóa; rỗng là bình thường, không xóa.

Đã xóa `movies_cleaned_full.jsonl`: 11.347 records đều có trong catalog hiện tại,
metadata giống hoàn toàn ngoài `movie_id`. Đã xóa draft `evaluation_query_set_v0.csv`;
bộ hiện hành ở `data/evaluation/query_set_v1.json`, chatbot set ở cùng thư mục.
Đã dọn năm logs local cũ không có tiến trình mở lúc kiểm tra.

Nếu cần xuất lại **checkpoint 11.347 phim** cho pipeline thu thập cũ hoặc chạy
`validate_catalog.py` với input mặc định, dùng từ repo root:

```bash
python data/scripts/run_shared_catalog.py --offline
```

Lệnh này xuất lại JSONL và cập nhật các báo cáo checkpoint; không gọi TMDB.
Không coi bản xuất đó là catalog mapped hiện hành hoặc thay input SFT bằng nó.
Bộ handoff ZIP từng ghi trong README cũ hiện không có trong thư mục; có thể tạo
lại bằng `package_catalog_handoff.py` khi thực sự cần bàn giao checkpoint/cache.

Chi tiết hashes/lý do xóa: `docs/evidence/week-06-ai-evaluation/processed_cleanup.json`.
