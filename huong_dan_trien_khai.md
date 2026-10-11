HƯỚNG DẪN TRIỂN KHAI VÀ KHỞI CHẠY DỰ ÁN WHATTOWATCH
PHẦN 1: CHUẨN BỊ DỮ LIỆU ĐẦU VÀO
Cần chuẩn bị sẵn các file dữ liệu (không có trên GitHub do dung lượng lớn).
Truy cập thư mục gốc của dự án: WhatToWatch/
Đặt 2 file dữ liệu sau vào thư mục data/raw/ (tạo thư mục nếu chưa có):
movies_cleaned_full.jsonl
Đặt file sau vào thư mục data/processed/ (tạo thư mục nếu chưa có):
movies_id_mapping.csv
PHẦN 2: ĐỒNG BỘ MÃ NGUỒN TỪ GITHUB
Mở Terminal hoặc CMD tại thư mục gốc của dự án WhatToWatch và chạy lệnh đồng bộ mã nguồn mới nhất:
Bash
git pull origin main
(File cấu hình docker-compose.yml hiện tại đã được thiết lập tự động mount file dump movies_data.sql vào MySQL container).
PHẦN 3: CẤU HÌNH VÀ KHỞI ĐỘNG OLLAMA (CHẠY GPU)
Yêu cầu khởi chạy Ollama để lắng nghe kết nối từ Docker và sử dụng card đồ họa (GPU).
Mở một cửa sổ CMD/Terminal mới (giữ cửa sổ này chạy ngầm trong suốt quá trình sử dụng hệ thống).
Thiết lập môi trường và chạy Ollama:
Trên Windows (CMD):
DOS
set OLLAMA_HOST=0.0.0.0:11434
ollama serve
Trên Linux/macOS:
Bash
OLLAMA_HOST=0.0.0.0:11434 ollama serve
Mở thêm 1 tab CMD/Terminal khác để tải model AI (nếu chưa có sẵn trên máy):
DOS
ollama pull qwen2.5:3b
PHẦN 4: KHỞI CHẠY HỆ THỐNG DOCKER COMPOSE
Quay lại cửa sổ CMD tại thư mục gốc của dự án và thực hiện lệnh build và khởi chạy các container:
Bash
docker compose up -d --build
Quá trình này sẽ tự động:
Biên dịch lại mã nguồn Spring Boot thành file .jar mới nhất.
Khởi tạo MySQL, tự động đọc file movies_data.sql để tạo bảng và nạp 46,000 phim vào database whattowatch_db.
Khởi động Qdrant và AI-Service.
Xác minh: Chạy lệnh docker ps. Yêu cầu cả 4 container (mysql, qdrant, ai-service, backend) đều có trạng thái Up.
PHẦN 5: CHUẨN BỊ VÀ NẠP DỮ LIỆU VECTOR VÀO QDRANT (INDEXING)
Để kích hoạt tính năng Hybrid Search, bạn cần ánh xạ ID từ MySQL sang file dữ liệu gốc, sau đó nạp vector vào Qdrant.
Ghép ID (Mapping): Mở CMD/Terminal tại thư mục gốc dự án và chạy lệnh sau để ghép movie_id vào dữ liệu phim:
Bash
python data/scripts/map_mysql_ids.py --movies data/raw/movies_cleaned_full.jsonl --mysql-csv data/processed/movies_id_mapping.csv --output data/processed/movies_with_mysql_ids.jsonl
Nạp Vector (Indexing): Chạy tiếp script nạp vector vào Qdrant bằng GPU:
Đối với môi trường Linux/Mac hoặc Git Bash/WSL:
Bash
bash run_catalog_gpu.sh
Đối với Windows (chạy trực tiếp Python):
Bash
python qdrant/scripts/index_catalog.py --input data/processed/movies_with_mysql_ids.jsonl --url http://localhost:6335 --device cuda:0 --batch-size 4 --chunk-size 64
Đợi script chạy hoàn tất.
PHẦN 6: KIỂM TRA HỆ THỐNG (TEST API)
Sử dụng phần mềm Postman để gửi request kiểm tra tính toàn vẹn của luồng xử lý từ Backend đến AI Service.
Method: POST
URL: http://localhost:8080/movie-recommendation/chat
Body (chọn raw -> JSON):
JSON
{
  "message": "Can you recommend a great movie about space travel and father-daughter relationship?"
}
Bấm Send.
Kết quả mong đợi: Hệ thống trả về HTTP Status 200 kèm phản hồi JSON. Nội dung bao gồm trường reply (đoạn văn bản phân tích từ Ollama) và trường recommendedMovies (mảng chứa dữ liệu các bộ phim gợi ý, ví dụ: Interstellar). Nếu nhận được dữ liệu này, hệ thống đã hoạt động bình thường.