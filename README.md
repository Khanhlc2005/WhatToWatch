# WhatToWatch

Movie discovery app with Spring Boot backend and a Next.js frontend in `nextflix/`. AI service and Qdrant are separate work in progress.

## Chạy toàn bộ ứng dụng (cấu hình hiện tại)

Cấu hình này dùng **Docker Desktop cho MySQL và Spring Boot**, còn UI Next.js chạy trong thư mục `nextflix/`. Cần có Docker Desktop, Node.js 18 và npm. Chạy các lệnh Docker Compose tại thư mục gốc `WhatToWatch`, nơi có `docker-compose.yml` với hai service `mysql`, `backend`.

### 1. Khởi động backend và database — terminal thứ nhất

Trên Ubuntu, bật Docker Desktop rồi chạy Compose tại thư mục gốc dự án:

```bash
systemctl --user start docker-desktop
docker compose up -d --build
docker compose ps
```

Nếu stack ở `WhatToWatch-docker` còn chạy, hãy dừng nó bằng `docker compose down` trong thư mục đó trước khi khởi động stack này để tránh trùng tên container và cổng. Stack ở thư mục này dùng Docker volume riêng, nên dữ liệu MySQL cũ không tự chuyển sang. Cả `whattowatch-mysql` và `whattowatch-backend` cần ở trạng thái `Up`. Những lần tiếp theo có thể dùng `docker compose up -d`; sau khi sửa backend, dùng `docker compose up -d --build`. Nếu cổng `3306` đã được MySQL cài trên máy sử dụng, dừng MySQL local bằng `sudo systemctl stop mysql` rồi chạy lại Compose.

**Chỉ khi database chưa có phim:** đặt `movies_data.sql` ở thư mục gốc `WhatToWatch`, sau đó chạy các lệnh sau tại thư mục gốc `WhatToWatch`:

```bash
python3 tools/prepare_movies_sql.py movies_data.sql /tmp/movies_data_compatible.sql
docker exec -i -e MYSQL_PWD=root whattowatch-mysql mysql -u root whattowatch_db < /tmp/movies_data_compatible.sql
docker exec -i -e MYSQL_PWD=root whattowatch-mysql mysql -u root whattowatch_db < data/mysql/sample_trailers.sql
```

File SQL gốc thiếu `id`, `created_at`, `updated_at`, nên cần bước chuẩn bị trước khi import. **Không import lại sau mỗi lần khởi động** vì sẽ tạo bản ghi trùng. Kiểm tra số phim:

```bash
docker exec -e MYSQL_PWD=root whattowatch-mysql mysql -u root whattowatch_db -e 'SELECT COUNT(*) FROM movie;'
```

### 2. Khởi động UI — terminal thứ hai

Mở terminal khác tại thư mục gốc `WhatToWatch`, rồi chạy:

```bash
cd nextflix
npm run dev
```

Lần đầu chạy UI, thực hiện `cp .env.example .env.local` và `npm ci` trong `nextflix/` **trước** `npm run dev`. File `.env.local` cần có `BACKEND_URL=http://localhost:8080/movie-recommendation`. Giữ terminal UI mở khi sử dụng.

Mở [http://localhost:3000/browse](http://localhost:3000/browse). Kiểm tra backend tại [http://localhost:8080/movie-recommendation/movies/home-feed/top-rated](http://localhost:8080/movie-recommendation/movies/home-feed/top-rated).

### 3. Dừng ứng dụng

Dừng UI bằng `Ctrl+C` trong terminal thứ hai. Tại thư mục gốc `WhatToWatch`, chạy `docker compose down` để dừng backend và MySQL; lệnh này giữ nguyên dữ liệu trong Docker volume.

## Cách khác: chạy backend local với MySQL đã cài sẵn

Yêu cầu: Java 21, Node.js 18, npm và MySQL 8. Trên Ubuntu, kiểm tra MySQL bằng `systemctl is-active mysql`.

1. Mở MySQL bằng `sudo mysql` (nhập mật khẩu đăng nhập Ubuntu nếu được hỏi) và chạy SQL sau. Thay `your-password` bằng mật khẩu riêng của bạn:

   ```sql
   CREATE DATABASE IF NOT EXISTS `movie-recommendation` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   CREATE USER IF NOT EXISTS 'whattowatch'@'localhost' IDENTIFIED BY 'your-password';
   ALTER USER 'whattowatch'@'localhost' IDENTIFIED BY 'your-password';
   GRANT ALL PRIVILEGES ON `movie-recommendation`.* TO 'whattowatch'@'localhost';
   EXIT;
   ```

2. Xác nhận tài khoản có thể kết nối trước khi chạy backend. Lệnh sau sẽ hỏi mật khẩu MySQL:

   ```bash
   mysql -h 127.0.0.1 -u whattowatch -p -D movie-recommendation -e 'SELECT 1;'
   ```

   Nếu có `Access denied`, chạy lại `ALTER USER` và `GRANT` ở bước 1. Sau đó chạy backend trong terminal thứ nhất. Script hỏi mật khẩu của tài khoản `whattowatch` và nhập kín, không lưu trong lịch sử lệnh:

   ```bash
   cd backend
   ./run-local.sh
   ```

   Backend chạy tại http://localhost:8080/movie-recommendation. Cờ demo chỉ chèn ba phim khi bảng `movie` rỗng.

3. Trong terminal thứ hai, chạy frontend:

   ```bash
   cd nextflix
   cp .env.example .env.local
   npm ci
   npm run dev
   ```

4. Mở http://localhost:3000 để xem trang mở đầu Nextflix gốc. Vào `/register` để tạo tài khoản, đăng nhập ở `/login`, rồi xem home tại `/browse`. Chọn phim để mở chi tiết trong modal gốc tại `/movies/{id}`. Trang browse và chi tiết cũng xem được khi chưa đăng nhập.

## Nếu chỉ dùng Docker Compose cho MySQL

Nếu máy đã có Docker, có thể dùng `docker compose up -d mysql` thay bước tạo MySQL ở trên. Compose tạo database và tài khoản root phát triển với mật khẩu mặc định `root`; backend có cấu hình mặc định tương ứng.

`BACKEND_URL` trong `nextflix/.env.local` mặc định là `http://localhost:8080/movie-recommendation`. Đặt `JWT_SIGNER_KEY` riêng trước khi triển khai ngoài môi trường local.

Kiểm tra build: `cd backend && ./mvnw test`; `cd nextflix && npm run lint && npm run build`.