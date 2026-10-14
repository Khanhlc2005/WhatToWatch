# Tuần 6 — kiểm tra Recommendation và sửa backlog

Ngày kiểm tra: 14/10/2026. Fetch thành công: local main và origin/main cùng
`2992390` (Merge PR #50). Working tree ban đầu sạch. Đã tạo branch
`feature/week6-backlog-fixes`; không add/commit/push/PR.

## DONE / PARTIAL / BLOCKED

| Phạm vi | Trạng thái | Bằng chứng và giới hạn |
|---|---|---|
| Main/working tree/branch | DONE | Fetch origin/main; main=origin/main=2992390; branch mới đúng tên. |
| Hook rating sau commit | DONE (code + regression) | Spring transaction interceptor thật với transaction manager/repositories mock: tạo/sửa/xóa và commit failure; queue chỉ được thêm trong afterCommit. Chưa test MySQL transaction live với fixes. |
| Snapshot/transaction | DONE (code + regression) | Snapshot đầy đủ trong REQUIRES_NEW/read-only; mapping lazy movie IDs trong transaction; HTTP ở ngoài transaction. Xóa cuối cùng gửi ratings=[]. |
| Retry/order trong backend process | DONE (code + mock) | Một worker gửi tuần tự; coalesce user; mỗi retry đọc snapshot mới; null/exception giữ pending; commit trong khi gửi không bị mất. Delay 5 giây sau vòng trước, không cam kết tổng latency 5 giây. |
| Overlapping profile writes | DONE (regression trong một AI process) | Update cũ bị chặn ở upsert, request xóa mới phải đợi rồi xóa. Không lock: 1 FAIL tái hiện; có lock: PASS. Không bảo đảm revision/order giữa nhiều process. |
| Cold-start/exclusions/order/explainability | DONE (tests + live đã giới hạn) | Cold-start/neutral ratings/empty snapshot/storage failures dùng in-memory/mocks; live user thật có 7 ratings và 10 final hits. |
| Recommendation đọc live | DONE (một user, một snapshot) | Vector hiện có khớp 7 APP ratings (max diff 1.35559e-08); direct AI, Backend GET và frontend GET đều ready/10 hits, cùng IDs/order/scores/reasons. |
| Timeout/503/fallback | DONE (mocks) | HTTP client mock SocketTimeoutException/503; worker retry null; Recommendation unavailable/hits=[]; search fallback lexical qua service tests. Không cố ý ngắt service live. |
| App local | DONE | Frontend/Backend/MySQL/AI/Qdrant đang chạy; /login và /browse trả HTTP 200. URL http://localhost:3000/login. |
| Tài liệu tồn đọng | DONE trong phạm vi kiểm tra | Cập nhật preference, pending integration, MVP recommendation và chú thích kết quả tuần 5 là lịch sử. Không xác minh lại SFT/training/RAG toàn bộ. |
| Rating mutation → commit → Qdrant → UI live trên fixes | PARTIAL | Đã kiểm tra Spring transaction/mocks và live đọc với session thật. Chưa thao tác ratings thật và fixes chưa được deploy vào container. Không tuyên bố toàn luồng mutation end-to-end PASS. |
| Read-after-write/refresh UI | PARTIAL | GET chỉ đọc profile; UI fetch ngay khi rating-change có thể thấy profile cũ/cold_start trước worker. Cần thống nhất hành vi refresh hoặc chờ sync với owner Backend/Frontend. |
| Restart/multi-instance/permanent errors | PARTIAL | Pending queue RAM mất khi restart, chưa outbox/reconcile/CAS; client chưa phân loại 4xx permanent và sẽ retry như lỗi transient. Lock AI không bảo vệ nhiều workers/replicas hoặc ghi Qdrant hoàn tất muộn sau storage timeout. |
| Internal service auth | BLOCKED cần thống nhất contract | /internal/preferences và /internal/recommendations hiện không service auth. Không tự đổi contract. |
| Quality metrics evaluation | BLOCKED bởi labels | 18 queries có 0 expected IDs; 280 manual rows có 0 relevance/reviewer; không tính Precision/MRR/nDCG hay khẳng định tăng chất lượng. |
| Live fault injection | BLOCKED bởi authorization | Chỉ thực hiện khi có kịch bản an toàn và người dùng cho phép; phiên này không fault-inject. |

## Lỗi và cách sửa

1. **Async trước transaction commit:** `CompletableFuture.runAsync` có thể đọc
   snapshot chưa có rating vừa save hoặc còn rating vừa delete. Thay bằng
   `PreferenceSyncService.afterCommit`; rollback không enqueue.
2. **Snapshot ghi sai thứ tự/lost notification:** nhiều common-pool tasks chạy
   độc lập và query lazy entities ngoài persistence context. Worker đơn đọc
   transaction mới, map DTO trong transaction, remove pending trước khi đọc để
   commit trong lúc IO giữ được lượt tiếp theo. Retry không giữ snapshot cũ.
3. **Báo thành công dù sync lỗi:** client catch lỗi và trả null; RatingService
   cũ vẫn log “Triggered”. Worker chỉ log synced khi response ready/cold_start;
   lỗi/null giữ pending và log user ID cùng loại lỗi.
4. **Update AI còn chạy sau timeout có thể ghi chồng delete:** 64 locks cố định
   bao toàn bộ rebuild trong AI process. User cùng bucket có thể chờ. Đây là
   mutual exclusion; không thay thế source revision/CAS hoặc durable outbox.
5. **Test gây hiểu nhầm:** test tên gửi snapshot chỉ stub rebuildPreference mà
   không verify call. Đổi tên theo hành vi thật; verify GET không rebuild,
   bổ sung assertion order/exclusions/score components/reasons và unavailable.
6. **Tài liệu cũ:** hook chỉ log, chưa có public gateway, thiếu DB và không có
   ratings đã không còn đúng. Ghi lại code và số liệu thực tế theo ngày kiểm tra.

## Tests thực tế và evidence

- Python sau fix: **185 passed**, 1 Starlette deprecation warning, không failures.
  Lệnh: `PYTHONPATH=ai-service ai-service/.venv-gpu/bin/python -m pytest -q ai-service/tests data/tests/test_evaluate_retrieval.py`.
  [Output](evidence/week-06/python_tests.txt).
- Java: **25 passed, 1 skipped**, 0 failures/errors. Spring context test vẫn
  disabled vì chưa có test database. Repositories/AI là mocks; không nói đây là
  integration test MySQL thật. [Summary](evidence/week-06/java_summary.json) và
  các `com.project.*.txt` cùng thư mục.
- Chạy Java không cần cài JDK host:
  `docker build -f tools/week6-backend-tests.Dockerfile --output type=local,dest=/tmp/whattowatch-week6-java-reports backend`.
  Build container chỉ chạy Maven tests, không deploy app hoặc nối DB thật.
- [FAIL tái hiện khi bỏ lock](evidence/week-06/race_before_fix.txt): trong một
  tiến trình pytest riêng, gán `rebuild_preference = _rebuild_preference` rồi chạy
  regression overlapping update/delete. Không sửa code runtime/DB để tái hiện.
- [Audit labels](evidence/week-06/evaluation_labels.json): 18 queries/280 manual rows, chưa có labels hợp lệ.
- [Live MySQL/Qdrant/AI read-only](evidence/week-06/live_readonly.json): 7 ratings,
  7 embeddings dùng được, không skipped; profile khớp công thức v1; 10 hits
  unique, loại rated IDs, final score giảm dần, IDs có trong MySQL, reason values
  khớp components và weights. Tính vector trong RAM, không gửi PUT snapshot.
- [Live GET có xác thực](evidence/week-06/live_authenticated.json): session file
  do người dùng cung cấp, Backend và frontend HTTP 200, ready/10 hits; frontend
  khớp Backend, Backend khớp direct AI. Không lưu token trong evidence.

Một lượt Java bổ sung fixture bị 2 FAIL do Mockito `when` gọi stub cũ ngay
trong setup; đã đổi sang `doAnswer` và chạy lại toàn bộ đạt kết quả trên.
Không tính lượt này là PASS hoặc lỗi transaction trong implementation.

Lượt Python trong sandbox ban đầu bị treo ở TestClient và bị dừng (exit 130),
không tính PASS; chạy lại ngoài sandbox bằng quyền execution và hoàn tất.
AI/Qdrant/Frontend được khởi động bằng container/image/volumes hiện có với
`--no-build --no-recreate`. Các container app hiện có chưa nạp fixes branch tuần 6;
AI process đã khởi động trước khi thêm lock. Live smoke chứng minh dữ liệu/profile
và luồng đọc hiện tại; regression tests chứng minh fixes trong code branch.

## Files thay đổi

- `.gitignore`: bỏ qua file session local để token không xuất hiện trong Git.
- `backend/src/main/java/com/project/movie_recommendation/service/RatingService.java`.
- `backend/src/main/java/com/project/movie_recommendation/service/PreferenceSyncService.java` (mới).
- `backend/src/main/java/com/project/movie_recommendation/client/AiServiceClient.java`: constructor cho mock RestClient, constructor Spring được đánh dấu Autowired.
- `backend/src/test/java/com/project/movie_recommendation/service/RecommendationServiceTest.java`.
- `backend/src/test/java/com/project/movie_recommendation/service/PreferenceSyncServiceTest.java` (mới).
- `backend/src/test/java/com/project/movie_recommendation/service/RatingPreferenceTransactionTest.java` (mới).
- `backend/src/test/java/com/project/movie_recommendation/client/AiServiceClientTest.java` (mới).
- `ai-service/app/services/preference.py`, `ai-service/tests/test_preference.py`.
- `tools/week6-backend-tests.Dockerfile` (mới).
- `docs/pending_preference_backend_vi.md`, `docs/pending_search_integration_vi.md`.
- `docs/user_preference_v1_vi.md`, `docs/content_recommendation_mvp_vi.md`.
- `docs/week05_ai_ranking_sft_vi.md`, `docs/evidence/week-05/integration_test_report_vi.md` (chú thích lịch sử).
- `docs/week06_backlog_fixes_vi.md` và `docs/evidence/week-06/*` (mới).

## Phần cần nhóm xử lý

- **Khánh Vũ + Khánh Bùi:** review/deploy fixes sau khi test, kiểm thử thêm/sửa/xóa
  qua tài khoản thật theo thao tác người dùng; xử lý durable notification và
  nhiều instance. Muốn version/CAS/outbox cần thống nhất contract/schema trước.
- **Backend/Frontend owners:** chốt đọc ngay sau rating, tránh UI giữ profile cũ
  cho tới lần reload; chốt watched exclusions theo loại watch_history event.
- **Backend/AI owners:** thống nhất internal auth và phân loại retry permanent.
- **Nhóm evaluation:** cung cấp relevance labels được review; không lấy IMDb
  rating tổng hợp làm user preference hoặc ground truth cá nhân.
- **Người dùng:** cho phép kịch bản fault injection live riêng nếu cần. Không
  cần thêm dữ liệu để kiểm tra luồng đọc hiện tại.

Không tạo ratings/interactions, không gửi snapshot ghi profile thật, không
xóa/rebuild Qdrant/MySQL/volumes, không đổi API contract, không thêm dependencies.
File `wtw-session.token` là file người dùng tạo, không phải artifact bàn giao;
đã ignore và không chép token vào báo cáo/log.
