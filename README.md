# WhatToWatch

Ứng dụng web duyệt phim gồm frontend Next.js, backend Spring Boot và MySQL. Hướng dẫn dưới đây chạy phần web; AI service và Qdrant không cần thiết cho trang `/browse`.

## Yêu cầu

- Docker Desktop hoặc Docker Engine với Docker Compose; kiểm tra `docker info` có phần `Server`.
- Node.js và npm nếu muốn chạy frontend ngoài Docker.
- File `data/mysql/movies_data.sql` (nhận riêng từ người quản lý dữ liệu); Compose nạp file này vào MySQL khi tạo volume mới.

Trên Linux dùng Docker Desktop, có thể khởi động bằng `systemctl --user start docker-desktop` rồi chọn `docker context use desktop-linux`. Nếu Docker Desktop không lên vì thiếu RAM, đóng bớt ứng dụng trước khi thử lại.

## 1. Chạy MySQL và backend

Tại thư mục gốc của repo:

```bash
docker compose up -d --build mysql backend frontend
docker compose ps
```

`docker compose ps` phải hiện `mysql`, `backend` và `frontend` thuộc **project của thư mục này**. Mở `http://localhost:3000/browse`; backend phục vụ ở `http://localhost:8080/movie-recommendation`. MySQL dùng cổng `3306` trong mạng Docker. Chờ backend khởi động xong, rồi kiểm tra:

```bash
curl http://localhost:8080/movie-recommendation/movies/home-feed/top-rated
```

Nếu nhận `{"code":1000,"result":[]}`, backend đã hoạt động nhưng chưa có phim; làm bước 2. Nếu không kết nối được, xem `docker compose logs --tail=80 backend mysql`.

## 2. Kiểm tra dữ liệu phim

Backend đọc bảng `movies`. Compose mount `data/mysql/movies_data.sql` vào MySQL và tự nạp khi volume MySQL được tạo lần đầu. Dump hiện tại có 46.923 phim với ID khớp CSV mapping dùng cho Qdrant. Init script của MySQL không chạy lại trên volume đã tồn tại; kiểm tra trước khi thao tác với dữ liệu cũ.

```bash
docker exec -e MYSQL_PWD=root whattowatch-mysql mysql -u root -N whattowatch_db -e 'SELECT COUNT(*) FROM movies;'
```

Với dump hiện dùng, kết quả là `46923`. Khi dùng volume MySQL mới, tài khoản và danh sách cá nhân từ volume khác không tự chuyển sang.

## 3. Chạy frontend ngoài Docker (tùy chọn)

Tạo `frontend/.env.local` nếu chưa có, theo mẫu `frontend/.env.example`. Giữ `BACKEND_URL=http://localhost:8080/movie-recommendation`. Điền `TMDB_KEY` và `YOUTUBE_API_KEY` để tự tìm trailer cho phim chưa có trailer trong SQL. File `.env.local` được Git bỏ qua; không đưa khóa API vào commit.

```bash
cd frontend
cp -n .env.example .env.local
npm ci
npm run dev
```

Mở `http://localhost:3000/browse`. Nếu vừa sửa `.env.local`, khởi động lại frontend để Next.js đọc giá trị mới. Dùng `Ctrl+C` để dừng frontend; tại thư mục gốc, `docker compose down` dừng backend/MySQL nhưng giữ volume dữ liệu. Không dùng `docker compose down -v` nếu muốn giữ cơ sở dữ liệu.

Ở những lần chạy sau, chỉ cần `docker compose up -d` nếu dùng frontend trong Compose; dữ liệu trên volume MySQL được giữ lại.

`ai-service` nằm trong profile `ai` nên `docker compose up -d` **không** khởi động nó. Khi AI tắt, hàng "For you" ở trang Home báo "Recommendations are temporarily unavailable" và chatbot báo "the AI service is currently unavailable". Chạy thêm `docker compose --profile ai up -d ai-service` (xem mục AI Search bên dưới) rồi tải lại trang.

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

Demo chatbot và trạng thái tích hợp: [runbook phát hành](docs/chat_demo_release_vi.md)
và [kịch bản thao tác](docs/chat_demo_scenarios_vi.md).

Catalog 46.923 phim và CSV ID từ bảng `movies`: xem [mapping, index GPU và audit sau integration](docs/mapped_catalog_run_vi.md). Dùng JSONL mới trong `data/raw`; bản xuất 11.347 phim cũ trong `data/processed` đã được dọn ngày 14/10/2026 vì toàn bộ metadata đã nằm trong catalog hiện tại. SQLite checkpoint và cache vẫn được giữ để tiếp tục thu thập. Mapping không yêu cầu import MySQL local.

## Qdrant với catalog 46.923 phim

`docker compose up -d qdrant` tạo Qdrant và volume riêng trên **máy đang chạy lệnh**. Git không chứa volume hoặc catalog đã index, vì vậy clone repo mới sẽ không tự có 46.923 phim. Compose dùng Qdrant v1.19.0 (phiên bản tạo snapshot) và mở cổng `127.0.0.1:6335` mặc định. Nếu cổng bận, đặt `QDRANT_HOST_PORT` trong `.env` theo `.env.example`, đồng thời đổi `QDRANT_URL` cho các lệnh chạy trên host. Container AI trong Compose kết nối nội bộ qua `http://qdrant:6333`.

Để chạy trên volume riêng của đồng đội, lấy file `movies-46923-2026-10-11.snapshot` từ người giữ catalog và đặt tại `data/processed/` (file 341 MiB, Git bỏ qua). Kiểm tra SHA-256 `9f98db41930a8d70f11692afb74e6b5dac5638cefb2d86b9dd6f03d30c3bf975`. **Chỉ phục hồi trên volume mới, chưa có collection `movies`**; lệnh upload snapshot sẽ ghi vào collection đích. Tại thư mục gốc repo:

```bash
cp -n .env.example .env
docker compose up -d qdrant
export QDRANT_URL=http://127.0.0.1:6335 # Đổi cổng ở đây nếu QDRANT_HOST_PORT khác 6335.
sha256sum data/processed/movies-46923-2026-10-11.snapshot
# Lệnh sau phải trả HTTP 404 trước khi phục hồi.
curl -s -o /dev/null -w '%{http_code}\n' "$QDRANT_URL/collections/movies"
curl -fsS -X POST \
  "$QDRANT_URL/collections/movies/snapshots/upload?priority=snapshot" \
  -F 'snapshot=@data/processed/movies-46923-2026-10-11.snapshot'
curl -fsS "$QDRANT_URL/collections/movies"
curl -fsS -H 'Content-Type: application/json' \
  -d '{"exact":true}' \
  "$QDRANT_URL/collections/movies/points/count"
```

Kết quả mong đợi là collection `green`, dense 1024/Cosine + sparse, và `count=46923`. Nếu collection đã có dữ liệu, dừng trước lệnh upload và kiểm tra volume hiện tại; không xóa collection để làm lại. Snapshot chứa vectors và payload `movie_id`, nên không cần GPU để phục hồi. Muốn dùng trực tiếp Qdrant trên máy giữ dữ liệu qua SSH, đồng đội có thể tạo tunnel `ssh -N -L 6335:127.0.0.1:6335 user@host`; Qdrant sẽ hiện ở `http://localhost:6335` trên máy họ khi tunnel và container nguồn đang chạy. Không mở cổng Qdrant trực tiếp ra Internet.

### Dung lượng AI trên máy đồng đội

Nếu chỉ cần dữ liệu Qdrant, chạy `docker compose up -d qdrant`; lệnh này không build AI image và không tải BGE-M3. Khi cần chạy AI Search, mới dùng `docker compose --profile ai up -d --build qdrant ai-service`. Dockerfile AI của repo cài PyTorch bản CPU; không cần CUDA image để tìm kiếm trên CPU. BGE-M3 vẫn cần cho việc biến câu hỏi mới thành vector. `.dockerignore` loại cache model và môi trường Python cục bộ khỏi build context, nên chúng không bị gửi vào quá trình build.

### Chatbot trên CPU

Chat qua backend cần đăng nhập. Máy không có GPU có thể mất thêm thời gian ở lần hỏi đầu vì BGE-M3 và Qwen phải nạp vào bộ nhớ. Các ngưỡng mặc định: AI chờ Ollama tối đa 300 giây, backend chờ AI chat 390 giây, backend chờ AI search 35 giây và frontend chờ search 45 giây. AI giới hạn 4 luồng embedding CPU; có thể chỉnh `EMBEDDING_CPU_THREADS`, `OLLAMA_READ_TIMEOUT_SECONDS`, `AI_SERVICE_CHAT_TIMEOUT_SECONDS` và `AI_SERVICE_SEARCH_TIMEOUT_SECONDS` trong `.env` ở thư mục gốc. Giữ timeout backend chat lớn hơn timeout Ollama để backend nhận được lỗi thực thay vì ngắt trước.

Nếu Ollama trên Linux chỉ lắng nghe `127.0.0.1:11434`, đặt `OLLAMA_BASE_URL=http://host.docker.internal:11435` trong `.env` và chạy `docker compose --profile ai --profile ai-local up -d --build`. Profile `ai-local` mở proxy trên Docker bridge `172.17.0.1:11435`, không mở ra LAN. Nếu Docker bridge dùng IP khác, đặt `OLLAMA_PROXY_BIND` trong `.env`. Khi Ollama đã lắng nghe trên địa chỉ Docker truy cập được, dùng `--profile ai` và URL tương ứng, không cần proxy.

Trên máy có báo đầy ổ, kiểm tra riêng image, build cache và volume bằng `docker system df -v`; kích thước của từng image trong `docker image ls` không cộng trực tiếp vì các image có thể chia sẻ layer. Nếu build cache cũ chiếm nhiều chỗ, `docker builder prune` chỉ xóa cache build không còn dùng; lệnh này không xóa Qdrant volume, nhưng lần build sau có thể phải tải lại dependencies. Không dùng `docker compose down -v` hoặc `docker system prune --volumes` với volume Qdrant đang giữ catalog.
