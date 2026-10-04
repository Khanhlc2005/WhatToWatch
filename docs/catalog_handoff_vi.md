# Hướng dẫn tải và làm sạch catalog phim

Bản sao **`dữ liệu.jsonl`** bên ngoài ZIP chứa 11.347 phim đã làm sạch.
Các file **`script.sh` / `script.py`** nằm trong thư mục `catalog_handoff` sau khi giải nén.

## Bước 1 — Chuẩn bị
Cài **Python 3.10 trở lên**, giải nén `catalog_handoff.zip` rồi mở Terminal trong thư mục `catalog_handoff`.
Dùng mạng không giới hạn dung lượng, nên có khoảng 15 GB ổ đĩa trống (ước lượng, tùy kích thước metadata) và giữ máy thức.

## Bước 2 — Chạy một lệnh
**Linux/macOS hoặc Windows dùng WSL/Git Bash:** chạy lệnh dưới; file Bash tự tạo môi trường và cài thư viện cần thiết.

```bash
bash script.sh
```

**Windows không có Bash:** chạy `py script.py` (hoặc `python script.py`); script cũng tự cài thư viện.

## Bước 3 — Nhập API key
Lấy TMDB API key v3 từ file `.env` gửi kèm bên ngoài ZIP và nhập khi được hỏi, rồi chờ; key không hiện khi nhập và không lưu vào gói.
Script tự tiếp tục checkpoint → tải đến đủ 100.000 phim sạch tổng cộng → làm sạch → tạo văn bản embedding → xuất JSONL → kiểm tra dữ liệu.

## Bước 4 — Gửi kết quả
Gửi file chính **`data/processed/movies_cleaned_full.jsonl`** cùng `run_summary.json`, `validation.json` và hai file `movies_cleaned_full_rejected.jsonl`, `movies_cleaned_full_unmatched.jsonl`.
Đọc `run_summary.json`: `target_reached=true` và `validation_passed=true` xác nhận đủ mục tiêu và kiểm tra tự động đạt. `complete=false` là bình thường vì không xử lý hết catalog.

## Bước 5 — Nếu mất mạng hoặc cần nghỉ
Nhấn **Ctrl+C một lần**, chờ lưu xong; khi chạy tiếp chỉ cần dùng lại lệnh ở bước 2.
Không xóa `catalog.sqlite`/`tmdb_cache`, không chạy hai cửa sổ cùng lúc.

## Thông tin cần biết
- Bộ này dừng ở **100.000 phim sạch tổng cộng**, gồm **11.347 phim đã có**, tức cần thêm **88.653 phim sạch**. Catalog 215.409 ứng viên được giữ để bù phim lỗi/không mapping; phim đó không tính vào mục tiêu. Chạy lại vẫn giữ cùng mốc 100.000, không cộng thêm 100.000. Không áp dụng hạn mức hotspot 6 GB của máy gửi.
- Đầu ra đã làm sạch; chưa tạo vector hoặc import MySQL/Qdrant, không tải ảnh/video/model.
- Mặc định 2 request/giây, có thể mất hơn một ngày; mạng nhanh hơn không loại bỏ giới hạn tốc độ của script/API.
- Muốn xuất phần đã có mà không tải: `python script.py --offline` (Windows có thể dùng `py`).
- Linux thiếu `venv`: cài gói `python3-venv` rồi chạy lại; lỗi DNS/kết nối: kiểm tra mạng rồi chạy lại.
- Nếu chuyển tiếp cho máy khác, dừng trước rồi gửi cả bộ cùng `catalog.sqlite` và `tmdb_cache/`, bỏ `.catalog-venv/` và credentials.
