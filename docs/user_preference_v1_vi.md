# User Preference Vector v1

## Phạm vi và dữ liệu đã kiểm tra

RatingService có tạo/sửa/xóa rating thang 1–5; unique (user_id, movie_id).
GET /ratings/my-ratings trả dữ liệu phân trang của user đăng nhập, gồm movieId,
rating, source, createdAt. Rating không có updated_at. notifyAiPreferenceUpdate
hiện chỉ log, chưa gửi HTTP. Favorite/watchlist/history tồn tại nhưng không được
đưa vào profile v1. Chưa xác minh dữ liệu tài khoản/rating trong MySQL live.

AI dùng dense embedding đã index trong movies qua payload movie_id, không gọi
embedding model, không suy ID từ point ID/IMDb/TMDB. Mapping cần được pipeline
catalog xác minh; endpoint không kiểm tra MySQL live.

## Công thức đã chốt

v_i = L2-normalize(movie dense embedding)
s_i = (rating_i - 3) / 2
w_i = s_i nếu s_i >= 0, ngược lại 0.35 * s_i
P = L2-normalize(sum(w_i * v_i))

Không time decay. Rating 3 là neutral, không tính vào usable_rating_count.
Ít nhất 3 ratings không neutral có embedding hợp lệ mới đủ điều kiện ready.
Thiếu embedding, sai dimension/NaN/Inf/zero hoặc movie_id trùng nhiều points:
bỏ qua, trả skipped_movies kèm reason. Tổng có norm <= 1e-12 coi là zero.
Vector chỉ gồm dislikes vẫn áp dụng đúng công thức nếu đủ 3 tín hiệu.

Cold-start trả insufficient_ratings hoặc zero_vector, xóa profile cũ nếu có,
không lưu zero vector. Feed popularity/quality thuộc bước recommendation,
endpoint này không tạo feed hoặc dữ liệu onboarding.

## API nội bộ

PUT /internal/preferences/snapshot

```json
{
  "user_id": 7,
  "ratings": [
    {"movie_id": 101, "rating": 5},
    {"movie_id": 102, "rating": 4},
    {"movie_id": 103, "rating": 1}
  ]
}
```

Đây là **toàn bộ ratings hiện tại**, không phải delta hoặc một trang dữ liệu.
Danh sách rỗng có nghĩa không còn rating và sẽ xóa profile. User/movie IDs là
integer dương <= signed BIGINT; rating hữu hạn 1–5; cấm field lạ và movie_id trùng.
Giới hạn an toàn request: 10.000 ratings, vượt trả 422, không tự truncate.
Không áp dụng cửa sổ 50–100 vì snapshot hiện chưa có timestamp/version cho việc đó.

Ví dụ response minh họa khi cả 3 phim có embedding hợp lệ:

```json
{
  "user_id": 7,
  "status": "ready",
  "reason": null,
  "profile_version": "ratings-v1",
  "last_updated": "2026-10-11T00:00:00+00:00",
  "rating_count": 3,
  "usable_rating_count": 3,
  "skipped_movies": []
}
```

HTTP 200: rebuild/upsert hoặc cold-start/delete hoàn tất (`wait=True`).
422: request sai. 503: Qdrant/lỗi xử lý, response không lộ chi tiết nội bộ.
Lỗi đọc không thay profile; timeout ghi có thể đã ghi thành công, retry snapshot.
Replays cùng snapshot cho cùng vector; last_updated đổi theo lần rebuild.

Qdrant user_profiles giữ named dense 1024/Cosine như script create_collections.py.
Point ID = user_id; payload user_id, profile_version, last_updated.
PROFILE_VERSION là version thuật toán, không phải sequence sự kiện.
Collection cấu hình qua QDRANT_USER_PROFILES_COLLECTION, mặc định user_profiles.
Phải tạo collections trước; endpoint không tự thay schema hoặc tạo collection.

## Handoff backend

Backend chưa bị sửa. Để nối tự động, teammate cần:

1. Sau transaction rating commit, đọc snapshot đầy đủ từ MySQL (kể cả sau delete).
2. Gửi user_id từ identity đã xác thực, ratings theo snake_case như trên.
3. Serialize update theo user, gửi snapshot mới nhất; retry không phát lại snapshot
   cũ sau snapshot mới. V1 chưa có source revision/CAS, không bảo vệ event đến
   sai thứ tự hay concurrent writers từ nhiều backend instances.
4. AI failure không rollback rating; retry/reconcile từ MySQL. Bỏ sót notification
   cần rebuild lại, endpoint chưa có queue/outbox hay lịch reconcile tự động.

Endpoint theo convention /internal hiện tại; chưa có service authentication.
Chỉ cho trusted backend truy cập qua mạng nội bộ; không cho frontend/client tự
chọn user_id. Internal auth là phần integration cần nối, không tuyên bố production-ready.
Không cần sao chép ratings vào Qdrant hoặc sửa entity UserPreference trong task này.

## Kiểm tra

```bash
curl -X PUT http://localhost:8010/internal/preferences/snapshot \
  -H 'Content-Type: application/json' \
  -d '{"user_id":7,"ratings":[]}'

PYTHONPATH=ai-service ai-service/.venv-gpu/bin/python -m pytest -q ai-service/tests
```

Curl trên là thao tác ghi: dùng user thử nghiệm, nó xóa profile user 7 và trả
cold_start/insufficient_ratings. Muốn demo ready, thay IDs bằng IDs thật trong catalog.
Tests dùng fixtures và Qdrant in-memory: công thức, snapshot replay/update/delete,
user isolation, cold-start, zero sum, missing/ambiguous/invalid embeddings,
validation và lỗi storage. Không thay thế kiểm tra live MySQL → backend → AI → Qdrant.
