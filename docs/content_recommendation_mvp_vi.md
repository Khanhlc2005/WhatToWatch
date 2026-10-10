# Content-based recommendation MVP

## Luồng và contract

POST `/internal/recommendations` → đọc user_profiles theo point ID = user_id →
validate payload user_id, profile_version=ratings-v1 và dense 1024 hữu hạn/nonzero →
query movies named dense bằng cosine → loại ID lỗi, dedup → trả movie_id/score.
Reuse normalize của preference và MovieFilters/build_payload_filter của retrieval.
Không inference embedding, không reranker/final ranking Tuần 5, không tạo interactions.

Request:

```json
{"user_id":7,"limit":10,"filters":{"countries":["US"]},"exclude_movie_ids":[101,102,103]}
```

- user_id: integer dương <= signed BIGINT, do trusted backend xác định.
- limit: integer 1–100, mặc định 10.
- filters: cùng contract search (genres, exclude_genres, languages, countries,
  year_min/max, rating_min, runtime_max); mặc định rỗng.
- exclude_movie_ids: tối đa 10.000 IDs hợp lệ; backend lấy từ dữ liệu thật theo
  chính sách sản phẩm. Mặc định rỗng, không tự loại watched/rated/disliked.

Response minh họa, không phải kết quả catalog live:

```json
{"user_id":7,"status":"ready","hits":[{"movie_id":456,"score":0.81},{"movie_id":789,"score":0.72}]}
```

HTTP 200 khi có profile hợp lệ; không có candidates vẫn ready/hits=[].
Thiếu profile: HTTP 200, status=cold_start, hits=[]. Không tự sinh popularity feed.
Profile sai identity/version/vector hoặc lỗi Qdrant: 503 với thông báo generic.
Input sai: 422. Collection thiếu là lỗi service, không giả thành cold-start.

Cosine giảm dần, giữ score gốc (có thể âm), không diễn giải thành % match.
Dedup theo movie_id, lấy score lớn nhất; hòa điểm sắp movie_id tăng dần.
Loại ID null/string/bool/không dương/vượt signed BIGINT và score NaN/Inf.
Không fallback sang point ID/IMDb/TMDB. Không tự áp chính sách adult/status.

Query dùng filters và exclusions ngay trong Qdrant, lấy max(50, 5*limit) candidates
(tối đa 500), không nới filter. Nếu pool thiếu unique valid IDs thì trả ít hơn limit;
không scan toàn catalog để lấp đầy. Tie order chỉ bảo đảm trong pool Qdrant trả về.
Đây là candidate retrieval theo cosine, không phải final ranking.

## Backend handoff

Repo chưa có public recommendation gateway; task này thêm endpoint phía FastAPI.
Backend cần xác thực user, truyền exclusions, gọi AI, batch resolve movie_id trong
MySQL và giữ thứ tự score. Bỏ IDs không tồn tại/không hợp lệ nghiệp vụ khi hydrate;
AI chỉ xác nhận hình dạng ID, không xác nhận MySQL live.
Cold-start chọn feed fallback ở backend; profile/service lỗi 503 xử lý riêng.
Endpoint theo convention internal hiện có, chưa có service auth; không expose cho
frontend trực tiếp. Internal authentication cần phối hợp backend/AI.

## Demo theo user

1. Chuẩn bị movies và user_profiles bằng scripts hiện có, cùng dense 1024/Cosine.
2. Chọn user thử nghiệm và ít nhất 3 movie_id duy nhất có embedding hợp lệ.
3. Gửi snapshot ratings đầy đủ bằng API preference; phải nhận status=ready.
4. Gọi recommendation, truyền IDs muốn loại bằng exclude_movie_ids.

```bash
# Thay user/movie IDs dưới đây bằng IDs thử nghiệm thật trong catalog.
# PUT thay toàn bộ snapshot preference của user, không dùng tài khoản thật để thử.
curl -X PUT http://localhost:8010/internal/preferences/snapshot \
  -H 'Content-Type: application/json' \
  -d '{"user_id":7,"ratings":[{"movie_id":101,"rating":5},{"movie_id":102,"rating":4},{"movie_id":103,"rating":1}]}'

curl -X POST http://localhost:8010/internal/recommendations \
  -H 'Content-Type: application/json' \
  -d '{"user_id":7,"limit":5,"exclude_movie_ids":[101,102,103]}'
```

Nếu cả 3 IDs mẫu không có trong catalog, preference trả cold-start thay vì bịa vector.
Sửa ratings rồi gửi lại snapshot để quan sát ranking đổi; không bảo đảm đổi thứ tự
trên mọi catalog. Dùng user chưa có profile để demo cold_start.

## Tests

```bash
PYTHONPATH=ai-service ai-service/.venv-gpu/bin/python -m pytest -q ai-service/tests
```

Tests dùng FastAPI TestClient và Qdrant in-memory: cosine/order, signed scores,
duplicate, invalid IDs, ties, filters/exclusions, validation, cold-start, profile
lỗi, storage errors và snapshot → recommendation → update → delete.
Chưa xác minh backend/MySQL/Qdrant live end-to-end.
