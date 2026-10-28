# User Preference Vector v1

## Phạm vi và dữ liệu đã kiểm tra

RatingService có tạo/sửa/xóa rating thang 1–5; unique (user_id, movie_id).
GET /ratings/my-ratings trả dữ liệu phân trang của user đăng nhập, gồm movieId,
rating, source, createdAt. Rating không có updated_at. Trên branch tuần 6,
RatingService xếp user vào PreferenceSyncService sau commit; worker đọc snapshot
đầy đủ trong transaction read-only REQUIRES_NEW rồi gửi HTTP, kể cả snapshot rỗng.
Favorite/watchlist/history không được đưa vào profile v1. Kiểm tra live 14/10/2026:
MySQL có 1 user và 7 APP ratings; vector hiện có khớp 7 ratings này.
GET recommendation bằng session user qua Backend/frontend đã trả ready/10 hits.

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

Trạng thái code branch `feature/week6-backlog-fixes` ngày 14/10/2026:

1. Hook chạy sau transaction commit; rollback/commit failure không gửi snapshot.
2. Worker đơn trong backend đọc snapshot đầy đủ từ transaction mới, mapping movie
   IDs khi persistence context còn mở; không truyền JPA entities sang HTTP worker.
3. Worker coalesce theo user, gửi tuần tự và retry sau mỗi vòng với delay 5 giây
   kể từ vòng trước hoàn tất. Response null/lỗi/khác ready hoặc cold_start giữ user
   trong pending; mỗi retry đọc snapshot mới nhất. Commit xảy ra trong khi gửi
   vẫn giữ một lần cập nhật tiếp theo. HTTP không nằm trong transaction đọc DB.
4. AI dùng 64 locks trong một process để tránh hai rebuild cùng user ghi chồng
   nhau, gồm update cũ vẫn chạy sau read timeout của backend. User trùng bucket
   có thể phải chờ. Lock bảo vệ tính loại trừ, không cung cấp revision/CAS.
5. Queue nằm trong RAM, mất khi restart; chưa có outbox/reconcile và không điều
   phối nhiều backend/AI instances. Request đến sai thứ tự qua mạng, timeout ở
   Qdrant mà server vẫn hoàn tất ghi và lost notification chưa được bảo đảm.
   PROFILE_VERSION là version thuật toán; không dùng nó như sequence sự kiện.
6. Recommendation GET chỉ đọc profile; không rebuild mỗi lần GET. Vì sync là
   eventual consistency, request ngay sau rating có thể nhận profile cũ/cold_start.
   API rating không chờ AI và AI failure không rollback rating đã commit.

Bằng chứng/giới hạn live và tests: xem `docs/evidence/`.
Backend container đang chạy image cũ; các fixes mới chưa được deploy.

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
