# Hybrid Search v1

`POST /internal/qdrant/search` nhận thêm `mode: "hybrid"` bên cạnh `dense` và `sparse`.
Giá trị mặc định vẫn là `dense`. Các field `query`, `limit` (1–100), `filters`
và cấu trúc response không đổi. `score` của hybrid là điểm RRF, không phải
cosine similarity hay sparse score.

```bash
curl -X POST http://localhost:8010/internal/qdrant/search \
  -H 'Content-Type: application/json' \
  -d '{"query":"space exploration","mode":"hybrid","limit":5,"filters":{"genres":["Science Fiction"],"countries":["US"],"rating_min":7}}'
```

Ví dụ response minh họa hình dạng contract (ID và điểm thực tế phụ thuộc dữ liệu đã index):

```json
{
  "collection": "movies",
  "mode": "hybrid",
  "hits": [
    {
      "point_id": "7d8134cb-07f2-5761-8495-b393b30a79f0",
      "movie_id": 42,
      "imdb_id": "tt0000042",
      "tmdb_id": 42,
      "title": "Example movie",
      "score": 0.03278688524590164,
      "id_status": "present_unverified"
    }
  ]
}
```

Hybrid tạo embedding một lần, truy vấn hai vector `dense` và `sparse` với cùng
payload filter, mỗi nhánh lấy tối đa `limit` ứng viên. Nếu sparse embedding rỗng,
chỉ nhánh dense được truy vấn. RRF cộng `1 / (60 + rank)` cho mỗi phim trong mỗi
nhánh, với rank bắt đầu từ 1. Một phim ở hạng 1 của cả hai nhánh được
`2 / 61 ≈ 0.032787`; phim chỉ ở hạng 1 một nhánh được `1 / 61 ≈ 0.016393`.
Kết quả được sắp theo điểm RRF giảm dần, có thứ tự ổn định khi hòa điểm,
rồi cắt theo `limit`.

Các point có `movie_id` là số nguyên dương trong miền signed 64-bit được gộp
theo ID đó. Khi thiếu hoặc ID sai định dạng, khóa gộp dùng `imdb_id`, rồi mới
đến point ID. Mỗi khóa chỉ đóng góp một lần trong từng nhánh. API vẫn trả
`id_status: "present_unverified"` cho ID hợp lệ về định dạng: việc xác minh ID
với MySQL thuộc quy trình audit dữ liệu, không xảy ra trong request tìm kiếm.
Không sử dụng point ID, IMDb ID hoặc TMDB ID làm `movie_id` thay thế.

Nếu một nhánh Qdrant lỗi, endpoint trả 503 chung như các mode hiện có.
Filters không được nới lỏng để bù số kết quả sau khi gộp.
