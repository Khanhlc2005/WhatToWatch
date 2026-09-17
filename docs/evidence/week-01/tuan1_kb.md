**Phần việc:** Khảo sát IMDb/TMDB, thiết kế data ingestion và Qdrant schema, xác định field cho movie embedding, chuẩn bị evaluation query set.

**Phạm vi dữ liệu đã chốt:** `titleType` gồm `movie` + `tvMovie` (phim lẻ chiếu rạp và phim làm riêng cho TV, bao gồm cả phim tài liệu vì "Documentary" là genre chứ không phải titleType riêng); không bao gồm series/episode — đúng theo scope "Movie Recommendation" đã chốt trong blueprint dự án.

---

## 1. Khảo sát dataset IMDb

Tải 6 file chính thức tại `datasets.imdbws.com` (title.basics, title.ratings, title.crew, title.principals, title.akas, name.basics). Đọc `title.basics` theo chunk (100.000 dòng/lần) để tránh tràn RAM với ~12,8 triệu dòng gốc, đồng thời thêm `quoting=QUOTE_NONE` để tránh lỗi parse do dấu `"` xuất hiện trong một số tên phim.

**Kết quả:**

- Tổng số dòng title.basics gốc: 12.788.670
- Sau lọc `movie` + `tvMovie`: 912.963 (movie: 756.837 · tvMovie: 156.126)
- Sau lọc `numVotes ≥ 50`: **215.409 phim**
- Phân bố startYear: trung bình ~1999, trung vị 2008, khoảng 1894–2026

**Output:** `data/processed/movies_filtered_step1.csv`

---

## 2. Khảo sát TMDB API

Đăng ký API key (v3 auth) theo hướng dẫn chính thức tại `developer.themoviedb.org/docs/getting-started`. Gọi thử endpoint `/movie/{id}` kèm `credits,keywords,videos`.

**Kết quả:**

- Rate limit: không chạm giới hạn ở tốc độ ~8 request/giây (60 request liên tiếp, không có mã 429). Theo tài liệu chính thức, giới hạn cứng 40 req/10s đã bị gỡ từ 2019, hiện chỉ còn giới hạn ẩn ~40 req/s.
- Tỉ lệ null trên mẫu 10 phim nổi tiếng: 0% cho tất cả field kiểm tra (overview, tagline, poster_path, backdrop_path, release_date, runtime, original_language); 100% có trailer và director. Mẫu này thiên lệch vì toàn phim nổi tiếng — cần đánh giá lại với phim ít phổ biến ở giai đoạn ingest thật (Tuần 2) để có fallback phù hợp (ví dụ dùng poster thay backdrop khi thiếu, ẩn nút trailer khi không có video).
- Sự cố đã xử lý: mạng Wi-Fi ban đầu chặn TLS handshake tới `api.themoviedb.org` (nghi do lọc theo SNI); chuyển sang hotspot 4G thì hoạt động ổn định.

---

## 3. Mapping IMDb ↔ TMDB

Dùng endpoint `/find` (tra theo `imdb_id`) làm phương pháp chính, đối chiếu thêm với `links.csv` của MovieLens 32M.

**Kết quả trên mẫu 50 phim:**

- Mapping được qua `/find`: 46/50 (92%)
- Số phim lệch giữa `/find` và MovieLens: 0 — hai nguồn khớp nhau hoàn toàn
- Số phim không map được ở cả 2 cách: 1/50 — tức 3/4 phim `/find` bỏ sót đã được cứu nhờ đối chiếu MovieLens, xác nhận chiến lược dùng song song 2 nguồn là cần thiết (đạt ~98% coverage kết hợp)

**Output:** `data/processed/unmatched_step3.csv` (log các phim chưa map được, để xử lý tiếp ở Tuần 2)

---

## 4. Movie embedding text template

Chốt template gồm Title, Original Title, Genres, Keywords, Overview, Tagline, Director, Cast, Production Countries, Original Language. Year/rating/runtime chủ động loại khỏi text, chỉ lưu Qdrant payload — đã kiểm chứng bằng assertion (không phát hiện field numeric lẫn vào text) trên 3 phim thật (Interstellar, Fight Club, The Godfather).

**Nhận xét:** số lượng keyword dao động khá lớn giữa các phim trong mẫu (14–29 keyword) — cần theo dõi khi mở rộng catalog, vì phim ít phổ biến nhiều khả năng có ít hoặc không có keyword.

---

## 5. Qdrant collection draft

Dùng container Qdrant local có sẵn (`tinyrag_qdrant`, port 6333/6334, dùng chung với project trước — không xung đột vì khác tên collection). Tạo 2 collection theo đúng thiết kế:

- `movies`: named vectors dense (BGE-M3, 1024 chiều, cosine) + sparse; payload gồm movie_id, genres, year, rating, language, country, runtime, keywords, adult, status
- `user_profiles`: dense vector; payload gồm user_id, profile_version, last_updated

**Kết quả:** tạo collection thành công, test insert/retrieve 1 point — payload trả về khớp 100% với dữ liệu đã insert.

---

## 6. Evaluation query set (draft)

Tạo khung 6 query mẫu, mỗi loại 1 câu: exact title, semantic, actor/director, genre, combined filter, conversational follow-up. `expected_movie_ids` đã điền cho 3 query có đáp án rõ ràng (đều trỏ về Interstellar); 3 query còn lại để mở, sẽ bổ sung khi mở rộng lên 50–100 query ở Tuần 4.

**Output:** `data/processed/evaluation_query_set_v0.csv`

---

## Tổng kết

Cả 6 nhiệm vụ Tuần 1 đã hoàn thành. Điểm cần mang sang Tuần 2:

- Xử lý danh sách phim chưa map được (`unmatched_step3.csv`) khi ingest toàn bộ catalog
- Thiết kế fallback cho các field dễ thiếu (backdrop, trailer, keywords) với phim ít phổ biến
- Mở rộng mapping/embedding từ mẫu 50 phim lên toàn bộ 215.409 phim
