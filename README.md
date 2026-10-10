# WhatToWatch

Ứng dụng web duyệt phim gồm frontend Next.js, backend Spring Boot và MySQL. Hướng dẫn dưới đây chạy phần web; AI service và Qdrant không cần thiết cho trang `/browse`.

## Yêu cầu

- Docker Desktop hoặc Docker Engine với Docker Compose; kiểm tra `docker info` có phần `Server`.
- Node.js và npm để chạy frontend.
- File `movies_data.sql` ở thư mục gốc nếu muốn nạp bộ phim mẫu. File này không nằm trong GitHub; cần lấy riêng từ người quản lý dữ liệu.

Trên Linux dùng Docker Desktop, có thể khởi động bằng `systemctl --user start docker-desktop` rồi chọn `docker context use desktop-linux`. Nếu Docker Desktop không lên vì thiếu RAM, đóng bớt ứng dụng trước khi thử lại.

## 1. Chạy MySQL và backend

Tại thư mục gốc của repo:

```bash
docker compose up -d --build mysql backend
docker compose ps
```

`docker compose ps` phải hiện cả `mysql` và `backend` thuộc **project của thư mục này**. Backend phục vụ ở `http://localhost:8080/movie-recommendation`. MySQL luôn dùng cổng `3306` bên trong mạng Docker; cổng trên máy mặc định là `3306` và có thể đặt bằng `MYSQL_HOST_PORT` trong file `.env` ở thư mục gốc. Chờ backend khởi động xong, rồi kiểm tra:

```bash
curl http://localhost:8080/movie-recommendation/movies/home-feed/top-rated
```

Nếu nhận `{"code":1000,"result":[]}`, backend đã hoạt động nhưng chưa có phim; làm bước 2. Nếu không kết nối được, xem `docker compose logs --tail=80 backend mysql`.

## 2. Nạp phim vào cơ sở dữ liệu mới — chỉ một lần

Backend đọc bảng `movies`. File `movies_data.sql` nạp vào bảng cũ `movie`, sau đó `data/mysql/import_legacy_movies.sql` chuyển sang `movies`. **Chỉ chạy các lệnh nhập khi `movies` đang có 0 phim**; nạp lại file nguồn có thể tạo dữ liệu trùng.

```bash
docker exec -e MYSQL_PWD=root whattowatch-mysql mysql -u root -N whattowatch_db -e 'SELECT COUNT(*) FROM movies;'
docker exec -i -e MYSQL_PWD=root whattowatch-mysql mysql -u root whattowatch_db < movies_data.sql
docker exec -i -e MYSQL_PWD=root whattowatch-mysql mysql -u root whattowatch_db < data/mysql/import_legacy_movies.sql
docker exec -i -e MYSQL_PWD=root whattowatch-mysql mysql -u root whattowatch_db < data/mysql/sample_trailers.sql
docker exec -e MYSQL_PWD=root whattowatch-mysql mysql -u root -N whattowatch_db -e 'SELECT COUNT(*), COUNT(trailer_key) FROM movies;'
```

Với file dữ liệu hiện dùng, kết quả cuối là `11347` phim và `3` trailer gắn sẵn. Khi dùng volume MySQL mới, tài khoản và danh sách cá nhân từ volume khác không tự chuyển sang; dữ liệu cũ vẫn còn trong volume cũ.

## 3. Chạy frontend

Tạo `frontend/.env.local` nếu chưa có, theo mẫu `frontend/.env.example`. Giữ `BACKEND_URL=http://localhost:8080/movie-recommendation`. Điền `TMDB_KEY` và `YOUTUBE_API_KEY` để tự tìm trailer cho phim chưa có trailer trong SQL. File `.env.local` được Git bỏ qua; không đưa khóa API vào commit.

```bash
cd frontend
cp -n .env.example .env.local
npm ci
npm run dev
```

Mở `http://localhost:3000/browse`. Nếu vừa sửa `.env.local`, khởi động lại frontend để Next.js đọc giá trị mới. Dùng `Ctrl+C` để dừng frontend; tại thư mục gốc, `docker compose down` dừng backend/MySQL nhưng giữ volume dữ liệu. Không dùng `docker compose down -v` nếu muốn giữ cơ sở dữ liệu.

Ở những lần chạy sau, chỉ cần làm bước 1 và 3; bỏ qua bước nạp phim nếu bảng `movies` đã có dữ liệu.

## Khi gặp lỗi

- **“Không tải được danh sách phim”**: kiểm tra `http://localhost:3000/api/movies/top-rated`. API phải trả mảng phim có `id` là **số**. Nếu ID là UUID, cổng `8080` đang được backend của workspace khác phục vụ. Dùng `docker ps -a` và `docker inspect <container> --format '{{index .Config.Labels "com.docker.compose.project.working_dir"}}'` để kiểm tra nguồn container. Dừng **và đổi tên** container cũ nếu chúng trùng tên `whattowatch-backend` hoặc `whattowatch-mysql`; container đã dừng vẫn giữ tên. Không xóa volume dữ liệu cũ.
- **MySQL báo `Invalid MySQL server downgrade`**: volume đã được tạo bởi MySQL phiên bản mới hơn `mysql:8.0`. Giữ volume cũ, tạo file `docker-compose.override.yml` trên máy với nội dung bên dưới, chạy `docker compose down` (không thêm `-v`), rồi chạy lại bước 1 và 2. File override được Git bỏ qua.

  ```yaml
  volumes:
    mysql_data:
      name: whattowatch_mysql_data_mysql8
  ```

- **Cổng bị chiếm**: kiểm tra `docker ps` và `ss -ltn` cho các cổng `3000`, `8080` và cổng MySQL trên máy. Nếu MySQL cục bộ đã dùng `3306`, tạo file `.env` ở thư mục gốc với dòng `MYSQL_HOST_PORT=3308`, rồi chạy lại Compose. File này được Git bỏ qua; backend vẫn dùng `mysql:3306` trong mạng Docker.

Tài liệu frontend: [frontend/README.md](frontend/README.md). Tài liệu retrieval và AI: [docs/retrieval_data_contract_vi.md](docs/retrieval_data_contract_vi.md).

Catalog 46.923 phim và CSV ID từ bảng `movies`: xem [mapping, index GPU và audit sau integration](docs/mapped_catalog_run_vi.md). Dùng JSONL mới trong `data/raw`; snapshot 11.347 phim trong `data/processed` là bản cũ. Mapping không yêu cầu import MySQL local.
