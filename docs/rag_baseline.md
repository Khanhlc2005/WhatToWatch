# RAG chatbot và baseline context mẫu

`POST /internal/chat` nhận `message`, `filters` JSON tùy chọn và `movie_context` tùy chọn. Khi bỏ `movie_context`, service chạy hybrid retrieval trên Qdrant, lấy tối đa 10 ứng viên, tra chi tiết phim từ Spring Boot/MySQL, rồi đưa tối đa 5 phim đã xác minh vào prompt. Phim không có MySQL ID hợp lệ, không tồn tại trong backend hoặc có IMDb/TMDB ID lệch nhau sẽ bị bỏ qua. `movie_id` trong câu trả lời là MySQL ID dạng chuỗi để mở đúng trang phim.

`movie_context` tường minh vẫn dùng được cho baseline và kiểm thử. Ba phim mẫu trong `ai-service/app/data/sample_movie_context.json` không còn là dữ liệu mặc định của chat. Chúng được rút từ `data/seeds/movies_cleaned_sample.jsonl`; `tests/test_rag.py` đối chiếu ID, tên, thể loại, mô tả và đạo diễn với nguồn đó. Truyền `movie_context: []` nghĩa là **không có context**, không gọi Ollama. Phim chỉ có ID/tên cũng là context hợp lệ; khi thiếu dữ kiện cần thiết, API trả `insufficient_context`.

```json
{
  "message": "Gợi ý phim về du hành vũ trụ",
  "movie_context": [
    {
      "movie_id": "tmdb:157336",
      "title": "Interstellar",
      "year": 2014,
      "genres": ["Adventure", "Drama", "Science Fiction"],
      "overview": "The adventures of a group of explorers who make use of a newly discovered wormhole to surpass the limitations on human space travel and conquer the vast distances involved in an interstellar voyage.",
      "director": "Christopher Nolan",
      "runtime_minutes": 169
    }
  ]
}
```

Phản hồi gồm `status` (`answered`, `no_match`, `insufficient_context`), `answer`, `movies` và `reply` để tương thích với client chat cũ. Mỗi phim trong `movies` có `movie_id`, `title`, `reason`. `reply` ghép `answer` với danh sách phim đã qua kiểm tra. Trường `system_prompt` cũ vẫn được nhận nhưng không được dùng, vì baseline cần một prompt cố định để giữ câu trả lời trong context.

Context builder lấy tên, overview, ngày phát hành, thời lượng và đạo diễn từ backend; thể loại từ payload Qdrant sau khi ID phim đã được đối chiếu. Overview được giới hạn 1.200 ký tự/phim để giữ prompt có kích thước hữu hạn. Khi retrieval không trả phim, API trả `no_match` mà không gọi Ollama; khi các hit không thể xác minh/lấy chi tiết, API trả `insufficient_context`. Qdrant hoặc backend không khả dụng trả `503`, không dùng phim mẫu làm fallback.

Prompt yêu cầu model chỉ dùng context, trả JSON, không làm theo chỉ dẫn nằm trong dữ liệu phim. Ollama nhận [JSON Schema trong trường `format`](https://github.com/ollama/ollama/blob/main/docs/capabilities/structured-outputs.mdx). Service parse JSON, kiểm tra schema, loại phim lặp, kiểm tra cặp ID/tên phim với context đầu vào và thử lại một lần nếu kết quả sai format hoặc sai nguồn. Nếu vẫn sai, API trả `502` và không chuyển câu trả lời đó cho client. Context đầu vào có ID trùng trả `422`; Ollama không kết nối được trả `503`. Context rỗng hoặc thiếu dữ kiện trả `insufficient_context`; nếu context có phim nhưng không phim nào phù hợp, model phải trả `no_match` với `movies: []`. Phần `answer` và `reason` công khai được dựng lại từ phim đã xác thực, nên tên phim hoặc dữ kiện ngoài context trong lời văn tự do của model không được chuyển tiếp.

## Chạy

```bash
pip install -r requirements.txt
cd ai-service
uvicorn app.main:app --reload --port 8010
pytest -q
```

Đặt `OLLAMA_BASE_URL`, `OLLAMA_MODEL_NAME` và `BACKEND_BASE_URL` nếu khác `http://localhost:11434`, `qwen2.5:3b` và `http://localhost:8080/movie-recommendation`. Trong Docker Compose, `BACKEND_BASE_URL` trỏ tới `http://backend:8080/movie-recommendation`. Luồng mặc định cần Qdrant đã được index bằng các MySQL ID tương ứng và backend đang chạy. Để hỏi trên catalog thật:

```bash
curl -sS http://localhost:8010/internal/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"Gợi ý phim về du hành không gian"}'
```

Để thử riêng baseline ba phim mẫu với model thật và lưu câu hỏi/kết quả:

```bash
python scripts/run_rag_cases.py
```

Kết quả được ghi vào `docs/evidence/rag_baseline_results.jsonl`, gồm câu hỏi, ID phim trong context, trạng thái mong đợi, phản hồi thực tế, thời gian và lỗi nếu có. Script thoát với mã lỗi nếu ca nào thất bại. `tests/test_chat_retrieval.py` kiểm tra riêng đường retrieval → catalog → context → chatbot, gồm cả lỗi backend và ID không khớp.

Với `qwen2.5:3b` cục bộ, 5/5 ca chính đạt ở lần chạy cuối; `docs/evidence/rag_baseline_initial_results.jsonl` lưu lần chạy đầu để thấy lỗi format trước khi bổ sung JSON Schema. Đây là kiểm tra baseline trên ba phim mẫu, chưa đo chất lượng trên dữ liệu retrieval hoặc truy vấn ngoài bộ ca trên.
