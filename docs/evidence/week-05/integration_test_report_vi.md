# Báo cáo tích hợp AI Service — tuần 5 (2026-10-12)

> Cập nhật 14/10/2026: tài liệu này ghi kết quả lịch sử tuần 5. Hiện MySQL có
> 1 user/7 ratings, Qdrant có profile user 1 và smoke recommendation read-only
> trả ready/10 hits. RecommendationService trên main không gửi snapshot mỗi GET;
> RatingService main gửi async trước commit, đã sửa trên branch tuần 6.
> Các số PASS và trạng thái dịch vụ bên dưới không phải kết quả chạy lại tuần 6.


Branch `audit-week05-integration-review` bắt đầu từ `main` commit `931be55`. Các phép thử live chỉ đọc MySQL/Qdrant; không tạo ratings, interactions hoặc profile. Unit/mock tests được tách khỏi live smoke. Không `git add`, commit, push hoặc PR.

## Nguyên nhân và thay đổi

Qdrant ở host port **6333** là `tinyrag_qdrant` của dự án khác. WhatToWatch dùng port **6335**; kết luận collection hỏng trong bản audit ban đầu là do kiểm tra nhầm service. Collection đúng có 46.923 points. `.env` trước đó thiếu Qdrant/reranker/timeout keys và FastAPI chưa chạy vì profile `ai` chưa được khởi động. Đã bổ sung `.env` (Git ignored), `.env.example`, Compose, khởi động Qdrant/FastAPI/Ollama proxy và tải `BAAI/bge-reranker-v2-m3` vào cache dự án.

Backend search nay gửi `mode=hybrid`, `rerank=true`, `candidate_k=50`, giữ thứ tự ranking AI khi hydrate MySQL và chỉ fallback lexical khi AI unavailable. Chat dùng Hybrid → Rerank trước khi dựng context. Endpoint có xác thực `GET /movies/recommendations` lấy ratings thật của user, gửi complete snapshot khi có ít nhất 3 ratings, gọi `ranking=final`, loại phim đã rate, hydrate đúng thứ tự và trả `score_components`/`reasons`. Không có ratings thì trả `cold_start` và không ghi profile.

## PASS / FAIL / NOT RUN

| Hạng mục | Trạng thái | Bằng chứng và giới hạn |
|---|---|---|
| Qdrant catalog và movie IDs | **PASS (live, read-only)** | `sync_movie_ids.py` dry-run trên `127.0.0.1:6335`: `records=46923`, `to_update=0`, `updated=0`, `failed=0`; MySQL `COUNT(movies)=46923`. |
| Dense, Sparse, Hybrid | **PASS (live smoke)** | Query `space exploration` với `genres=[Science Fiction]`: 3 modes HTTP 200, 5 hits/mode, tất cả hit có genre yêu cầu. |
| Hybrid + BGE Reranker | **PASS (live smoke)** | Cùng query/filter: HTTP 200, 5 hits, 5/5 có `rerank_score`; run 3 candidates có cả `retrieval_score` và `rerank_score`. |
| Backend → FastAPI → Qdrant, ranking order | **PASS (live smoke)** | `GET /movies/search?query=space%20exploration&page=0&size=10`: HTTP 200, `code=1000`; 10 IDs đầu trùng đúng thứ tự direct AI Hybrid + Reranker với `candidate_k=50`, `limit=50`. Chỉ chứng minh query này. |
| RAG Query → Retrieval → Rerank → Context → Answer | **PASS (live smoke)** | `POST /internal/chat` với Science Fiction: HTTP 200, `status=answered`, movie ID `5253`; FastAPI container truy cập Backend catalog và Ollama proxy đều HTTP 200. |
| Empty / invalid inputs | **PASS (live smoke + mock)** | Hybrid + rerank `year_min=2099` trả `hits=[]`; invalid recommendation movie ID và year range trả 422; mock tests kiểm tra ID sai/thiếu không bị thay bằng point ID. |
| Recommendation Final Ranking, reason codes | **PASS (unit/mock); NOT RUN (live user)** | Python/Java tests kiểm tra snapshot, final score, reasons, exclusions, schema và thứ tự. Live request user không có profile trả `cold_start`, `hits=[]`. MySQL có 0 ratings và Qdrant có 0 profiles. |
| Service unavailable / timeout | **PASS (unit/mock); NOT RUN (live fault injection)** | Mock tests kiểm tra 503 cho retrieval/model/catalog outage và catalog timeout; Java mock test kiểm tra lexical fallback. Chưa cố ý ngắt live services. |
| Recommendation authorization | **PASS (live)** | GET `/movies/recommendations` không token trả 401. Authorized response NOT RUN vì chưa có ratings thật. |
| Python tests | **PASS (unit/mock)** | `PYTHONPATH=ai-service ai-service/.venv-gpu/bin/python -m pytest -q ai-service/tests data/tests/test_evaluate_retrieval.py` → **184 passed**, 1 Starlette deprecation warning. |
| Java tests | **PASS (unit/mock)** | Maven BuildKit `mvn -q test` → **9 passed, 1 skipped**; Spring context test đã disabled vì chưa có test database. |

## So sánh retrieval

| Phương pháp | Live smoke mới | Artifact tuần 4 | Precision@K / MRR / NDCG@K |
|---|---|---|---|
| Dense | 1 query có filter PASS | 18 queries, 0 structural issues | Không tính |
| Sparse | 1 query có filter PASS | 18 queries, 0 structural issues | Không tính |
| Hybrid | 1 query có filter PASS | 18 queries, 0 structural issues | Không tính |
| Hybrid + Reranker | 1 query có filter PASS | Chưa có batch artifact | Không tính |

[Query set](../../../data/evaluation/query_set_v1.json) có 18/18 queries `unjudged`, `expected_movie_ids=[]`; 280 dòng [manual evaluation CSV](../week-04/search-v1/manual_evaluation.csv) trống `relevance`/`reviewer`. `catalog_anchors` chỉ là identity references. [Artifact tuần 4](../week-04/search-v1/summary.json) gồm 54 requests trước phiên này; latency một lượt có cold startup, không phải benchmark. **0 query có labels hợp lệ**, nên không báo quality metrics hay reranker gain.

## Bugs đã sửa và phần còn lại

**Đã sửa:** trỏ nhầm Qdrant local và thiếu cấu hình `.env`; thiếu model reranker trong offline cache; Backend chỉ gọi Dense và áp thêm RRF làm đổi AI order; thiếu Backend recommendation contract; Chat bỏ qua rerank; RatingService log webhook dù không thực sự gửi. Thêm tests cho rerank 3 modes, RAG rerank/timeout, Backend order/empty/fallback và recommendation snapshot/exclusion/schema.

**Còn lại:**

1. Chưa có ratings từ người dùng ứng dụng (`COUNT(ratings)=0`) hoặc user profile, nên **live Final Ranking/Explainability qua tài khoản người dùng NOT RUN**. `data/raw/title.ratings.tsv.gz` là IMDb `tconst/averageRating/numVotes` tổng hợp theo phim; cả 46.923 phim MySQL đã có `imdb_rating` và `imdb_vote_count`. File này không có `user_id` và không thể dùng làm preference ratings 1–5. Không tạo ratings giả.
2. Chưa có relevance labels được duyệt, nên không thể tính Precision@K, MRR, NDCG@K. Runner tuần 4 chỉ hỗ trợ 3 modes và query set unjudged; cần mở rộng sau khi có labels.
3. Chưa fault-inject live timeout/service unavailable. Spring context test vẫn disabled.
4. Backend search phân trang trong top 50 AI candidates; `totalElements` là số candidates đã hydrate, không phải tổng số phim phù hợp. Recommendation hiện loại phim đã rate; `watch_history.event_type` chưa có quy tắc đủ rõ để loại phim đã xem.

## Sẵn sàng tuần 6

**Search và Chat AI Service sẵn sàng ở mức live smoke** trên Qdrant/MySQL/Backend/FastAPI/Ollama đúng môi trường. **Recommendation Final Ranking sẵn sàng ở mức unit/mock và cold-start live**; cần ratings thật có quyền sử dụng để xác nhận user flow. Benchmark chất lượng còn chờ relevance labels. Không tuyên bố full end-to-end PASS cho recommendation hoặc timeout.

## Bổ sung giao diện web (12/10/2026)

- Trang `/browse` có hàng **Dành cho bạn** gọi Next API `/api/movies/recommendations`, chuyển tiếp cookie phiên tới Backend `GET /movies/recommendations` và giữ đúng thứ tự kết quả. Giao diện hiện lý do theo reason codes `profile_similarity`/`imdb_rating`; `cold_start` hướng dẫn chấm ít nhất 3 phim, còn 401 hiển thị liên kết đăng nhập.
- Chi tiết phim có nút chấm 1–5 sao qua Next API `/api/ratings/[movieId]` tới Backend ratings. Chỉ ghi rating khi người dùng thực sự bấm; sau khi lưu, hàng đề xuất tự tải lại. Trường hợp Backend bỏ `result` khi chưa có rating được xử lý thành `null` ở proxy.
- **PASS (build/contract):** Docker frontend production build biên dịch và kiểm tra TypeScript thành công; `npm run test:contract` trong container PASS. **PASS (live smoke):** `/browse` trả 200 và HTML có “Dành cho bạn”; `/api/movies/recommendations` và `/api/ratings/1` không có cookie trả 401; home feed top-rated trả 200. Compose frontend, backend, mysql, ai-service và qdrant đang chạy.
- **NOT RUN (live user):** chưa xác nhận luồng chấm 3 phim → preference vector → final ranking → hàng đề xuất bằng tài khoản thật vì database hiện chưa có user ratings và không dùng đánh giá giả.

## Sửa phản hồi giao diện (12/10/2026)

- Home feed `top-rated` nay dùng IMDb rating với ít nhất 50.000 lượt bình chọn, trả 50 phim; `newest` cũng trả 50 phim. Mapper phim ưu tiên IMDb để điểm ở card, banner, modal và các hàng nhất quán. Live API `top-rated` trả 50 phim, từ 8,5 đến 9,3 điểm; các phim đầu là *The Shawshank Redemption* (9,3), *The Godfather* (9,2), *The Dark Knight* (9,1). Trước sửa, home feed ưu tiên TMDB và xuất hiện nhiều phim 10/10 ít lượt bình chọn.
- Khi chưa đăng nhập hoặc chưa có 3 ratings, hàng “Dành cho bạn” hiển thị 10 phim chọn ngẫu nhiên từ 50 phim IMDb cao nhất và giải thích đây là gợi ý chung. Khi đủ ratings, hàng dùng thứ tự final ranking từ API. Không ghi ratings hoặc interactions giả.
- `MovieRow` có nút `‹`/`›` và ẩn thanh cuộn; vẫn hỗ trợ vuốt. Headless Chrome smoke: 3 hàng trên `/browse` có nút sang phải, bấm sang phải làm `scrollLeft` từ 0 lên 533 px, bấm sang trái đưa về 0. Mở một card hiển thị modal và phần chấm phim, không thấy lỗi JSON trong phiên chưa đăng nhập.
- Các luồng mở chi tiết, trailer, recommendation và rating mới dùng bộ đọc JSON có thông báo khi phản hồi rỗng/hỏng; GET rating chưa chấm được coi là `null`. Frontend build và contract tests PASS, bao gồm regression cho IMDb ưu tiên TMDB 10 và phản hồi JSON rỗng. **NOT RUN:** chưa tái hiện/kiểm chứng thao tác mở card trên tài khoản đăng nhập thật vì không có credentials; do đó chưa tuyên bố lỗi JSON trong phiên đăng nhập đã được xác nhận hết bằng live test.

## Bổ sung ngôn ngữ giao diện (12/10/2026)

- Chuỗi giao diện cố định của trang đăng nhập, đăng ký, Browse, Search, Chatbot, Favourite, Watch later, modal phim, trạng thái lỗi và Next API đã chuyển sang tiếng Anh; HTML khai báo `lang="en"`. Tám đường dẫn `/`, `/login`, `/register`, `/browse`, `/search`, `/chat`, `/library/favorites`, `/library/watchlist` đều trả 200 và phần chữ giao diện SSR không còn ký tự tiếng Việt.
- Prompt và câu trả lời cố định của Chatbot được chuyển sang tiếng Anh. **PASS (unit/mock):** 46 test Chatbot/RAG liên quan. **PASS (live service):** AI Service trả câu tiếng Anh cho cả empty context và câu hỏi release year dùng tool catalog qua Backend/MySQL. Frontend contract tests PASS.
- Nội dung phim lấy từ dữ liệu gốc, tin nhắn người dùng và hội thoại cũ được giữ nguyên; không dịch hoặc ghi đè dữ liệu hiện có. Không tuyên bố mọi dữ liệu động đều là tiếng Anh.
