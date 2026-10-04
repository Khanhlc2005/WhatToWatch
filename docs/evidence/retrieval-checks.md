# Verification — retrieval/data contract (2026-10-04)

Branch: `feature/khanh-retrieval-data-contract`; base `da0672d`. Frontend files imported from `anhvn-setup-UI` at `b66a05a`. No new commit, staging, or push.

| Check | Result | Scope / limitation |
| --- | --- | --- |
| `PYTHONPATH=ai-service python3 -m pytest -q ai-service/tests data/tests/test_movie_links.py` | PASS: 42 tests | Host Python 3.14; model embedding fixtures, Qdrant in-memory; one Starlette deprecation warning |
| AI tests in `whattowatch-ai:local` | PASS: 35 tests | Python 3.11 Docker environment, network disabled; one Starlette deprecation warning |
| Frontend `npm ci`, `npx tsc --noEmit`, `npm run test:contract`, `npm run lint`, `npm run build` | PASS | Node 20 container; starter emits dependency/Browserslist deprecation warnings. No dependency upgrades |
| Frontend contract tests after adding route-ID assertions | PASS | DTO identity/ratings/null handling, numeric route IDs accepted and UUID/unsafe IDs rejected |
| `docker compose --profile ai config --quiet` | PASS | Configuration validation only, does not prove database integration |
| `docker build -f ai-service/Dockerfile -t whattowatch-ai:local .` | PASS | First attempt timed out downloading PyTorch; succeeded after increasing pip timeout. Final image includes current source/cache permissions |
| Docker runtime | PASS | Default CMD started uvicorn; real HTTP GET `127.0.0.1:8010/internal/health` returned status ok. Temporary container removed |
| Docker BGE-M3 import/cache | PASS | `from FlagEmbedding import BGEM3FlagModel`; UID 10001; HF_HOME writable. No model inference or model download |
| Python compile / `git diff --check` | PASS | Changed Python modules and whitespace checks |
| Sample ID audit | INCOMPLETE (expected exit 1) | Three sample movies, all missing movie_id; no supplied MySQL CSV or Qdrant snapshot. See `retrieval-id-audit.json` |
| Live Qdrant audit | BLOCKED | Connection refused at localhost:6335; no data read from collection |
| Real model inference | NOT VERIFIED | Host attempt failed before inference: installed transformers requires huggingface-hub <2, host has 2.0.0. Docker import passes, but cached snapshot lacks PyTorch model weights; no weights downloaded for this task |
| MySQL ↔ Qdrant / full UI-backend E2E | NOT RUN | Awaiting CSV IDs; no verified import or running MySQL/backend fixture. User requested leaving current import script unchanged |

Docker final image manifest: `sha256:d751f731d6ca60817a093a4c397e43182ce19d618692606bb8696fdacb56e08f`.

No change to `tools/prepare_movies_sql.py`, backend source, or stored Qdrant payloads. Existing local changes to catalog scripts, seeds, requirements and collection scripts were preserved. Code and offline tests do not establish that pending MySQL IDs resolve correctly.

## Chốt phạm vi bàn giao theo yêu cầu mới

Người dùng đã loại các nhiệm vụ phụ thuộc CSV MySQL khỏi đợt này. Phần triển khai và kiểm tra trong phạm vi còn lại đã hoàn thành; các hàng MySQL/CSV INCOMPLETE/NOT RUN phía trên thuộc công việc hoãn, không phải tuyên bố mapping đã xong. Checklist tiếp tục nằm trong [tổng kết bàn giao](../handoff_retrieval_vi.md).

Kiểm tra cuối đợt trên nguồn hiện tại:

- `ruff check --no-cache .` trong thư mục ai-service, container Python 3.11: **PASS**, toàn bộ app/scripts/tests.
- Lệnh CI mới `python -m pytest -q tests` từ working-directory ai-service: **35 passed**, một warning deprecation Starlette; chạy network disabled, cache test ở /tmp.
- `docker compose --profile ai config --quiet`: **PASS**.
- `git diff --check`: **PASS**; Git index không có file staged.
- Không thay đổi code runtime kể từ Docker build/smoke và frontend build đã báo PASS phía trên. Lần chốt chỉ cập nhật CI và tài liệu phạm vi/việc hoãn.

## Chuẩn hóa thư mục frontend

Đã chuyển toàn bộ nội dung `nextflix/` vào thẳng `frontend/`, cập nhật CI (paths, working-directory, npm cache lockfile) và lệnh trong tài liệu. Các nhắc đến `nextflix/` ở phần nguồn gốc chỉ thư mục gốc của branch UI.

Sau khi chuyển: `npx --no-install tsc --noEmit`, `npm run test:contract`, `npm run lint`, `npm run build` đều **PASS** trong Node 20 container. `frontend/node_modules` và `frontend/.next` vẫn được Git ignore. Không add/commit/push.
