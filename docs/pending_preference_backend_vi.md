# Trạng thái tích hợp User Preference — cập nhật 14/10/2026

Đối chiếu `main` 2992390 và branch `feature/week6-backlog-fixes`.

- [x] Backend có gửi complete snapshot qua HTTP; mô tả cũ “hook chỉ log” đã lỗi thời.
- [x] Fix branch tuần 6: enqueue sau commit, đọc trong REQUIRES_NEW/read-only,
  gửi snapshot rỗng sau xóa rating cuối cùng; rollback không enqueue.
- [x] Coalesce và gửi tuần tự trong một backend process; retry đọc snapshot mới
  nhất. Kiểm tra response thực thay vì log thành công khi client trả null.
- [x] AI process serialize overlapping rebuild để update cũ đang chạy không
  ghi chồng lên delete mới trong trường hợp đã kiểm thử bằng mocks.
- [x] Public recommendation gateway đã có, giữ ranking, exclusions và reasons.
- [x] Live read-only: 7 APP ratings của user 1 khớp profile Qdrant; 10 hits final
  loại phim đã rate, IDs tồn tại trong MySQL, scores/reasons nhất quán.
- [x] GET có xác thực qua Backend và frontend trả 200/ready/10 hits;
  IDs, thứ tự, điểm và reasons khớp direct AI bằng session user hiện có.
- [ ] Deploy/restart backend với fixes và kiểm thử rating commit qua phiên thật;
  không tự tạo/sửa ratings trong DB thật để demo.
- [ ] Durable outbox/reconcile, revision/CAS và thứ tự giữa nhiều instances.
  Queue RAM mất khi restart; timeout phía Qdrant vẫn có kết quả ghi không rõ.
- [ ] Recommendation ngay sau rating có thể đọc profile cũ trước worker; cần
  chốt hành vi refresh UI/read-after-write với owner Backend/Frontend.
- [ ] Phân loại retry cho lỗi permanent 4xx; client hiện trả null cho mọi lỗi.
- [ ] Internal service authentication chưa có; cần thống nhất contract với nhóm.
- [ ] Live fault injection chưa chạy; chỉ mocks timeout/503.

[Báo cáo và tests thực tế tuần 6](week06_backlog_fixes_vi.md).
[Contract preference](user_preference_v1_vi.md).
