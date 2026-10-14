# Tuần 6 — kiểm tra AI pipeline và chuẩn bị evaluation

Ngày 14/10/2026, Khánh Bùi. Working tree ban đầu sạch, branch gốc
`feature/week6-backlog-fixes`, HEAD `1f7b1f2`; tạo `feature/week6-ai-evaluation`
từ trạng thái đó để giữ fixes tuần 6 đã có. Không fetch/reset main, không
add/commit/push/PR. Chưa triển khai code vào dịch vụ live.

## Kết quả và bằng chứng

| Phạm vi | Trạng thái | Kết quả và giới hạn |
|---|---|---|
| Dense/Sparse/Hybrid/Reranker regression | DONE, offline | Qdrant in-memory và model mocks; filters, K, dedup, IDs, ranking, errors và backward response checks. Không coi đây là benchmark model thật. |
| Lỗi Hybrid NaN | FIXED | [FAIL trước sửa](evidence/week-06-ai-evaluation/nonfinite_before_fix.txt): movie có NaN vẫn xuất hiện sau RRF. Lọc score không hữu hạn trước sort/fusion, regression PASS. |
| SFT v1 review | DONE, retired | 1.996 targets khớp source/schema/generator, không duplicate/leakage. Phát hiện lệch tiếng Việt với runtime English. [Audit trước quyết định ngôn ngữ](evidence/week-06-ai-evaluation/sft_quality.json). Người dùng yêu cầu xóa bốn artifact v1. |
| SFT v2-en | DONE, technical checks | 1.996 mẫu / 1.000 phim; train/validation/test = 1.613/185/198 mẫu; prompt runtime English; giữ identity/split, không tuning test. [Quality report](evidence/week-06-ai-evaluation/sft_v2_en_quality.json). Chưa human-review semantic quality. |
| Catalog identity | DONE, offline export | 46.923 processed records khớp 46.923 MySQL CSV records, 0 issues. [Audit](evidence/week-06-ai-evaluation/catalog_identity.json) ghi INCOMPLETE vì chưa đối chiếu Qdrant live; CSV không chứng minh DB hiện tại. |
| Retrieval set + runner | DONE, capability | Giữ 18 queries unjudged; hỗ trợ dense/sparse/hybrid/hybrid_reranker; export pool bốn modes; CLI được kiểm tra bằng HTTP mocks; malformed responses vẫn export evidence và báo lỗi. |
| Quality metrics | BLOCKED bởi labels | 0 relevance/reviewer trong 280 manual rows; không báo gain hay tính quality metrics thực. [Audit labels](evidence/week-06-ai-evaluation/evaluation_labels.json). |
| Base/Fine-tuned comparator | DONE, capability | 22 frozen cases trên context catalog xác minh, anchors không overlap SFT train; model/input/prompt/settings checks; capture raw và guarded riêng, giữ errors. Chưa chạy so sánh model thật. |
| Live retrieval/reranker | NOT RUN | AI localhost:8010 connection refused; không có AI container chạy lúc kiểm tra. RAM khả dụng ~3,6 GiB, swap dùng ~2,0 GiB; cache ~4,9 GiB không chứng minh reranker có weights phù hợp. Không khởi động/load/download model. |
| Fine-tuned model/training | Nam Anh phụ trách | Ollama có qwen2.5:3b và gemma4:e2b-it-qat; chưa có fine-tuned checkpoint cung cấp. Không LoRA training hoặc runtime migration. |

[Resource preflight](evidence/week-06-ai-evaluation/resource_preflight.json) chỉ
là snapshot lúc kiểm tra. Các kết quả live trong báo cáo backlog trước đây là
lịch sử; không tái sử dụng thành PASS live của phiên này.

## Pipeline đã rà soát

- `embedding.py`: BGE-M3 encode query với dense 1024 và sparse lexical weights;
  model load lười, không đổi embedding/index.
- `filters.py` + `MovieFilters`: OR trong danh sách cùng field, AND giữa fields;
  exclude genres, language/country, year/rating/runtime; reject unsupported
  fields, year đảo chiều, values rỗng/sai phạm vi. Không relax filter để đủ K.
- Retrieval: không rerank lấy final-K mỗi nhánh; rerank dùng candidate-K explicit
  hoặc `max(final-K, default 50)`; candidate range 1..500, final 1..100, explicit
  candidate<final bị 422. Candidate-K ignored khi rerank=false.
- Dense/sparse score sort giảm dần, tie point ID; Hybrid RRF k=60 một lần, mỗi
  identity chỉ góp một lần mỗi branch. Dedup ưu tiên MySQL ID hợp lệ rồi IMDb
  rồi point ID. Không thay ID thiếu/sai bằng point ID; API ghi present_unverified
  khi ID hiện diện, không khẳng định đã xác minh MySQL.
- Reranker chấm title/genres/keywords thật, không thêm overview giả; dedup trước
  scoring; score ties giữ retrieval order; candidates thiếu text đứng cuối,
  score giữ retrieval score. Nonfinite/wrong number of model scores bị reject.
- Search error model/Qdrant/vector → 503 generic; sparse rỗng → empty, hybrid
  sparse rỗng vẫn dùng dense. Rerank opt-in; response baseline không thêm fields
  score mới. Filters/API/weights và thuật toán cho dữ liệu hợp lệ giữ nguyên.
- Context hydration kiểm tra ID/IMDb/TMDB với backend, bỏ missing/mismatch và
  preserve retrieval order; tối đa 5 context movies. Suite chat retrieval hiện
  có kiểm thử đường này bằng mocks, không chứng minh hydration live lần này.

## Explainability

`profile_similarity`: chỉ xuất hiện khi cosine>0 và weight>0; reason value bằng
component đã chuẩn hóa `(cosine+1)/2` sau clamp. Không giải mã thể loại/diễn viên
ưa thích từ vector. `imdb_rating`: chỉ xuất hiện khi rating số hữu hạn thuộc
[0,10] và weight>0; value=rating/10. Bool/string/NaN/out-of-range không là rating.
Thiếu rating thì renormalize weights, không gán feedback giả.

Regression kiểm tra reasons/components/contributions, rating sai/thiếu, cosine
âm/0/dương và zero weight. `ranking=cosine` giữ contract cũ; final ranking mới
mới có components/reasons. Cold-start không tạo explanation cá nhân giả.

**Vấn đề còn tồn tại ở UI:** `frontend/lib/recommendations.ts` hiển thị “Highly
rated on IMDb” chỉ dựa vào code `imdb_rating`. Code này có cả rating 0 và 2,
không phải ngưỡng “highly rated”; regression xác nhận nghĩa code hiện tại.
Owner Frontend nên dùng wording trung tính hoặc value với ngưỡng được thống
nhất. Không đổi frontend/threshold trong phạm vi review reason codes.

Chatbot RAG reason khác Recommendation reason codes: RAG reason là text,
Recommendation reasons là `{code,value}`. `_grounded_response` hiện tạo lại
reason theo facts context, nên fine-tuning có thể không thay đổi explanation
cuối cùng dù raw output thay đổi. Comparator lưu cả hai để tránh kết luận sai.
Substring support check chỉ là diagnostic, không phải đánh giá usefulness hay
semantic correctness. SFT v2 chưa dạy explainability recommendation cá nhân.

## Bàn giao và phần cần làm tiếp

[Bàn giao Nam Anh](handoff_sft_week06_vi.md) có schema, provenance, hashes,
validator, cách dùng chat template, mask loss và chính sách split.
[Hướng dẫn evaluation](../data/evaluation/README.md) có lệnh bốn modes,
reviewed-label schema, capture/compare và thiết kế đánh giá tác động ba thành phần.

Cần nhóm cung cấp relevance judgments được review và feedback thật nếu muốn
đo recommendation cá nhân; Nam Anh cung cấp model/checkpoint cùng tokenizer và
training metadata. Live reranker cần môi trường tài nguyên/model phù hợp, AI
endpoint hoạt động và snapshot config/version để so sánh. Không dùng SFT test
để tune. Hiện ranking retrieval/recommendation không dùng LLM; muốn đo ảnh hưởng
qua query rewrite/tool selection phải thống nhất thí nghiệm riêng, không tự thêm
thuật toán vào production.

## Kiểm chứng và files

Lệnh regression:

```bash
PYTHONPATH=.:ai-service ai-service/.venv-gpu/bin/python -m pytest -q \
  ai-service/tests finetuning/tests \
  data/tests/test_evaluate_retrieval.py data/tests/test_evaluate_chatbot.py
```

**226 passed**, 1 Starlette deprecation warning, 0 failures. `git diff --check` sạch.
Kết quả cuối được lưu trong [python_tests.txt](evidence/week-06-ai-evaluation/python_tests.txt).
Một lượt sandbox TestClient treo ở đầu suite đã bị dừng (exit 130), không tính
PASS; suite chạy lại ngoài sandbox. Tests không download/load model thật hoặc
thay đổi Qdrant/MySQL; collection tests là in-memory. Validator rebuild chỉ
trong temp; test split chỉ dùng integrity audit. Một lỗi trong quá trình tạo v2
(do director=None bị loại khỏi prompt khi exclude_none) đã được sửa trước khi
artifact v2 được ghi; regression bao phủ source không có director.

Files sửa:

- `ai-service/app/services/retrieval.py`.
- `ai-service/tests/{test_retrieval,test_reranker,test_recommendation}.py`.
- `data/scripts/evaluate_retrieval.py`, `data/tests/test_evaluate_retrieval.py`.
- `finetuning/scripts/build_sft_v1.py` (mặc định v2-en, thêm English/runtime prompt).
- `docs/week05_ai_ranking_sft_vi.md` (ghi rõ SFT v1 đã retired).

Files thêm:

- `finetuning/scripts/validate_sft_v1.py`, `finetuning/tests/test_validate_sft.py`.
- `finetuning/datasets/v2-en/{train,validation,test}.jsonl`, `manifest.json`.
- `data/evaluation/chatbot_set_v1.json`, `data/evaluation/README.md`.
- `data/scripts/evaluate_chatbot.py`, `data/tests/test_evaluate_chatbot.py`.
- `docs/handoff_sft_week06_vi.md`, báo cáo này và `docs/evidence/week-06-ai-evaluation/*`.

Files xóa theo yêu cầu: `finetuning/datasets/v1/{train,validation,test}.jsonl`
và `manifest.json`. Danh sách chính xác kèm trạng thái Git ở
[changed_files.txt](evidence/week-06-ai-evaluation/changed_files.txt).
