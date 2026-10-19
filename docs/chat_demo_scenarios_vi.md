# Kịch bản demo chatbot WhatToWatch

Chỉ thực hiện sau [preflight và smoke tích hợp](chat_demo_release_vi.md). Dùng
catalog thật và tài khoản test. Trước khi quay màn hình, ghi thời điểm, commit
tích hợp, `ollama list` (tag/digest đang dùng), MySQL count, Qdrant count/status.
Ghi câu hỏi và response thật; title/ID bên dưới là điều kiện cần kiểm tra,
không phải kết quả đã quan sát trên stack này.

## 1. Gợi ý phim và mở chi tiết

1. Đăng nhập `http://127.0.0.1:3000/chat`, tạo hội thoại mới.
2. Hỏi: `Recommend a science fiction movie with a strong story.`
3. Ghi status, lời đáp, phim gợi ý và ID. Bấm phim gợi ý để mở trang chi tiết.
4. Đối chiếu ID số và title với bản ghi MySQL/các phim được trả về từ retrieval.
   Nếu `no_match` hay `insufficient_context`, ghi nguyên trạng thái và kiểm tra
   catalog/retrieval; đừng coi đó là demo gợi ý thành công.

Luồng UI dùng `POST /api/chat` với cookie `wtw_session`; API Spring lưu hội thoại
và gọi `POST /internal/chat`. Xem [hợp đồng hội thoại](chat_multiturn_contract.md).

## 2. Câu hỏi nối tiếp và memory

Trong cùng hội thoại, khi lượt trước gợi ý **một** phim, hỏi:
`Who directed that movie?` Nếu có nhiều phim, nêu rõ title của phim cần hỏi.
Kiểm tra câu trả lời dựa trên director của bản ghi catalog, không chỉ dựa vào
việc response có chữ. Tải lại trang, mở hội thoại từ danh sách và xác nhận hai
lượt vẫn có mặt, đúng thứ tự. Đây là kiểm tra persistence và chọn đúng tham chiếu;
không suy ra mọi câu hỏi memory đều đúng.

## 3. Bộ lọc ngôn ngữ tự nhiên

Hỏi: `Gợi ý phim hành động nhưng tránh phim kinh dị sau năm 2015.` Ghi các phim
được trả về; đối chiếu genres và năm trong MySQL. Giao diện không hiển thị mọi
trường `applied_filters`, nên có thể kiểm tra độc lập parser bằng API sau:

```bash
curl -fsS -H 'Content-Type: application/json' \
  -d '{"message":"Gợi ý phim hành động nhưng tránh phim kinh dị sau năm 2015."}' \
  http://127.0.0.1:8010/internal/chat/filters
```

Endpoint `/filters` không gọi Qdrant/Ollama; response của nó chứng minh bước
trích filter, không chứng minh phim được retrieval đúng. Kỳ vọng
`retrieval.genres=["Action"]`, `exclude_genres=["Horror"]` và `year_min=2016`
theo cách parser hiện hiểu chữ “sau”. Nếu response khác, ghi nhận lỗi parser
trước khi diễn giải kết quả retrieval.

## 4. Chi tiết và so sánh bằng tool

Chọn phim đã xuất hiện trong hội thoại và hỏi
`What is the release year of [exact title]?` rồi
`Compare [first exact title] and [second exact title].` Chỉ dùng
hai phim thực có trong catalog; ghi ID, `tool_name` (`movie_detail` hoặc
`compare_movies`) và dữ kiện nguồn. Tên tool có trong response của
`POST /internal/chat`, không nhất thiết được giao diện hiện ra. Nếu muốn minh
họa tool chắc chắn với context cố định, gọi API nội bộ với `movie_context` được
lấy từ catalog; báo rõ đó là kiểm tra tool riêng, không phải luồng retrieval UI.

## 5. Không đủ ngữ cảnh và xử lý lỗi

Để kiểm tra guard mà không phụ thuộc retrieval, gửi context rỗng tới AI API:

```bash
curl -fsS -H 'Content-Type: application/json' \
  -d '{"message":"Who directed this movie?","movie_context":[]}' \
  http://127.0.0.1:8010/internal/chat
```

Kỳ vọng `status=insufficient_context`, `movies=[]`; trường hợp này khác
`no_match` khi truy vấn catalog không có hit. Không cần cố ý tắt service khi
demo. Nếu hệ thống thật gặp lỗi AI, nhánh E2E trả HTTP 503 và không lưu lượt
assistant giả; ghi log và khôi phục service trước khi tiếp tục.

## Phiếu ghi nhận sau mỗi lượt

| Trường | Giá trị cần ghi |
|---|---|
| Câu hỏi, thời điểm, conversation ID | Nguyên văn và ID thực |
| Trạng thái, lời đáp, movie IDs | Response thực, gồm lỗi nếu có |
| Dữ kiện đối chiếu | MySQL movie ID, title, director/genre/year liên quan |
| Hạ tầng | Commit tích hợp, model tag/digest, Qdrant/MySQL count |
| Kết luận | Đạt/chưa đạt theo từng bước; phân biệt UI, retrieval, tool và model |

Chấm chất lượng base/fine-tuned bằng bộ evaluation và reviewer riêng theo
[runbook](chat_demo_release_vi.md#bằng-chứng-hiện-có-và-phần-chưa-được-chấm),
không dùng vài câu demo để kết luận model nào tốt hơn.
