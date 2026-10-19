# Đánh giá chất lượng chatbot

Nhánh này tách ba phép đo: F1 trích bộ lọc, khả năng chọn đúng phim trong câu hỏi
nối tiếp, và faithfulness/relevance do người đọc chấm. Điểm trên bộ kiểm tra
format của notebook QLoRA không thay thế ba phép đo này. Dữ liệu fixed-context
không đo chất lượng retrieval hoặc toàn bộ UI → backend → AI service.

## 1. Filter extraction F1

`data/evaluation/chat_filters_v1.json` có 12 câu Anh/Việt được viết thủ công để
chẩn đoán các kiểu filter thông dụng. Mỗi giá trị trường là một nhãn; danh sách
genre/language/country được chấm như tập hợp, số năm/rating/runtime và tên người
được chấm khớp chính xác. Report có micro precision/recall/F1, F1 theo trường,
exact-match theo câu và TP/FP/FN từng câu.

```bash
PYTHONPATH=ai-service python data/scripts/evaluate_chat_quality.py filters \
  --evaluation data/evaluation/chat_filters_v1.json --output /tmp/chat-filters.json
```

Trên đúng bộ 12 câu đã dùng để tìm và sửa lỗi, trước sửa: **21 TP, 1 FP, 4 FN,
micro-F1 0,894, exact-match 9/12**; sau sửa: **25 TP, 0 FP/FN, micro-F1 1,0,
exact-match 12/12**. Chi tiết và hash dữ liệu nằm trong
[`filters_before.json`](evidence/chat-quality-evaluation/filters_before.json) và
[`filters_after.json`](evidence/chat-quality-evaluation/filters_after.json).
Đây là **regression set in-sample**, không phải ước lượng F1 trên câu hỏi người
dùng thực tế. Muốn báo cáo F1 tổng quát phải gắn nhãn một holdout độc lập.

## 2. Base vs fine-tuned và memory continuity

Runner `evaluate_chatbot.py` hiện truyền `history` và `summary` vào prompt/guard
khi case cung cấp các trường này. Bộ `chat_memory_v1.json` gồm 3 ca synthetic:
tham chiếu phim gần nhất, đổi phim ở lượt sau, và summary cũ. Mỗi ca có hai phim
trong cùng context và nhãn `expected_movie_ids`, nên chọn đại một phim không
được tính đúng. Kết quả raw và guarded được chấm riêng.

Sau khi cả hai tag model đã **cài sẵn** trong Ollama, chạy cùng bộ nhớ cho mỗi
model; runner không tự pull model:

```bash
export EVAL=data/evaluation/chat_memory_v1.json
PYTHONPATH=ai-service python data/scripts/evaluate_chatbot.py capture \
  --evaluation "$EVAL" --model qwen2.5:3b --output /tmp/memory-base.json
PYTHONPATH=ai-service python data/scripts/evaluate_chatbot.py capture \
  --evaluation "$EVAL" --model TAG_FINE_TUNED --output /tmp/memory-tuned.json
PYTHONPATH=ai-service python data/scripts/evaluate_chatbot.py compare \
  --evaluation "$EVAL" --base /tmp/memory-base.json \
  --finetuned /tmp/memory-tuned.json --output /tmp/memory-paired.json
PYTHONPATH=ai-service python data/scripts/evaluate_chat_quality.py memory-score \
  --evaluation "$EVAL" --comparison /tmp/memory-paired.json \
  --output /tmp/memory-quality.json
```

`memory-score` từ chối capture cùng tag/digest, khác dataset hoặc thiếu case.
Điểm là tỷ lệ chọn đúng **status và đúng thứ tự movie IDs** trên ba ca; nó không
chứng minh memory persistence của MySQL hoặc tính đúng của dữ kiện phim.
Ngày 19/10/2026, capture base `qwen2.5:3b` trên máy local hoàn thành cả ba ca:
raw hợp lệ về JSON/source ID và guarded chọn đúng movie ID/status ở **3/3** ca.
[Raw capture](evidence/chat-quality-evaluation/base_memory_capture.json) ghi
digest và từng output. Đây chỉ là kiểm tra base trên ba ví dụ synthetic, chưa có
so sánh paired với model fine-tuned.

## 3. Faithfulness và relevance của câu trả lời

Chạy `capture` và `compare` trên `data/evaluation/chatbot_set_v1.json` theo
[hướng dẫn evaluation](../data/evaluation/README.md), dùng tên file riêng với
bộ memory. Sau đó xuất biểu mẫu A/B để người review chấm raw và guarded riêng:

Ngày 19/10/2026 đã capture **base** `qwen2.5:3b` trên đủ 22 ca context cố định:
22/22 ca không có exception; JSON contract và source identity đạt 22/22 ở output
thô lẫn sau guard; hai ca cấu trúc C20/C21 có status mong đợi. Digest model là
`357c53fb659c5076de1d65ccb0b397446227b71a42be9d1603d46168015c9e4b`.
[Capture gốc](evidence/chat-quality-evaluation/base_chatbot_22_capture.json)
(SHA-256 `6e1f047b52fd134943c808547b14180a3a1bc3535b90adab071062fcbca870de`)
giữ từng output và thời gian. Các phép kiểm này **không** đo faithfulness,
relevance hay retrieval; chưa có capture fine-tuned để so sánh paired.

```bash
PYTHONPATH=ai-service python data/scripts/evaluate_chat_quality.py review-template \
  --evaluation data/evaluation/chatbot_set_v1.json \
  --comparison /tmp/paired-comparison.json --output /tmp/chat-review.json
```

Mỗi output cần `reviewer` và bốn nhãn: `raw.faithful` và `guarded.faithful` là
boolean; `raw.relevance` và `guarded.relevance` là số nguyên 0–3. Faithful=true
khi mọi dữ kiện trả lời có trong context; relevance: 0 không liên quan, 1 yếu,
2 liên quan, 3 trả lời trực tiếp. Output lỗi/trống được chấm false và 0. Không
sửa question, context, raw, guarded hoặc `output_sha256`; file A/B không hiện
tên model. Cần ít nhất một reviewer đọc tất cả output; nên có reviewer thứ hai
để giải quyết bất đồng trước khi diễn giải điểm.

```bash
PYTHONPATH=ai-service python data/scripts/evaluate_chat_quality.py review-score \
  --evaluation data/evaluation/chatbot_set_v1.json \
  --comparison /tmp/paired-comparison.json --review /tmp/chat-review.json \
  --output /tmp/chat-quality.json
```

Scorer từ chối nhãn thiếu, nhãn sai kiểu, dữ liệu thay đổi và capture trùng
model. Report tách raw/guarded: faithfulness rate, tỷ lệ relevance ≥2, relevance
trung bình và chênh lệch fine-tuned trừ base. Không có nhãn thì **không có điểm
semantic quality**.

Artifact `w2w_english_v1_artifacts` chứa báo cáo QLoRA trên 198 ca test
synthetic về đạo diễn/thể loại, với thước đo khớp template nghiêm ngặt. Model
fine-tuned chưa có tag Ollama được xác minh trên máy lúc kiểm tra, nên chưa chạy
được paired capture hay review 22 ca ở đây. Không dùng tập test SFT để chỉnh prompt,
temperature hoặc chọn model; nếu thử cấu hình, dùng tập development riêng rồi
đóng băng một cấu hình trước khi chấm holdout.
