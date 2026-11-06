# Evaluation tuần 6

Đánh giá filter F1 dùng `chat_filters_v1.json` với `data/scripts/evaluate_chat_quality.py filters`.

`query_set_v1.json` giữ 18 queries semantic/keyword/filter Anh-Việt, final-K=10.
Anchors chỉ xác minh identity catalog; không phải relevance labels. Q18 là kiểm
tra cấu trúc empty do filters mâu thuẫn. Không gán relevance tự động từ anchors,
IMDb rating hoặc text overlap.

## Retrieval

Từ repo root:

```bash
ai-service/.venv-gpu/bin/python data/scripts/evaluate_retrieval.py \
  --base-url http://127.0.0.1:8010 \
  --modes dense sparse hybrid hybrid_reranker --candidate-k 50 \
  --output /tmp/week6-retrieval-run
```

Mặc định vẫn là ba modes cũ. `hybrid_reranker` gửi API `mode=hybrid,rerank=true`;
các modes còn lại giữ `rerank=false` mặc định. Candidate-K chỉ áp dụng reranker;
final-K lấy từ query set. RRF chạy một lần trong service. Đây là so sánh cấu hình
production, không phải thí nghiệm pool giống nhau: hybrid baseline lấy mỗi nhánh
final-K, reranker lấy mỗi nhánh candidate-K. Nếu tune candidate-K, dùng evaluation
development riêng.

Trước khi chạy live, kiểm tra dịch vụ, cache/model đã có và RAM/VRAM. Endpoint
reranker có thể load/download model lazily; phiên tuần 6 **chưa gọi live reranker**.
Không chạy lệnh trên khi chưa xác nhận môi trường model phù hợp. Runner chỉ gọi
search read-only, không xóa/rebuild collection.

Outputs: request/response/latency/issues JSONL, summary với input hashes, pooled
CSV và bảng thứ tự. Checks gồm MySQL/IMDb/TMDB identity đối chiếu catalog/CSV,
filters, duplicate IDs, final-K và score order. Reranker có hai nhóm scored và
unscored: raw cross-encoder scores giảm dần, unscored ở cuối giữ retrieval order;
không so score cross-encoder với retrieval score của nhóm unscored.

## Nhãn và quality metrics

Pooled CSV được export với `relevance`, `reviewer`, `notes` rỗng. Reviewer điền
relevance nguyên 0..3 (0: không liên quan, 1: liên quan ít, 2: liên quan,
3: rất liên quan) và định danh reviewer. Nhóm cần chốt rubric và review bất đồng
trước khi dùng; đây chỉ là schema đầu vào. Giữ nguyên query/filter/movie IDs.

```bash
ai-service/.venv-gpu/bin/python data/scripts/evaluate_retrieval.py \
  --modes dense sparse hybrid hybrid_reranker --candidate-k 50 \
  --labels /path/to/reviewed-pool.csv --output /tmp/week6-reviewed-run
```

Reject grade sai, thiếu reviewer, query/filter lệch, ID lạ hoặc judgments trùng.
Chỉ tính P@K, MRR@K và nDCG@K khi **mọi hit của tất cả modes đang so sánh** được
judged, có ít nhất một positive và query không có lỗi request/structural.
P@K chia cho K kể cả thiếu hits; positive là grade>0; nDCG dùng gain `2^grade-1`,
ideal từ **pool đã judged**, không phải toàn catalog. Không tính Recall vì pool
không exhaustive. Queries không đủ điều kiện được ghi `skipped`, không gán 0.
Hiện 18 queries và 280 dòng manual tuần 4 có **0 labels/reviewers**; chưa có
quality metrics thực tế.

## Chatbot (fixed context)

`chatbot_set_v1.json` đóng băng 22 cases: 18 queries gốc với catalog anchors làm
context, hai câu hỏi facts, empty context và missing director. Context được cung
cấp cố định để tách ảnh hưởng model khỏi retrieval; không tuyên bố đây là context
live retrieval. `chat_memory_v1.json` có 3 ca memory.

Tái tạo bộ evaluation sau thay đổi source chỉ bằng version mới, giữ bộ đã chốt:

```bash
PYTHONPATH=ai-service ai-service/.venv-gpu/bin/python data/scripts/evaluate_chatbot.py prepare \
  --output /tmp/chatbot-set-review.json
```

Với model đã cài sẵn trong Ollama:

```bash
PYTHONPATH=ai-service ai-service/.venv-gpu/bin/python data/scripts/evaluate_chatbot.py capture \
  --evaluation data/evaluation/chatbot_set_v1.json --model qwen2.5:3b \
  --ollama-url http://localhost:11434 --output /tmp/base-capture.json
```

Capture kiểm tra `/api/tags`, từ chối model chưa cài, không pull hoặc đổi runtime.
Lưu model digest, prompt/input hash và generation settings (temperature=0,
seed=42, num_predict=512). Output đầu thô và output qua `answer_question`
(guard/retry hiện hành) được ghi riêng. JSON/source identity checks là kiểm tra
contract, reason fact substring là proxy hạn chế, **không phải semantic quality
metrics**.

## Đánh giá tác động

| Thành phần | Thí nghiệm cần chốt | Giới hạn hiện tại |
|---|---|---|
| Retrieval | Giữ catalog/index/filters/K; bốn modes trên cùng reviewed queries. Nếu chatbot rewrite query, lưu original/rewrite và relevance do người review. | Dense/sparse/RRF/reranker không dùng chatbot model. |
| Recommendation | Dùng cùng snapshot ratings thật, exclusions và profile version; lưu IDs/order/score components/reasons trước/sau. | Ranking cosine/final không gọi LLM; chưa có feedback hợp lệ để đo gain cá nhân. |
| Explainability | Cùng context/reason codes, đánh giá correctness, grounding và usefulness bằng reviewer; đọc raw lẫn guarded output. | Guard hiện viết lại reasons. |

Chưa thêm query rewriting hoặc LLM reranking vào production. Không tạo user
ratings/feedback giả. Để đo end-to-end sau này cần đóng băng output retrieval và
recommendation thật rồi hydrate cùng context cho cả model; không dùng anchors
làm ground truth relevance.
