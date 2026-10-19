# Kế hoạch phát hành demo chatbot WhatToWatch

Trạng thái được kiểm tra ngày **19/10/2026**. Mục tiêu demo là luồng `/chat` dùng
RAG trên catalog 46.923 phim, nhớ hội thoại, nhận bộ lọc, gọi công cụ chi tiết/so
sánh và có đường chạy riêng cho Qwen2.5-3B English-v1 đã fine-tune bằng QLoRA.
Đọc [kịch bản thao tác](chat_demo_scenarios_vi.md) cùng runbook này.

## Trạng thái và điều kiện ghép nhánh

`main` tại `c9c8554` đã gộp hai nhánh đầu; nhánh đánh giá chất lượng và nhánh
tài liệu này chưa được gộp. Demo tích hợp chưa được nghiệm thu chỉ vì từng nhánh
có test riêng.

| Nhánh | Trong `main`? | Phần đã có | Điều kiện còn lại |
|---|---|---|---|
| [`feature/chat-ollama-adapter`](https://github.com/Khanhlc2005/WhatToWatch/blob/feature/chat-ollama-adapter/docs/ollama_adapter_integration_vi.md) (`9c36021`) | Có, qua `a213b40` | Export adapter đã train, nhập model đã merge vào Ollama, smoke với context cố định | Xuất bản model hoàn chỉnh, cài tag fine-tuned trên máy demo và kiểm tra tag |
| [`feature/chat-e2e-flow`](https://github.com/Khanhlc2005/WhatToWatch/blob/feature/chat-e2e-flow/docs/chat_e2e_flow_vi.md) (`e5db567`) | Có, qua `c9c8554` | Xử lý lỗi AI thành HTTP 503, smoke UI → backend → AI | Chạy smoke trên stack thật có catalog |
| [`feature/chat-quality-evaluation`](https://github.com/Khanhlc2005/WhatToWatch/blob/feature/chat-quality-evaluation/docs/chat_quality_evaluation_vi.md) (`0c91bf9`) | Chưa | Filter F1, memory set, capture A/B, biểu mẫu chấm faithfulness/relevance | Ghép nhánh, capture hai tag trên cùng set; review chất lượng câu trả lời |

**Chưa đạt điều kiện phát hành demo fine-tuned:** máy kiểm tra chưa có tag Ollama
fine-tuned được xác minh; Docker daemon không hoạt động nên chưa chạy được E2E
trên stack và catalog thật. Tag `qwen-chat:latest` có trên máy không được xác nhận
là English-v1. Khi ghép các nhánh còn lại, rà xung đột và chạy lại các test liên
quan trên commit tích hợp; không dùng kết quả test nhánh riêng làm bằng chứng
cho commit mới.

## Chuẩn bị môi trường

Chạy các lệnh từ thư mục gốc repo. Phần demo chức năng dùng `main` đã ghép hai
nhánh đầu; runner đánh giá cần ghép nhánh quality. Cần có:

- Docker Engine/Compose hoạt động; Ollama truy cập được từ container AI; đủ RAM và
  ổ đĩa để nạp BGE-M3, Qwen và các service. Lần hỏi đầu có thể tải/nạp model lâu.
- `data/mysql/movies_data.sql` do nhóm dữ liệu cung cấp; file không nằm trong Git.
  Trên volume MySQL mới, Compose mới tự import dump này.
- Snapshot `data/processed/movies-46923-2026-10-11.snapshot` có SHA-256
  `9f98db41930a8d70f11692afb74e6b5dac5638cefb2d86b9dd6f03d30c3bf975`.
  Phục hồi **chỉ trên Qdrant volume mới chưa có collection `movies`**, theo
  [README mục Qdrant](../README.md#qdrant-với-catalog-46923-phim).
- Một tài khoản test đã tạo để đăng nhập `/chat`; giữ mật khẩu ngoài repo.

```bash
docker info
ollama list
docker compose config --services
test -s data/mysql/movies_data.sql
sha256sum data/processed/movies-46923-2026-10-11.snapshot
```

Nếu dùng catalog/snapshot khác, ghi rõ phiên bản và kiểm tra ID MySQL ↔ Qdrant
trước demo; các con số kỳ vọng bên dưới chỉ áp dụng cho catalog 46.923 phim.
Không chạy `docker compose down -v` với volume dữ liệu cần giữ.

Chạy preflight read-only để lưu hash/phiên bản, catalog count và danh sách điều
kiện thiếu. Cung cấp **thư mục model đã merge**, không phải thư mục adapter.
Script trả exit code `2` khi chưa đủ điều kiện; nó không phục hồi snapshot, khởi
động Docker hoặc thay đổi model.

```bash
python tools/chat_demo_preflight.py \
  --merged-model-dir /path/to/wtw-qwen25-english-v1-merged \
  --output /tmp/chat-demo-preflight.json
```

Nếu chưa có model đã merge, bỏ `--merged-model-dir` để nhận báo cáo cụ thể về
phần còn thiếu. `ready=true` chỉ xác nhận đầu vào và service đang chạy; vẫn phải
chạy smoke E2E và đánh giá chất lượng ở các phần sau.
[Preflight local ngày 19/10/2026](evidence/chat-demo-release/preflight-local-2026-10-19.json)
trả `ready=false`: adapter và SQL có mặt, còn thiếu model đã merge, snapshot,
Docker, tag fine-tuned và các service. Đây là bằng chứng môi trường hiện tại,
không phải kết quả chạy thử từ môi trường sạch.

## Chọn và kiểm tra model

`qwen2.5:3b` là tag base, giữ nguyên để đối chứng và quay lại. Adapter
`w2w_english_v1_artifacts/adapter/` là trọng số PEFT của
`Qwen/Qwen2.5-3B-Instruct` revision
`aa8e72537993ba99e69dfaafa59ed015b17504d1`. Ollama local 0.34.2 đã từ
chối Modelfile `ADAPTER`; cần **merge adapter với đúng base** trên Colab/Kaggle
T4 rồi nhập thư mục Safetensors hoàn chỉnh. Đây là bước xuất model đã train,
không train lại. Lệnh, notebook, hash check và cách tạo tag riêng nằm trong
[hướng dẫn nhánh adapter](https://github.com/Khanhlc2005/WhatToWatch/blob/feature/chat-ollama-adapter/docs/ollama_adapter_integration_vi.md).

Sau khi tag `whattowatch-qwen25-3b-sft:english-v1` được nhập thành công:

```bash
ollama show qwen2.5:3b
ollama show whattowatch-qwen25-3b-sft:english-v1
PYTHONPATH=ai-service python tools/smoke_qwen25_ollama.py --model qwen2.5:3b
PYTHONPATH=ai-service python tools/smoke_qwen25_ollama.py \
  --model whattowatch-qwen25-3b-sft:english-v1
```

Lưu tên tag **và digest** từ `ollama list` hoặc `/api/tags`. Chỉ sau smoke mới
đặt `OLLAMA_MODEL_NAME=whattowatch-qwen25-3b-sft:english-v1` trong `.env` và tạo
lại `ai-service`. Biến Compose này đã có trong `main`, mặc định `qwen2.5:3b`.
Ollama lượng tử hóa `int4` khi import, khác NF4 khi train
và benchmark; không chuyển thẳng điểm benchmark notebook thành điểm bản demo.

## Khởi động và kiểm tra stack

```bash
docker compose up -d --build mysql backend frontend
docker compose --profile ai up -d --build qdrant ai-service
docker compose ps
curl -fsS http://127.0.0.1:8010/internal/health
curl -fsS http://127.0.0.1:8080/movie-recommendation/movies/home-feed/top-rated
docker exec -e MYSQL_PWD=root whattowatch-mysql mysql -u root -N \
  whattowatch_db -e 'SELECT COUNT(*) FROM movies;'
curl -fsS -H 'Content-Type: application/json' -d '{"exact":true}' \
  http://127.0.0.1:6335/collections/movies/points/count
```

Kỳ vọng với dump/snapshot nêu trên: MySQL `46923`, Qdrant `count=46923`,
collection `green`; dense 1024/Cosine và sparse theo
[README](../README.md#qdrant-với-catalog-46923-phim). Endpoint `health` chỉ xác
nhận AI process trả lời, **không** xác nhận Qdrant, MySQL, embedding hoặc Ollama.
Đổi cổng Qdrant trong lệnh nếu dùng `QDRANT_HOST_PORT` khác `6335`. Nếu Ollama
chỉ bind `127.0.0.1` trên Linux, dùng cấu hình proxy profile `ai-local` trong
[README mục chatbot CPU](../README.md#chatbot-trên-cpu).

Chạy smoke tích hợp từ nhánh E2E với tài khoản test. Nó tạo hai lượt, đọc lại bốn
tin nhắn rồi xóa hội thoại do chính nó tạo; dùng `--keep` nếu cần xem trên UI.

```bash
export WTW_E2E_EMAIL='test@example.com'
read -rsp 'WTW_E2E_PASSWORD: ' WTW_E2E_PASSWORD; echo
export WTW_E2E_PASSWORD
python tools/chat_e2e_smoke.py --base-url http://127.0.0.1:3000
unset WTW_E2E_PASSWORD
```

Mở `http://127.0.0.1:3000/chat`, đăng nhập và làm theo
[kịch bản demo](chat_demo_scenarios_vi.md). Nếu chat trả 503 sau khi ghép nhánh
E2E, kiểm tra `docker compose logs --tail=100 ai-service backend`, kết nối
Qdrant/catalog/Ollama và tag đang cấu hình. Giữ timeout backend chat lớn hơn
timeout Ollama như README. Khi cần quay lại base, đặt
`OLLAMA_MODEL_NAME=qwen2.5:3b`, tạo lại `ai-service`, rồi lặp smoke và kịch bản.

## Bằng chứng hiện có và phần chưa được chấm

| Phép đo | Kết quả đã có | Phạm vi đúng |
|---|---|---|
| SFT QLoRA English-v1 | Test synthetic 198 ca: base schema hợp lệ 131/198, adapter 198/198; `all_checks` 0/198 → 198/198 | Khớp template nghiêm ngặt cho facts đạo diễn/thể loại với NF4 trong notebook; không đo RAG/Ollama int4 hay semantic faithfulness. Nguồn: artifact local `w2w_english_v1_artifacts/reports/summary.json`, không có trong Git. |
| Filter extraction | Micro-F1 0,894 → 1,0; exact-match 9/12 → 12/12 | 12 câu curated đã dùng để sửa lỗi, là regression in-sample; [chi tiết](https://github.com/Khanhlc2005/WhatToWatch/blob/feature/chat-quality-evaluation/docs/chat_quality_evaluation_vi.md). |
| Memory base | Guarded đúng movie ID/status 3/3 | Ba ca synthetic có context cố định, chưa chứng minh MySQL persistence; chưa có paired fine-tuned. |
| Chatbot base trên bộ 22 ca | 22/22 không có lỗi chạy; raw/guarded JSON contract và source identity 22/22 | Context cố định, chỉ kiểm tra cấu trúc/ID. Capture nằm trên nhánh quality tại commit `d75d044`; chưa có nhãn faithfulness/relevance. |
| Live E2E, base vs fine-tuned, faithfulness/relevance | Chưa có kết quả đủ điều kiện báo cáo | Cần chạy smoke stack thật; capture hai tag cùng set 22 ca, review raw và guarded; cần holdout filter và kiểm tra retrieval nếu muốn báo cáo chất lượng tổng quát. |

Không gộp các tỷ lệ trên thành một điểm chất lượng. Sau khi model fine-tuned
được cài, chạy [quy trình đánh giá nhánh quality](https://github.com/Khanhlc2005/WhatToWatch/blob/feature/chat-quality-evaluation/docs/chat_quality_evaluation_vi.md),
ghi commit tích hợp, tag/digest hai model, hash dataset/prompt, số catalog, ngày
chạy, lỗi từng ca và nhãn reviewer. Chỉ công bố so sánh semantic khi có nhãn.

## Tiêu chí chốt demo

- [ ] Ba nhánh chức năng đã ghép, xung đột đã xử lý và test trên commit tích hợp đạt.
- [ ] MySQL/Qdrant đúng catalog, Ollama base và fine-tuned có tag/digest xác minh;
      `ai-service` đang dùng đúng tag công bố.
- [ ] Smoke UI → Next.js → Spring → AI → catalog/Ollama đạt trên stack thật;
      hội thoại hai lượt lưu/đọc được. Test rollback ở nhánh E2E đạt trên commit
      tích hợp; nếu có lỗi AI thực tế, xác nhận HTTP 503 không lưu lượt trả lời giả.
- [ ] Kịch bản gợi ý, follow-up, bộ lọc, detail/compare được ghi nhận bằng
      movie ID nguồn và response thực tế; không dùng ID hoặc kết quả dựng trước.
- [ ] Paired capture và review A/B được lưu; giới hạn của dữ liệu test được nêu
      cùng kết quả. Nếu thiếu bước này, chỉ giới thiệu bản demo chức năng và ghi
      rõ chưa có bằng chứng fine-tuned cải thiện chất lượng chatbot.
