# Backend còn thiếu cho User Preference Vector v1

- [ ] Gửi toàn bộ ratings hiện tại sang AI qua `PUT /internal/preferences/snapshot` sau khi thêm/sửa/xóa rating đã commit; hook hiện chỉ ghi log. Xóa rating cuối cùng gửi `ratings: []`.
- [ ] Bổ sung timeout, retry bằng snapshot mới nhất, bảo vệ API nội bộ và đảm bảo thứ tự cập nhật theo user.
- [ ] Nối API recommendation với profile/cold-start và thêm integration tests cho luồng backend → AI.

Contract và ví dụ: [User Preference Vector v1](user_preference_v1_vi.md).
