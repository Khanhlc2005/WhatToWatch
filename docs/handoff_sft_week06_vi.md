# Bàn giao SFT tuần 6 cho Nam Anh

Khánh Bùi chuẩn bị ngày 14/10/2026 trên `feature/week6-ai-evaluation`.
Theo quyết định của Khánh Bùi, giữ contract runtime **tiếng Anh**, xóa artifact
v1 tiếng Việt và dùng `finetuning/datasets/v2-en/`. Chưa training, chưa đổi runtime
Qwen2.5 3B sang Qwen3. Tài liệu tuần 5 là lịch sử.

## Artifact và phạm vi

| Split | Phim | Mẫu |
|---|---:|---:|
| train | 808 | 1.613 |
| validation | 93 | 185 |
| test | 99 | 198 |

1.000 phim được chọn bằng hash ổn định từ metadata catalog thật. Hai loại câu
hỏi: director và genres. Đây là **synthetic template examples**, không phải hội
thoại thật, relevance labels, đánh giá của người dùng hoặc dữ liệu đã human-review.
Không có supervision về recommendation cá nhân, fallback, multi-turn hay chất
lượng giải thích. Dataset phù hợp để thử học format/grounding trong phạm vi hẹp.

Mỗi JSONL row gồm `messages` và `provenance`. Messages theo thứ tự
system/user/assistant; assistant content là JSON có `status`, `answer`, `movies`.
`movie_id` trong JSON RAG là **string của MySQL ID**, khác với retrieval API dùng
integer; không dùng Qdrant point ID hay TMDB ID thay thế. Title được copy từ context.
V2 dùng chính `SYSTEM_PROMPT` và `build_user_prompt` runtime, có history/summary
rỗng và cùng cấu trúc context. Manifest lưu hash prompt, source và split policy.

Provenance gồm `origin`, `source`, `source_sha256`, `source_movie_id`, `generator`.
Source là `data/processed/movies_with_mysql_ids.jsonl`, SHA-256:
`f6c18688f4ba09b514bdf53cf329961441d3b759fcae769a0170b23525956400`.
Source processed và MySQL CSV bị Git ignore; Nam Anh cần nhận bản catalog đúng
hash qua kênh dữ liệu của nhóm nếu muốn chạy lại validator. JSONL dùng trực tiếp
cho SFT không cần source ngoài, nhưng không được bỏ provenance trong artifact lưu trữ.

## Kiểm tra trước training

Từ repo root, dùng Python environment đã có dependencies AI Service:

```bash
PYTHONPATH=.:ai-service ai-service/.venv-gpu/bin/python finetuning/scripts/validate_sft_v1.py \
  --dataset finetuning/datasets/v2-en \
  --report /tmp/sft-v2-en-quality.json
```

Tên script giữ tương thích với generator tuần 5; mặc định hiện là v2-en.
Validator kiểm tra roles/schema/provenance, source hash, IDs, duplicate messages,
phân split deterministic, leakage cả movie_id/IMDb/TMDB, `MovieContext`,
`parse_answer`, và rebuild vào thư mục tạm để đối chiếu chính xác targets/facts/
manifest. **Không ghi lại split đang kiểm tra**. Integrity audit của test split
không được dùng để tune prompt, weights hay chọn checkpoint.

Báo cáo [quality](evidence/week-06-ai-evaluation/sft_v2_en_quality.json) có hashes
của cả bốn artifact. `training_ready` chỉ biểu thị đạt kiểm tra kỹ thuật và ngôn
ngữ; Nam Anh vẫn review scope, stack và tài nguyên trước training. Không diễn giải
PASS integrity thành PASS chất lượng semantic.

Tái tạo vào thư mục riêng để review, không overwrite artifact bàn giao:

```bash
PYTHONPATH=.:ai-service ai-service/.venv-gpu/bin/python finetuning/scripts/build_sft_v1.py \
  --language en --max-movies 1000 --output /tmp/sft-v2-en-rebuild
```

## Trách nhiệm training của Nam Anh

- Dùng `messages`; loại `provenance` khỏi tensor training nhưng giữ trong bản lưu.
- Dùng chat template đúng tokenizer/model được nhóm chốt; không ghép special
  tokens thủ công. Mask loss system/user, chỉ học assistant JSON.
- Chọn checkpoint/hyperparameters bằng train/validation. Giữ test ngoài mọi
  quyết định tuning; dùng một lần cho kết quả cuối đã chốt.
- Kế hoạch Qwen3-4B tuần 5 chưa xác minh stack/tokenizer trong phiên này. Giữ
  output JSON và English contract; runtime migration cần quyết định riêng.
- Bàn giao model adapter/checkpoint, base model chính xác, tokenizer/template,
  generation settings, commit/code version, hashes dataset, seed và training log.
- Review mẫu **train/validation** về tên riêng, grounding và độ đa dạng trước khi
  chạy. Việc dataset chỉ có hai templates cần ghi trong báo cáo kết quả.

Khánh Bùi đã chuẩn bị 22 cases chatbot và runner capture/compare. Khi có model
fine-tuned được phục vụ riêng, dùng hướng dẫn [evaluation](../data/evaluation/README.md).
Không gửi dữ liệu này cho Nam Anh qua công cụ nhắn tin trong phiên này; đây là
artifact bàn giao trong repo.
