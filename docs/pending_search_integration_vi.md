# Trạng thái search → card → detail — đối chiếu 14/10/2026

Ghi chú tạm hoãn ngày 11/10 đã lỗi thời về code và hạ tầng. Đây là trạng thái
đã đối chiếu từ main 2992390; không suy lại PASS từ tài liệu cũ.

| Hạng mục | Trạng thái hiện tại | Bằng chứng/giới hạn |
|---|---|---|
| MySQL/Backend | DONE (đọc live) | Đang chạy; movies=46.923, users=1, ratings=7. Không import/seed/rebuild. |
| Qdrant/AI Service | DONE (health live) | Khởi động container hiện có bằng --no-build --no-recreate; movies/user_profiles tồn tại, AI health=ok. |
| Backend search gateway | DONE (code + mock tests) | MovieService gọi hybrid/rerank/candidate pool, hydrate theo AI order, fallback lexical khi client trả null. |
| UI card IDs/order | DONE (đối chiếu code) | Adapter dùng MySQL ID; MovieRow map theo thứ tự input. Không browser-test thao tác card trong phiên này. |
| Catalog mapping đầy đủ | PARTIAL | 46.923 là số lượng MySQL; live tuần 6 chỉ xác nhận 10 recommendation IDs tồn tại, chưa audit toàn bộ mapping. |
| Search/card/detail live | PARTIAL | Báo cáo tuần 5 có smoke lịch sử; chưa chạy lại toàn luồng này trong tuần 6. |
| Phân trang search | PARTIAL | Backend phân trang trong pool AI candidates, không phải total toàn catalog. Không đổi API contract. |

Cấu hình Compose hiện mount `data/mysql/movies_data.sql`, không còn init.sql
legacy như ghi chú cũ. Không chạy lại init/import và không xóa volumes.
Contract/code đã có; không cần tiếp tục dựa vào đề xuất chưa duyệt
`mode=dense|sparse` trong tài liệu cũ.

Lịch sử kiểm tra search: [báo cáo tuần 5](evidence/week-05/integration_test_report_vi.md).
Phạm vi recommendation/tests và blocker hiện tại: [báo cáo tuần 6](week06_backlog_fixes_vi.md).
