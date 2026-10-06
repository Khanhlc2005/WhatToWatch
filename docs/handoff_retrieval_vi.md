# Tổng kết bàn giao — retrieval/data contract

## Phạm vi chốt lần này

Theo yêu cầu mới của người dùng, **loại khỏi đợt này các nhiệm vụ phụ thuộc CSV ID từ MySQL**. Việc thiếu CSV không còn chặn bàn giao phần còn lại. Không coi các mục hoãn bên dưới là đã hoàn thành.

Branch: `feature/khanh-retrieval-data-contract`, base main `da0672d`. Frontend lấy riêng thư mục `nextflix/` (đã chuyển vào `frontend/`) từ branch `anhvn-setup-UI` tại `b66a05a`; không đưa backend UUID cũ của branch đó vào main. Không chạy git add/commit/push; người dùng tự review và đẩy Git.

## Đã hoàn thành trong phạm vi này

- Tài liệu field mapping theo source/processed, JPA, payload Qdrant, DTO/API và UI thực tế; dẫn chiếu 3 phim sample có sẵn. Phân biệt CONFIRMED/INFERRED/MISSING, ghi rõ các đoạn mapping chưa có dữ liệu thật.
- Frontend `MovieCard`/`MovieRow` dùng cùng `Movie`; adapter theo DTO ID số của main; loading/error/empty states; hiển thị rating /10, không diễn giải thành phần trăm matching. Route detail/trailer nhận ID số, từ chối UUID và số không an toàn của JavaScript.
- Endpoint nội bộ `/internal/qdrant/search` hỗ trợ dense hoặc sparse BGE-M3 theo config/schema có sẵn. Bộ lọc reusable chỉ dùng field payload thực tế; kiểm tra input, không tự nới filter, xử lý lỗi/empty và deduplicate kết quả. ID chưa mapped được báo rõ, không thay bằng point UUID.
- `ai-service/Dockerfile` chạy FastAPI trên 8010, CPU, user không phải root, cache model có quyền ghi; profile Compose `ai` kết nối Qdrant. Không thêm secret vào image.
- Tests cho retrieval/filter/ID status, frontend contract và route ID; CI frontend dùng đúng `frontend/`. CI AI chạy tests thật và không còn che giấu test thất bại bằng `|| echo`.
- Công cụ **chỉ đọc** `data/scripts/validate_movie_links.py` và tests đã chuẩn bị cho đợt CSV sau; báo cáo sample hiện tại là INCOMPLETE, không phải chứng nhận liên kết MySQL.

## Các nhiệm vụ đã loại trừ lần này — tiếp tục khi có CSV

1. Nhận và kiểm tra CSV thực tế: header, kiểu ID, số bản ghi, nguồn export và bảng MySQL thật. Đối chiếu chênh lệch hiện tại giữa JPA `movies`/Long, init SQL `movie` và script import UUID. **Giữ nguyên script import lần này theo yêu cầu người dùng.**
2. Đối chiếu `imdb_id` và `tmdb_id` với ID nội bộ MySQL; phát hiện missing/duplicate/mismatch sau import trên phạm vi dữ liệu thực tế; xử lý các trường hợp mâu thuẫn trước khi ghi mapping.
3. Điền `movie_id` thật vào processed data và Qdrant payload; xác minh quan hệ point UUID ↔ payload movie_id ↔ MySQL ID. Không suy ra MySQL ID từ TMDB, IMDb hoặc MovieLens `links.csv`.
4. Chạy validator trên CSV/processed/Qdrant thật, kiểm tra missing point, orphan, duplicate và mismatch; lưu báo cáo đạt yêu cầu. Test fixture hiện có không thay thế bước này.
5. Hoàn thiện đường search result → backend hydrate metadata từ MySQL, giữ thứ tự ranking và xử lý ID không tồn tại. Chưa nối AI search vào trang search của starter.
6. Kiểm thử end-to-end search → MovieCard/MovieRow → movie detail bằng ID MySQL thật; ghi evidence sau khi các dịch vụ và mapping đã sẵn sàng.

Điểm tiếp tục: gửi đường dẫn CSV. Tool đang nhận header `id,imdb_id,tmdb_id`; cần kiểm tra file nhận được trước khi dùng, không giả định header hoặc schema của file chưa có.

## Kiểm tra và giới hạn

Xem [bằng chứng kiểm tra](evidence/retrieval-checks.md): 42 test Python host, 35 test AI trong image, frontend typecheck/contract/lint/build, Docker build và HTTP health thực tế đã PASS. Kiểm tra cuối đợt được bổ sung trong cùng file evidence.

**NOT RUN / chưa xác minh:** inference với trọng số BGE-M3 thật (cache chưa có model weights; môi trường host còn xung đột dependency), live retrieval trên Qdrant đang tắt. Import BGE-M3 và kiểm thử logic retrieval bằng embeddings fixture/Qdrant in-memory đã PASS. Đây là giới hạn xác minh, không phải kết quả model thật. Các kiểm thử MySQL/CSV thuộc danh sách hoãn ở trên.

## File để review và lệnh chạy

- Frontend mới: `frontend/**` (đặc biệt `types/index.ts`, `lib/movies.ts`, `components/List/`, hai route `pages/api/movies/[id]/`, `scripts/test-movies.cjs`).
- AI: router/schema/retrieval, `services/filters.py`, tests, Dockerfile.
- Data: `validate_movie_links.py`, `test_movie_links.py`; chưa ghi mapping thật.
- Hạ tầng/tài liệu: Compose, `.dockerignore`, CI frontend/AI, README, `docs/ai_service_local_run.md`, `docs/retrieval_data_contract_vi.md`, evidence và bản tổng kết này.
- Repo còn các thay đổi catalog/requirements/Qdrant scripts có sẵn trước task; giữ nguyên, cần review riêng khi chọn file để commit.

```bash
# repo root
PYTHONPATH=ai-service python3 -m pytest -q ai-service/tests data/tests/test_movie_links.py
docker compose --profile ai config --quiet
docker compose --profile ai up -d --build qdrant ai-service
curl http://localhost:8010/internal/health

# frontend, cần Node 20
cd frontend
npm ci
npx tsc --noEmit
npm run test:contract
npm run lint
npm run build
npm run dev
```

Demo dense/sparse và format CSV/snapshot: [hướng dẫn chi tiết](retrieval_data_contract_vi.md). Search thật cần collection đã index và model weights; không tự import vào MySQL để chạy demo.
