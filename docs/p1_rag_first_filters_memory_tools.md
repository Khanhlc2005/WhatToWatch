# P1 — RAG-first, filter, memory và catalog tools

Luồng `POST /internal/chat`:

1. Trích filter từ câu hỏi thành `applied_filters.retrieval` theo schema `MovieFilters`. Các trường Qdrant hỗ trợ: `genres`, `exclude_genres`, `languages`, `countries`, `year_min`, `year_max`, `rating_min`, `runtime_max`. JSON filter do client gửi được xác thực và ghi đè các trường tương ứng trích từ câu hỏi. Tên đạo diễn/diễn viên nằm ở `applied_filters.director` và `.actor`; hai trường này lọc trên chi tiết phim backend vì payload Qdrant không có person fields.
   `POST /internal/chat/filters` trả đúng JSON đã chuẩn hóa để kiểm tra độc lập, không gọi Qdrant hay Ollama.
2. Hybrid retrieval → đối chiếu ID với phim MySQL qua backend → ngữ cảnh tối đa 5 phim. Không dùng dữ liệu hội thoại làm nguồn dữ kiện phim.
3. Câu hỏi dữ kiện một phim dùng `movie_detail`; câu hỏi so sánh hai phim dùng `compare_movies`. Tool đọc lại chi tiết phim từ backend và tạo câu trả lời từ trường có thật; nếu thiếu hoặc không xác định được phim, trả `insufficient_context`/`no_match`. Câu hỏi gợi ý dùng Qwen2.5 3B với JSON Schema; hệ thống kiểm tra ID, tên phim và dữ kiện trả lời.
4. Backend lưu tin nhắn trong MySQL. Mỗi lượt gửi `summary` tối đa 1.600 ký tự của phần hội thoại cũ cùng tối đa 10 tin nhắn gần nhất, theo thứ tự thời gian. `summary_through_message_id` tránh đưa tin nhắn vào summary nhiều lần. Câu hỏi hiện tại chỉ nằm ở `message`.

Kiểm tra mã: `PYTHONPATH=ai-service ai-service/.venv/bin/python -m pytest -q ai-service/tests` và `cd backend && mvn -Dtest=ConversationServiceTest test`. Các ca mới kiểm tra filter JSON, giá trị âm/ngoài khoảng, người dùng hỏi đạo diễn không bị hiểu là filter tên người, summary trong prompt, tool chi tiết/so sánh và nguồn catalog.

Giới hạn môi trường hiện tại: Qdrant trên máy đã tạo volume rỗng nhưng chưa có snapshot 46.923 phim; chưa thể đo chất lượng retrieval/chat trên catalog thật. Cần phục hồi snapshot đã xác minh rồi chạy smoke end-to-end. Sau lần thử Ollama, Docker Desktop từng bị OOM kill; không chạy lại inference khi tài nguyên chưa đủ.
