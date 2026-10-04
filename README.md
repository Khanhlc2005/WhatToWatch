# WhatToWatch
WhatToWatch(W2W) — Intelligent Movie Recommendation and Discovery using Vector Search, Hybrid Search, and AI Chatbot

Frontend từ branch `anhvn-setup-UI` nằm trong `frontend/`. Contract Movie, dense/sparse retrieval, Docker AI và cách kiểm tra CSV ID: [hướng dẫn retrieval/data contract](docs/retrieval_data_contract_vi.md).


## Chạy backend và nạp dữ liệu phim bằng Docker

Chạy `docker compose up -d --build` tại thư mục này. Kiểm tra cả `whattowatch-mysql` và `whattowatch-backend` bằng `docker compose ps`.

File `movies_data.sql` được cung cấp không có `id`, `created_at`, `updated_at`; bảng phim hiện tại yêu cầu các cột này. Trước khi nạp vào database **đang rỗng**, tạo bản SQL tương thích:

```bash
python3 tools/prepare_movies_sql.py /duong/dan/movies_data.sql /tmp/movies_data_compatible.sql
docker exec -i -e MYSQL_PWD=root whattowatch-mysql mysql -u root whattowatch_db < /tmp/movies_data_compatible.sql
```

Sau khi nạp phim, có thể bổ sung ba trailer YouTube có sẵn trong dữ liệu mẫu:

```bash
docker exec -i -e MYSQL_PWD=root whattowatch-mysql mysql -u root whattowatch_db < data/mysql/sample_trailers.sql
```

Không nạp lại khi bảng đã có phim, vì sẽ tạo bản ghi trùng. Kiểm tra bằng `docker exec -e MYSQL_PWD=root whattowatch-mysql mysql -u root whattowatch_db -e 'SELECT COUNT(*) FROM movie;'`. API `http://localhost:8080/movie-recommendation/movies/home-feed/top-rated` ưu tiên điểm TMDB khi có; nếu nguồn chưa có điểm TMDB, dùng điểm IMDb.

Tổng kết đợt retrieval, phạm vi đã hoàn thành và checklist việc hoãn chờ CSV MySQL: [bàn giao](docs/handoff_retrieval_vi.md).
