# WhatToWatch frontend

Next.js interface for registration, login, home feed and movie details. Browser requests go through Next.js API routes to the Spring Boot backend.

See the repository root README for MySQL setup and backend commands. Docker is optional when MySQL is already installed.

From `frontend/`:

```bash
cp .env.example .env.local
npm ci
npm run dev
```

Open http://localhost:3000 for the WhatToWatch landing page. Register at `/register`, log in at `/login`, then browse at `/browse`. Movie details are available at `/movies/[id]`. `BACKEND_URL` defaults to `http://localhost:8080/movie-recommendation`.
## Duyệt và lưu phim

- `/browse`: phim đánh giá cao và mới phát hành; banner chọn ngẫu nhiên một phim trong top 10 đánh giá cao.
- `/search`: tìm theo tên phim trong bảng `movies` của backend. Đây là tìm kiếm tên, chưa dùng API tìm kiếm ngữ nghĩa của AI service.
- `/library/favorites` và `/library/watchlist`: danh sách cá nhân, yêu cầu đăng nhập. Nút trên thẻ phim và màn chi tiết gọi API backend qua Next.js; JWT chỉ nằm trong cookie HttpOnly.
- Màn chi tiết tự phát trailer YouTube ở chế độ tắt tiếng. Nguồn trailer được thử theo thứ tự: `trailer_key` trong SQL, TMDB movie videos theo `tmdb_id`, rồi YouTube Data API tìm theo tên phim, năm và `official trailer`. Kết quả tìm từ YouTube phải khớp tên/năm, có quyền nhúng và dài 30 giây đến 6 phút; nếu không tìm được thì giữ ảnh phim và liên kết tìm thủ công.
- Để bật tra cứu bổ sung, đặt `TMDB_KEY` (khóa TMDB v3) và `YOUTUBE_API_KEY` (YouTube Data API v3) trong `frontend/.env.local`, rồi khởi động lại Next.js. Khóa chỉ dùng ở API phía máy chủ. Có thể dùng riêng từng khóa; thiếu cả hai thì chỉ trailer đã lưu trong SQL hoạt động. Kết quả tra cứu được lưu trong bộ nhớ tiến trình: 7 ngày nếu có video, 6 giờ nếu không có; cache mất khi khởi động lại.
- Màn chi tiết cũng có mô tả, diễn viên khi có dữ liệu, và phim gợi ý cùng ngôn ngữ gốc phát hành trong khoảng 5 năm quanh phim đang xem. Bộ SQL hiện tại chưa có bản ghi trong `movie_cast`, nên phần diễn viên sẽ báo chưa có dữ liệu.
