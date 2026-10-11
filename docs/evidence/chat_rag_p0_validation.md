# Kiểm tra chat RAG với catalog — 2026-10-11

Nhánh: `feature/chat-rag-retrieval`.

## Kiểm thử tự động

- `PYTHONPATH=ai-service ai-service/.venv/bin/python -m pytest -q ai-service/tests`: **148 passed**, 1 cảnh báo Starlette TestClient deprecated.
- Các ca mới dùng Qdrant in-memory để kiểm tra hybrid retrieval → MySQL detail response → context builder → structured answer, kể cả filter rỗng kết quả, ID không khớp, phim thiếu trong MySQL, backend/Qdrant lỗi và giới hạn 5 phim.
- `AiMovieSearchResponse.java` biên dịch riêng bằng `javac 21` cùng Lombok/Jackson. Maven wrapper trong repo thiếu `.mvn/wrapper/maven-wrapper.properties`, nên chưa chạy được build Maven đầy đủ.

## Smoke test với dữ liệu và model thật

- Backend/MySQL đang chạy trả phim `Interstellar`, MySQL ID `5853`, IMDb `tt0816692`, TMDB `157336`, ngày phát hành `2014-11-05`.
- Ollama đang chạy `qwen2.5:3b`. API `/internal/chat` đã gọi model thật và lấy chi tiết phim từ backend thật.
- Với câu hỏi **“Phim Interstellar phát hành năm nào?”**, phản hồi HTTP 200, `status=answered`, `movie_id=5853`, `answer="Phim phát hành năm 2014."`.
- Với câu hỏi **“Gợi ý một phim về hành trình khám phá không gian”**, phản hồi HTTP 200, `status=answered`, phim gợi ý có `movie_id=5853` và thể loại từ context.

Qdrant service không chạy và không có volume index trên máy ở thời điểm kiểm tra. Hai ca smoke dùng **Qdrant in-memory với point ID của phim thật và vector truy vấn cố định**; vì vậy chúng xác nhận đường gọi retrieval/context/MySQL/Ollama nhưng **chưa đo ranking ngữ nghĩa trên toàn catalog**. Cần chạy lại request mặc định sau khi collection `movies` được index với MySQL ID và BGE-M3 thật.
