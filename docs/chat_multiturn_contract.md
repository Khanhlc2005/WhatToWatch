# Chat nhiều lượt (P0)

Trang `/chat` dùng cookie `wtw_session` qua các API Next.js; browser không giữ JWT trong JavaScript.

## Hợp đồng browser ↔ backend

- `POST /api/chat`: `{ "conversationId": null | number, "message": string }`. `null` tạo cuộc hội thoại mới. Trả `{ conversationId, status, reply, recommendedMovies, createdAt }`.
- `GET /api/chat/conversations`: danh sách `{ id, title, updatedAt }` của người đang đăng nhập.
- `GET /api/chat/conversations/{id}`: `{ id, title, messages }`, mỗi tin nhắn có `{ id, role, content, recommendedMovies, createdAt }`.
- `DELETE /api/chat/conversations/{id}`: xóa cuộc hội thoại của người đang đăng nhập.

`status` có các giá trị `answered`, `no_match`, `insufficient_context`, `error`. Mỗi phim trong `recommendedMovies` có `movie_id`, `title`, `reason`; `movie_id` trỏ tới `/movies/{id}`. Phản hồi lượt mới còn có `appliedFilters` và `toolName` để kiểm tra bộ lọc đã áp dụng và đường trả lời.

## Hợp đồng backend ↔ AI service

Spring Boot lưu tin nhắn, lấy tối đa 10 tin nhắn trước lượt hiện tại theo thứ tự thời gian, rồi gọi `POST /internal/chat` với `{ message, history, summary }`. Mỗi phần tử `history` gồm `role` (`user` hoặc `assistant`), `content`, `movie_ids`. `movie_ids` của assistant được lấy từ phim đã gợi ý và lưu trong MySQL. Tin nhắn đang gửi chỉ có trong `message`, không lặp trong `history`. Các tin nhắn cũ hơn được rút gọn vào `conversations.summary`; `summary_through_message_id` ngăn tóm tắt lặp khi sang lượt tiếp theo.

AI service dùng summary và lịch sử để hiểu câu hỏi nối tiếp. Với tham chiếu như “phim đó”, các ID phim từng gợi ý được lấy chi tiết lại từ catalog backend trước khi tạo ngữ cảnh. Summary và lịch sử không được dùng làm nguồn dữ kiện phim; câu trả lời vẫn phải dựa vào `MOVIE_CONTEXT` hoặc kết quả tool đọc catalog.
