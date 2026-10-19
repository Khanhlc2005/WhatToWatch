# Kiểm tra luồng chat từ giao diện tới AI

Luồng cần chạy: `/chat` → Next.js `/api/chat` (cookie `wtw_session`) → Spring
`/chat` (lưu hội thoại trong MySQL) → FastAPI `/internal/chat` (Qdrant, catalog,
Ollama) → câu trả lời và các `movie_id` trên giao diện.

## Chạy smoke trên môi trường tích hợp

Chuẩn bị MySQL, Qdrant đã có catalog, backend, AI service, frontend và Ollama với
model đang cấu hình trong `docker-compose.yml` (mặc định `qwen2.5:3b`). Dùng tài khoản test đã tồn tại. Không
đưa mật khẩu vào lệnh hoặc commit file chứa mật khẩu.

```bash
export WTW_E2E_EMAIL='test@example.com'
export WTW_E2E_PASSWORD='...'
python tools/chat_e2e_smoke.py --base-url http://127.0.0.1:3000
```

Script đăng nhập qua API của frontend, gửi một câu hỏi tạo conversation, gửi
câu hỏi nối tiếp, đọc lại bốn tin nhắn đã lưu, kiểm tra danh sách hội thoại và
xóa conversation test khi kết thúc. `--keep` giữ hội thoại để xem thủ công.
Output gồm status và movie IDs của hai lượt. Nếu lượt đầu có phim, lượt hai hỏi
năm phát hành của phim đó; xem IDs và câu trả lời để đánh giá continuity. Smoke
chỉ xác nhận kết nối, persistence và định dạng cơ bản; chất lượng RAG cần chấm
riêng trên evaluation set.

Khi AI service lỗi hoặc trả payload không dùng được, Spring trả HTTP 503. Giao
diện giữ lại nội dung đang soạn để gửi lại; transaction Spring hoàn tác tin
nhắn của lượt lỗi, tránh tạo lịch sử giả. Nếu nhận 503, kiểm tra log AI service,
Qdrant, catalog và Ollama trước khi chạy lại.
