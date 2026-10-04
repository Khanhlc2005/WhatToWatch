# Chạy AI Service (FastAPI) cục bộ — Issue #9

## 1. Chuẩn bị môi trường

```bash
cp ai-service/.env.example ai-service/.env
pip install -r requirements.txt
```

Chỉnh `ai-service/.env` nếu cần, đặc biệt `EMBEDDING_DEVICE` (`cpu` nếu máy không có GPU CUDA).

## 2. Khởi động Qdrant

```bash
docker compose up -d qdrant
```

Kiểm tra Qdrant lên bằng `docker compose ps`. Chạy schema/seed nếu chưa có:

```bash
python qdrant/scripts/create_collections.py
```

## 3. Chạy FastAPI service

```bash
cd ai-service
uvicorn app.main:app --reload --port 8010
```

## 4. Kiểm tra qua OpenAPI

- Swagger UI: http://localhost:8010/docs
- OpenAPI schema: http://localhost:8010/openapi.json

Các endpoint hiện có:

| Method | Path | Mục đích |
| --- | --- | --- |
| GET | `/internal/health` | Health check của service |
| GET | `/internal/qdrant/health` | Kiểm tra kết nối Qdrant và danh sách collection |
| GET | `/internal/qdrant/sample?limit=5` | Truy xuất dữ liệu mẫu từ collection `movies` |
| POST | `/internal/qdrant/search` | Dense hoặc sparse search với payload filters; MySQL ID có thể chưa được mapping |
| POST | `/internal/chat` | Điểm tích hợp chatbot (Ollama/Qwen2.5), thống nhất với Nam Anh |

## 5. Chạy test

```bash
cd ai-service
pytest
```

Dockerfile dùng build context ở repo root. Xem [contract và lệnh demo Docker/retrieval](retrieval_data_contract_vi.md) để chạy profile `ai`, kiểm tra ID và giới hạn khi chưa có CSV MySQL.
