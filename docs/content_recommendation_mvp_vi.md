# Content-based recommendation MVP

## Luồng và contract

POST `/internal/recommendations` → đọc user_profiles theo point ID = user_id →
validate payload user_id, profile_version=ratings-v1 và dense 1024 hữu hạn/nonzero →
query movies named dense bằng cosine → loại ID lỗi, dedup → trả movie_id/score.
Reuse normalize của preference và MovieFilters/build_payload_filter của retrieval.
Không inference embedding hoặc tạo interactions. `ranking=cosine` giữ hành vi
MVP; `ranking=final` đã có trong code tuần 5, trả score_components/reasons và
sắp final score giảm dần.

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
Mô tả cosine trên áp dụng cho `ranking=cosine`; final ranking dùng cùng candidate
pool rồi chấm lại điểm theo profile similarity và IMDb rating.

## Backend handoff

Backend đã có `GET /movies/recommendations` cho user đăng nhập. Service đọc
ratings thật, trả cold_start nếu ít hơn 3 ratings, unavailable nếu hơn 10.000;
gửi ranking=final và loại tất cả phim đã rate. Backend hydrate từ MySQL, loại
ID thiếu/trùng/rated và giữ thứ tự, score_components/reasons của AI.
AI client lỗi/timeout trả null; Backend trả unavailable/hits=[]. Frontend hiển thị
thông báo unavailable; cold_start/chưa đăng nhập dùng feed IMDb chung.
Không tự loại watch_history vì chưa chốt chính sách event.
Recommendation GET không gửi snapshot; sync thuộc RatingService sau commit.

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
Ngày 14/10/2026: smoke live read-only với 7 ratings của user 1 xác nhận vector,
exclusions, final ranking/reasons và 10 IDs có trong MySQL. Chưa xác minh thao tác
rating qua phiên đăng nhập thật hoặc deployment fixes mới.
