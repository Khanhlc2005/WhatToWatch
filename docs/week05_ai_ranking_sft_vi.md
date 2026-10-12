# Tuần 5 — reranking, final ranking và SFT v1

## Search: Hybrid + BGE reranker v1

`POST /internal/qdrant/search` giữ mặc định `mode=dense`, `rerank=false` và
`limit=10`. Bật `rerank=true` cho dense, sparse hoặc hybrid. `candidate_k` (1–500)
chỉ có hiệu lực khi bật rerank; nếu bỏ trống, dùng `RETRIEVAL_CANDIDATE_K=50`.
`limit` là final-K (mặc định `RETRIEVAL_FINAL_K=10`, 1–100). Pool thực tế ít
nhất bằng final-K. Mỗi nhánh Qdrant lấy candidate-K với cùng payload filters;
hybrid dùng RRF **một lần**, deduplicate theo identity hiện có, rồi cross encoder
chấm pool duy nhất. Không áp RRF lần hai.

```json
{"query":"space travel","mode":"hybrid","rerank":true,"candidate_k":50,"limit":10,"filters":{"genres":["Science Fiction"]}}
```

Reranker `BAAI/bge-reranker-v2-m3` được load lười bằng FlagEmbedding. Có thể
trỏ `RERANKER_MODEL_PATH` tới model đã có sẵn và chọn `RERANKER_DEVICE` sau khi
kiểm tra tài nguyên. Qdrant payload hiện chỉ có title/genres/keywords; đây là
văn bản đưa vào cross encoder. Overview không nằm trong payload; muốn dùng nó
phải có thay đổi index được review riêng. Candidate thiếu cả ba trường vẫn ở
cuối danh sách theo thứ tự retrieval; không tạo văn bản giả.

Khi `rerank=true`, `hit.score` là raw cross encoder score nếu được chấm,
`retrieval_score` là dense/sparse/RRF score trước rerank, `rerank_score` là raw
cross encoder score. Với candidate thiếu văn bản, `score` giữ retrieval score và
`rerank_score` vắng mặt. Raw score không phải xác suất. Khi `rerank=false`,
response cũ không thêm các field score mới. `movie_id`, `id_status`, metadata và
filters dùng đường xử lý cũ. Lỗi model/Qdrant trả 503 generic; không âm thầm
trả ranking khác.

## Recommendation: final ranking v1

`POST /internal/recommendations` giữ mặc định `ranking=cosine` để bảo toàn
score và response MVP. Backend có thể gửi `ranking=final` để nhận final score,
`score_components` và `reasons` từng hit. Không cần đổi request/exclusion cũ.
Profile thiếu: `cold_start`, `hits=[]`; Backend quyết định feed fallback.

Final ranking chỉ dùng hai tín hiệu thực có trong Qdrant: cosine giữa user
profile và movie vector, IMDb rating trong payload. Chuẩn hóa cố định:

```text
profile_similarity = clamp((cosine + 1) / 2, 0, 1)
imdb_rating = IMDb rating / 10, nếu rating hợp lệ trong [0,10]
final_score = 0.8 * profile_similarity + 0.2 * imdb_rating
```

Weights cấu hình bằng `RECOMMENDATION_SIMILARITY_WEIGHT` và
`RECOMMENDATION_IMDB_WEIGHT`, mặc định 0.8/0.2 theo quyết định của nhóm trong
task này. Khi IMDb rating thiếu/sai, bỏ component đó và chuẩn hóa lại weights
còn lại; không gán rating giả bằng 0. Hòa điểm sắp movie_id tăng dần.
Candidate retrieval vẫn dense top `max(50,5*limit)`, filters/exclusions áp ở
Qdrant và loại lại trong Python. Không dùng lexical, overlap, novelty hoặc vote
count vì profile/payload hiện chưa cung cấp đủ tín hiệu đã xác thực. Chưa tune
weights trên relevance labels vì bộ manual evaluation tuần 4 vẫn chưa được duyệt.

Reason codes gồm `profile_similarity` (cosine dương, weight >0) và
`imdb_rating` (rating hợp lệ, weight >0). Mỗi reason có `value` đã chuẩn hóa;
UI có thể hiển thị “Phù hợp với sở thích từ các phim đã đánh giá” hoặc “IMDb
rating: X/10” tương ứng. Không suy ra thể loại yêu thích, diễn viên hoặc phim
đã xem từ vector. JSON score components được log cho `ranking=final` theo
user_id/movie_id để evaluation; tránh chuyển các log này tới telemetry công khai.

## SFT dataset v1 cho Nam Anh

`finetuning/datasets/v1/{train,validation,test}.jsonl` là **synthetic template
examples** sinh từ metadata thật trong `data/processed/movies_with_mysql_ids.jsonl`.
Không có hội thoại thật, relevance labels, hay câu trả lời do người dùng duyệt.
Mỗi dòng gồm `messages` (system/user/assistant) và `provenance` ghi source hash,
movie_id và generator. User message chứa MOVIE_CONTEXT một phim; assistant
message là JSON có `status`, `answer`, `movies` theo contract RAG. Chỉ có câu
hỏi fact về đạo diễn/thể loại khi source có dữ liệu. Đây là task hẹp nhằm tập
format và grounding; không dùng test split để điều chỉnh prompt hoặc weights.

Tạo lại bằng:

```bash
python finetuning/scripts/build_sft_v1.py --max-movies 1000
```

Script chọn phim bằng hash ổn định, chia 80/10/10 theo hash movie_id, bảo đảm
cùng phim không đi qua split khác, kiểm tra trùng dòng và đối chiếu target với
context. `manifest.json` ghi source SHA-256, số mẫu và kiểm tra leakage.
Nam Anh dùng `messages` làm input SFT và bỏ `provenance` khỏi tensor training;
áp chat template từ tokenizer **Qwen/Qwen3-4B**, `enable_thinking=False`, rồi
mask loss ở system/user để chỉ học assistant JSON. Không tự ghép special tokens
vào JSONL. Kiểm tra tokenizer/training stack trong môi trường tuần 6 trước khi
chạy; giai đoạn này chưa download hoặc train model. Model runtime repository vẫn
là Qwen2.5 3B; việc chuyển inference sang Qwen3 4B cần Nam Anh xác nhận và
benchmark riêng. Tham khảo [Qwen3-4B model card](https://huggingface.co/Qwen/Qwen3-4B)
về `apply_chat_template` và `enable_thinking`.

## Handoff và giới hạn đo

- **Khánh Vũ:** truyền `rerank=true`/candidate-K khi muốn dùng search mới, và
  `ranking=final` khi muốn final recommendation; hydrate theo thứ tự AI trả,
  truyền exclusion IDs từ nghiệp vụ và xử lý `cold_start` tại Backend.
- **Nam Anh:** review provenance/targets, dùng script và manifest trên training
  environment; giữ test split chưa xem khi đánh giá. Cần bổ sung hội thoại thật
  được phép sử dụng hoặc dữ liệu người review nếu muốn SFT vượt task format.
- Chưa có phép đo live reranker: máy hiện có khoảng 2,3 GiB RAM khả dụng; chưa
  tải model. Test reranker dùng mock model và Qdrant in-memory. Chưa có relevance
  đã duyệt để báo Precision/nDCG gain. Chưa có user ratings thật để đo ranking.

## Kiểm tra đã chạy

`PYTHONPATH=ai-service ai-service/.venv-gpu/bin/python -m pytest -q
ai-service/tests finetuning/tests`: 179 passed, 1 cảnh báo deprecation từ
Starlette. 1.996/1.996 target SFT được parse bằng `MovieContext`, `RAGAnswer`
và `parse_answer` hiện tại. `git diff --check` sạch. FastAPI `TestClient`
trong sandbox của phiên làm việc treo cả với app tối thiểu; suite đã chạy trong
môi trường execution được cấp quyền và hoàn tất trong vài giây. Kiểm thử này
không gọi Qdrant/Ollama live hoặc download model.

## Files thay đổi (19)

- Cấu hình/API: `.env.example`, `ai-service/app/core/config.py`,
  `ai-service/app/api/routers/qdrant.py`,
  `ai-service/app/api/routers/recommendation.py`,
  `ai-service/app/schemas/retrieval.py`,
  `ai-service/app/schemas/recommendation.py`.
- Services: `ai-service/app/services/retrieval.py`,
  `ai-service/app/services/reranker.py`,
  `ai-service/app/services/recommendation.py`.
- Tests: `ai-service/tests/test_retrieval.py`,
  `ai-service/tests/test_reranker.py`,
  `ai-service/tests/test_recommendation.py`,
  `finetuning/tests/test_build_sft_v1.py`.
- Dataset/script: `finetuning/scripts/build_sft_v1.py`,
  `finetuning/datasets/v1/train.jsonl`,
  `finetuning/datasets/v1/validation.jsonl`,
  `finetuning/datasets/v1/test.jsonl`,
  `finetuning/datasets/v1/manifest.json`.
- Tài liệu: `docs/week05_ai_ranking_sft_vi.md`.
