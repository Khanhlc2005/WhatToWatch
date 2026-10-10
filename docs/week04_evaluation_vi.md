# Kiểm thử cuối Tuần 4 — query set v1

Ngày local: 2026-10-11; branch `feature/week4-evaluation`; không add/commit/push.
Phạm vi: kiểm thử AI retrieval và regression code hiện tại, chưa chứng nhận toàn hệ thống end-to-end.

## Artifacts và cách chạy lại

- [Query set v1](../data/evaluation/query_set_v1.json): 18 queries (6 semantic, 6 keyword, 6 filtered), có tiếng Việt/Anh, limit=10 chung cho ba mode.
- [Runner](../data/scripts/evaluate_retrieval.py): HTTP tới endpoint hiện có, đối chiếu catalog/CSV, kiểm tra IDs, identity IMDb/TMDB, duplicate, score order, filters và limit.
- [Kết quả thô từng request](evidence/week-04/search-v1/results.jsonl).
- [So sánh ranking](evidence/week-04/search-v1/ranking_comparison.md).
- [Bảng manual evaluation](evidence/week-04/search-v1/manual_evaluation.csv): 280 cặp query–movie duy nhất trong pool ba mode.
- [Summary và hashes dữ liệu](evidence/week-04/search-v1/summary.json), [runtime/code hashes](evidence/week-04/run_context.json).
- [Audit catalog](evidence/week-04/catalog_audit.json), [test output](evidence/week-04/test_results.txt).
- [Tests runner](../data/tests/test_evaluate_retrieval.py).

Chạy FastAPI GPU theo [hướng dẫn local](mapped_catalog_run_vi.md), rồi từ repo root:

```bash
ai-service/.venv-gpu/bin/python data/scripts/evaluate_retrieval.py \
  --output docs/evidence/week-04/search-v1-rerun
PYTHONPATH=ai-service ai-service/.venv-gpu/bin/python -m pytest -q ai-service/tests data/tests
```

Runner yêu cầu thư mục output mới để tránh ghi đè review; ghi mỗi request ngay khi hoàn thành và trả exit code khác 0 nếu có lỗi kiểm tra.
Không ghi Qdrant, không gọi API tạo rating/profile, không sửa runtime retrieval.
Thứ tự chạy dense → sparse → hybrid cố định, một lượt tuần tự; thời gian có cold model startup, không dùng làm benchmark latency.

## Dataset và ID verification

Nguồn: `data/processed/movies_with_mysql_ids.jsonl` và `movies_id_mapping.csv` do đồng đội cung cấp, đã được người dùng xác nhận nguồn ID từ MySQL.
Audit lại **46.923 CSV rows ↔ 46.923 catalog records ↔ 46.923 live Qdrant points: PASS, 0 issues**.
Đây là xác nhận với bản export, chưa xác nhận live MySQL; `not_run=[]` trong audit chỉ nói các nguồn đầu vào được cung cấp đủ.
Catalog chứa overview, genres, keywords, cast/directors, language/country, year, rating/runtime và canonical embedding text.
Tên phim không duy nhất: Titanic có các bản 1943/1953/1997, Parasite có bản 1982/2019; query anchors được đối chiếu bằng movie_id + IMDb + TMDB.
`catalog_anchors` chỉ ghi nguồn gợi ý tạo query, **không phải relevance ground truth**; toàn bộ `expected_movie_ids=[]` và `relevance_status=unjudged`.
Các bộ lọc dùng vocabulary từ catalog; Q18 cố tình vừa include vừa exclude Science Fiction, kiểm tra kết quả rỗng theo logic filter, không phải nhãn relevance.

## Kết quả thực thi

- **54/54 requests thành công, 0 failed checks**; 3 modes dùng cùng queries, filters và limit.
- Q18: cả ba mode trả rỗng đúng điều kiện mâu thuẫn.
- Q15 Sparse trả 5 phim; Q17 Sparse trả 1 phim; các query còn lại ngoài Q18 trả 10 phim/mode. Không nới filters để lấp đầy.
- Q11 “Titanic”: Dense đứng đầu ID 13876, Sparse/Hybrid đứng đầu ID 2977; cả hai đều là IDs catalog đã xác minh, relevance chờ review.
- Q02 tiếng Việt có top kết quả khác đáng kể giữa các mode; cần review trực tiếp overview, chưa quy lỗi model hoặc sửa retrieval ngoài scope.
- **186 tests passed, 1 warning** (Starlette dùng alias BlockingPortal deprecated); `git diff --check` sạch.
- Tests preference/recommendation dùng Qdrant in-memory, gồm snapshot → update → delete và ranking/filters/edge cases.
- Recommendation với user/ratings thật: **SKIPPED theo yêu cầu người dùng**, không tạo interactions giả, không gọi endpoint ghi profile.

## Cách review relevance

Mở CSV bằng UTF-8, đọc query + filters + title/overview, điền `relevance`, `reviewer`, `notes`.
Quy ước đề xuất để bạn xác nhận: 0 = không phù hợp, 1 = một phần, 2 = phù hợp; giữ trống nếu chưa đánh giá (trống không đồng nghĩa 0).
Mỗi query–movie có một nhãn dùng chung cho ba mode, kèm rank/score riêng; các cột rank trống nghĩa là phim không xuất hiện trong top 10 của mode đó.
Đây là pool top 10, không phải toàn bộ phim liên quan trong catalog; không suy ra recall đầy đủ hoặc xem phim ngoài pool là irrelevant.
Chưa tính Precision/nDCG/MRR hay tuyên bố mode tốt nhất; score dense, sparse và RRF khác thang đo nên không so trực tiếp.
RRF dùng tổng `1/(60 + rank)` trên hai nhánh, chỉ tính lần xuất hiện tốt nhất của mỗi movie trong mỗi nhánh; cả hai nhánh ở lần chạy này lấy top 10.

## Trạng thái đến hết Tuần 4

| Hạng mục | Trạng thái/evidence | Còn thiếu |
|---|---|---|
| Catalog chuẩn hóa, mapping, dense+sparse vectors | 46.923 phim, audit live Qdrant PASS | Đối chiếu live MySQL khi có môi trường |
| Dense/Sparse, payload filters | Code + tests + requests live PASS | Manual relevance review |
| Hybrid RRF v1 | Code + tests + 18 requests live PASS | Manual relevance review, chưa benchmark chính thức |
| Preference ratings-v1 | Pipeline AI + tests snapshot/update/delete PASS | Backend hook gửi snapshot thật sau commit |
| Content recommendation MVP | Endpoint + tests in-memory PASS | User test thật, backend gateway/hydrate/fallback |
| Query set/evaluation | Query set, runner, bảng review và kết quả đã xuất | Người dùng xác nhận relevance |
| Search → backend → card/detail | Handoff đã ghi trong pending_search_integration | Chốt phân trang/error contract, gateway, hydrate, end-to-end |
| Backend APIs/account/chat và frontend khác | Không đánh giá lại toàn bộ trong phiên này | Không suy từ tests AI thành hoàn tất cả roadmap |
| Reranker/final ranking Tuần 5 | Ngoài phạm vi | Chưa triển khai trong task này |

## Việc còn dở và backend cần làm trước — 4 câu

Phiên này còn chờ bạn xác nhận relevance của query set và kiểm thử recommendation bằng user có ratings thật, phần kiểm thử user thật đã được bỏ qua theo yêu cầu.
Backend cần ưu tiên gửi snapshot ratings đầy đủ sau transaction commit sang AI, kèm xác thực nội bộ, timeout/retry và bảo đảm thứ tự cập nhật theo user.
Tiếp theo cần nối gateway search/recommendation, lấy danh tính user từ authentication, truyền exclusions, hydrate movie_id qua MySQL giữ thứ tự ranking và chốt phân trang cùng fallback cold-start/lỗi dịch vụ.
Sau khi có môi trường backend/MySQL và user test thật, cần chạy end-to-end rating → preference → recommendation và search → card → detail trước khi xác nhận hoàn tất Tuần 4 toàn hệ thống.
