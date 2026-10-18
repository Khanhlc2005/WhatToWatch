# Đưa Qwen2.5-3B English-v1 vào Ollama

Adapter gốc là PEFT LoRA tại `w2w_english_v1_artifacts/adapter/`. Model gốc
được khóa ở `Qwen/Qwen2.5-3B-Instruct`, revision
`aa8e72537993ba99e69dfaafa59ed015b17504d1` trong `model_lock.json`.
Không dùng Qwen3 hoặc một base Qwen2.5 khác để merge. Giữ nguyên tag Ollama
`qwen2.5:3b` làm bản đối chứng và đường quay lại.

## Vì sao phải merge

Ollama local 0.34.2 từ chối Modelfile có `ADAPTER` với lỗi
`LoRA adapters are no longer supported`. Do đó không thể đưa trực tiếp
`adapter_model.safetensors` vào tag local. Script bên dưới nạp đúng base
Safetensors từ Hugging Face, merge adapter bằng PEFT và xuất model float16 hoàn
chỉnh. Ollama sau đó nhập thư mục Safetensors và lượng tử hóa khi tạo tag mới.
Xem [tài liệu nhập Safetensors](https://docs.ollama.com/import) và
[Modelfile](https://docs.ollama.com/modelfile) hiện hành.

## 1. Export trên Kaggle/Colab có GPU

Notebook chạy sẵn: [qwen25_export_ollama.ipynb](../notebooks/qwen25_export_ollama.ipynb).
Trên Kaggle, tạo notebook T4, bật Internet, thêm artifact English-v1 dưới dạng
Input dataset (thư mục hoặc ZIP `w2w_english_v1_artifacts.zip`), rồi chạy lần
lượt các cell. Trên Colab T4, đặt artifact trong Drive; notebook tự mount Drive
và tìm `model_lock.json`. Nếu có nhiều bản artifact, đặt
`ARTIFACTS_OVERRIDE` ở cell “Locate the saved artifact”. Chạy xong, lưu toàn bộ thư mục
`wtw-qwen25-english-v1-merged` từ output Kaggle hoặc Drive về máy chạy Ollama.
Đây là bước merge adapter đã train, không train lại.

Máy dev lúc kiểm tra có 7,5 GiB RAM tổng và swap gần đầy; base FP16 không có
trong cache. Vì vậy thực hiện merge trên Kaggle/Colab T4 sau khi gắn artifact
English-v1 và code của nhánh này. Dùng đúng môi trường notebook train
(`torch 2.6.0+cu124`, `transformers 4.53.3`, `peft 0.17.1`, `accelerate 1.10.1`).
GPU 0 phải có ít nhất 9 GiB VRAM trống. Script xác minh hash adapter trước khi
tải đúng revision base:

```bash
python tools/export_qwen25_merged.py \
  --artifacts /path/to/w2w_english_v1_artifacts \
  --output /kaggle/working/wtw-qwen25-english-v1-merged
```

Lưu **toàn bộ** thư mục export, gồm `config.json`, các shard `.safetensors`,
tokenizer và `export_manifest.json`. Đây là trọng số model hoàn chỉnh, lớn hơn
adapter; tải về máy chạy Ollama hoặc lưu bằng kênh artifact của nhóm. Không
commit trọng số vào Git.

## 2. Tạo tag Ollama riêng trên máy phục vụ

Script xác minh SHA-256 mọi file export rồi tạo Modelfile tạm với `FROM` trỏ
đến thư mục Safetensors. `int4` là lượng tử hóa của Ollama; nó không giống NF4
trong benchmark Kaggle, nên kết quả cần được đo lại sau import.

```bash
python tools/import_qwen25_ollama.py \
  --model-dir /path/to/wtw-qwen25-english-v1-merged \
  --tag whattowatch-qwen25-3b-sft:english-v1 --quantize int4
ollama list
ollama show whattowatch-qwen25-3b-sft:english-v1
```

Nếu import lỗi do kiến trúc hoặc RAM, giữ nguyên base đang chạy, lưu lỗi chính
xác và cân nhắc export GGUF từ model đã merge bằng công cụ hỗ trợ Qwen2.5.
Không sửa `OLLAMA_MODEL_NAME` trước khi tag mới chạy được.

## 3. Kiểm tra RAG và chọn tag trong AI service

Smoke dưới đây gọi prompt và JSON Schema thật của AI service trên ba context
mẫu cố định. Nó xác nhận định dạng/ID và một ca `no_match`, nhưng không đo
retrieval, hội thoại hay chất lượng trên catalog thật.

```bash
PYTHONPATH=ai-service python tools/smoke_qwen25_ollama.py --model qwen2.5:3b
PYTHONPATH=ai-service python tools/smoke_qwen25_ollama.py \
  --model whattowatch-qwen25-3b-sft:english-v1
```

Sau khi kiểm tra model mới, đặt trong `.env` của Compose:

```dotenv
OLLAMA_MODEL_NAME=whattowatch-qwen25-3b-sft:english-v1
```

Chạy lại AI service theo profile đang dùng; kiểm tra container nhìn thấy cùng
Ollama host/tag rồi gọi `POST /internal/chat` và `/chat` với tài khoản test.
Để quay lại base, đặt `OLLAMA_MODEL_NAME=qwen2.5:3b` và chạy lại AI service.
Compose hiện lấy biến này từ `.env`, mặc định là base. Không đổi prompt runtime.

Trước khi công bố cải thiện chất lượng, dùng runner
`data/scripts/evaluate_chatbot.py` để capture base và model mới trên cùng bộ
`data/evaluation/chatbot_set_v1.json`; review output thô và output qua guard.
Benchmark Kaggle 198/198 chỉ gồm câu hỏi đạo diễn/thể loại một phim, dùng NF4
và phép chấm khớp template nghiêm ngặt; không phải benchmark Ollama int4 hay
RAG end-to-end.
