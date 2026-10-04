# Data contract và retrieval — Khánh Bùi

> Phạm vi bàn giao đã cập nhật: người dùng loại các nhiệm vụ phụ thuộc CSV MySQL khỏi đợt này. Xem [tổng kết và checklist việc hoãn](handoff_retrieval_vi.md).

## Nguồn và trạng thái

- **CONFIRMED:** base `main` ở `da0672d`; frontend lấy riêng thư mục `nextflix/` (nay nằm trong `frontend/`) tại `b66a05a` từ `anhvn-setup-UI` (hai commit riêng của branch: `b2ce71a`, `b66a05a`). Không merge backend UUID cũ từ branch UI vào backend Long ID hiện tại. Không tạo commit mới.
- **CONFIRMED:** FastAPI `app.main:app`, port 8010; `BAAI/bge-m3` qua `FlagEmbedding.BGEM3FlagModel`, max length 512, dense 1024/Cosine và sparse lexical weights. Collection mặc định `movies`, vector names `dense`, `sparse`.
- **CONFIRMED:** `Movie` JPA dùng bảng `movies`, `Long id` tự tăng; `MovieSummaryResponse` và `MovieDetailResponse` cũng dùng Long. `init.sql` lại tạo bảng `movie`; `prepare_movies_sql.py` chèn UUID. Giữ nguyên các file này theo yêu cầu người dùng; chưa có bằng chứng import hiện tại khớp JPA.
- **MISSING:** CSV ID từ MySQL và kết quả xác minh sau import. Không suy đoán `movies.id` từ IMDb/TMDB hoặc UUID point. Chưa thực hiện ghi mapping Qdrant, hydrate search results qua MySQL hoặc nối search AI vào UI.
- **INFERRED:** frontend có thể dùng API phim của main sau adapter ID số; cần chạy end-to-end với backend/MySQL để xác minh thực tế.

## Mapping source → processed → MySQL → Qdrant → API/UI

Nguồn mẫu: `data/seeds/imdb_tmdb_sample.jsonl`; chuẩn hóa bằng `data/scripts/clean_movies.py` thành `data/seeds/movies_cleaned_sample.jsonl`. `embedding_template.py` tạo `embedding_text` deterministic. Đây là dữ liệu thật có sẵn trong repo, không phải kết quả import mới.

| Source/processed | MySQL theo entity JPA | Qdrant theo `index_sample_movies.py` | API/UI hiện tại |
| --- | --- | --- | --- |
| `movie_id` (chưa có, null) | `movies.id` tự tăng sau import | payload `movie_id`; **khác point ID** | DTO `id` số → `Movie.id` chuỗi thập phân cho URL |
| `imdb_id`, `tmdb_id` | `imdb_id`, `tmdb_id` unique theo JPA | payload cùng tên; point UUID5 từ `whattowatch:movie:{imdb_id}` với `NAMESPACE_URL` | detail `imdbId`, `tmdbId`; không dùng làm ID điều hướng |
| `title`, `original_title` | `title`, `original_title` | `title`; original title nằm trong embedding text | summary/detail `title` → `Movie.title` |
| `overview`, `tagline` | `overview`, `tagline` | nằm trong canonical text, không là payload filter | detail `overview` → `Movie.overview`; summary không có overview |
| `release_date`, fallback `imdb_year` | `release_date` (`LocalDate`); không có cột imdb_year trong entity | `year`: năm release date, fallback imdb_year | `releaseDate` ISO date hoặc null |
| `imdb_rating`, `imdb_vote_count` | cùng tên | `rating` = IMDb rating; không có vote count trong payload | detail `imdbRating`; summary `voteAverage` ưu tiên TMDB > 0 rồi IMDb |
| `tmdb_vote_average`, `tmdb_popularity` | cùng tên | không có trong payload hiện tại | detail `tmdbVoteAverage`, `tmdbPopularity`; UI rating /10, không gọi là % match |
| `runtime_minutes` | `runtime_minutes` | `runtime` | detail `runtimeMinutes` → `Movie.runtime` |
| `original_language` | `original_language` | `language` | detail `originalLanguage`; chưa hiển thị trên card |
| `production_countries[].iso_3166_1` | **MISSING:** entity chưa có country | `country` danh sách mã quốc gia | DTO hiện tại chưa có |
| `genres[]`, `keywords[]` | quan hệ `movie_genres`, `movie_keywords`; ID TMDB không tự coi là khóa nội bộ | `genres`, `keywords` danh sách tên | DTO hiện tại không có; `Movie.genre=[]` |
| `cast[]`, `directors[]` | quan hệ `movie_cast`, `movie_crew` và `people`; cần import mapping riêng | nằm trong text, không có filter actor/director | DTO hiện tại không có; `Movie.cast=null` |
| `poster_path`, `backdrop_path` | cùng tên | không có trong payload | summary `posterUrl` thực tế mapper lấy posterPath; detail cùng camelCase → URL ảnh TMDB hoặc ảnh fallback |
| `trailer.key/site/type` | `trailer_key/site/type` | không có | detail `trailerKey/Site/Type`; chỉ embed key YouTube |
| `adult`, `status` | cùng tên | cùng tên | detail cùng tên |
| `embedding_text`, `text_template_version` | không có trong entity | dense+sparse từ cùng text; payload version/model/hash | không đưa lên card |

Ví dụ thực tế: The Godfather có `imdb_id=tt0068646`, `tmdb_id=238`, `movie_id=null`, năm 1972, IMDb 9.2, runtime 175, country `["US"]`. Cả ba sample đều chưa có MySQL ID; xem `docs/evidence/retrieval-id-audit.json`. Không tạo API response giả với ID tự gán.

## Contract frontend

`frontend/types/index.ts::Movie` là kiểu dùng chung cho `MovieCard`, `MovieRow`, featured card và qua alias `Media` cho starter. `lib/movies.ts::toMovie` chuyển DTO main sang Movie tại ranh giới lấy dữ liệu. Không dùng kiểu DTO UUID/genres-string của backend cũ.

ID API phải là số nguyên dương an toàn của JavaScript; ID vượt `Number.MAX_SAFE_INTEGER` bị từ chối thay vì làm tròn. Nếu dữ liệu đạt giới hạn này cần đổi backend JSON contract sang ID chuỗi. Null rating hiển thị “Chưa có điểm”, không giả định 0. Row có loading/error/empty states và bỏ qua response của endpoint cũ sau khi đổi endpoint.

Các route legacy `/api/discover`, `/api/popular`, `/api/trending` lấy từ starter còn tồn tại và chưa được tích hợp vào MovieRow; các row hiện tại dùng `/api/movies/top-rated` và `/api/movies/newest` qua Spring Boot. Trang search của starter chưa nối dense/sparse vì chờ mapping và backend hydrate. Không thay các module ngoài scope để giả lập search hoàn chỉnh.

## Dense/sparse và filters

`POST /internal/qdrant/search` nhận `query`, `mode` (`dense` hoặc `sparse`), `limit` (1–100), `filters`. Không triển khai hybrid hoặc tự fallback giữa hai nhánh. Query blank/unknown fields/year đảo ngược bị 422; model/Qdrant lỗi trả 503 với thông báo chung. Sparse query rỗng trả danh sách rỗng. Các giới hạn request là giới hạn triển khai của API này, không phải yêu cầu đã chốt của toàn dự án.

Bộ lọc reusable `app/services/filters.py`: `genres` → `genres`, `languages` → `language`, `countries` → `country`, `year_min/max` → `year`, `rating_min` → `rating`, `runtime_max` → `runtime`, `exclude_genres` → must_not genres. Trong mỗi danh sách là OR, giữa các field là AND. Case/value theo payload indexer, ví dụ `Drama`, `en`, `US`; không bịa enum vocabulary. Không nhận director/actor/exclude_watched vì payload/context chưa đủ. Không nới điều kiện khi không có kết quả.

Kết quả giữ score gốc từng nhánh; score bằng nhau sắp theo point ID. Deduplicate theo movie_id hợp lệ, fallback IMDb ID khi chưa mapped, cuối cùng point ID. Sau dedup có thể ít hơn limit. Mỗi hit chứa `point_id`, `movie_id` nullable, IMDb/TMDB ID, title, score, `id_status`. `present_unverified` chỉ nói payload có ID số hợp lệ, **không chứng minh tồn tại ở MySQL**. `missing`/`invalid` không được dùng để gọi movie detail. Backend hydrate giữ thứ tự ranking còn **chưa làm**, chờ CSV và xác minh import.

## Kiểm tra ID chỉ đọc

```bash
# Không có CSV/snapshot: báo INCOMPLETE và exit 1, không phải PASS.
python3 data/scripts/validate_movie_links.py

# Sau khi có CSV xuất từ bảng thật với header id,imdb_id,tmdb_id:
python3 data/scripts/validate_movie_links.py \
  --movies data/processed/movies_with_mysql_ids.jsonl \
  --mysql-csv /path/to/mysql_movie_ids.csv \
  --qdrant-url http://localhost:6335 --collection movies
```

`movies_with_mysql_ids.jsonl` ở ví dụ là artifact cần tạo sau khi đối chiếu CSV, **chưa tồn tại**. CSV header trên là format công cụ nhận theo field entity, không phải khẳng định CSV đang chờ có format này. Có thể dùng `--qdrant-jsonl` thay URL: mỗi dòng `{"id": "...", "payload": {...}}` xuất từ Qdrant, không dùng vector.

Công cụ phát hiện ID thiếu/sai, duplicate, IMDb/TMDB/movie_id mismatch, point UUID sai, missing point và orphan point. Đọc hết các trang Qdrant; scope là tất cả processed movies và points được cung cấp, MySQL CSV được phép có thêm phim ngoài sample. Không sinh ID hoặc ghi dữ liệu. Exit 0 chỉ khi đủ ba nguồn và không có issue; exit 1 khi FAIL/INCOMPLETE; exit 2 khi đọc Qdrant lỗi. CSV/table thực tế cần xác minh trước khi tạo mapping.

## Demo và kiểm tra

```bash
# Test offline: embeddings fixture, Qdrant in-memory, không tải model.
PYTHONPATH=ai-service python3 -m pytest -q ai-service/tests data/tests/test_movie_links.py

cd frontend
npm ci
npx tsc --noEmit
npm run test:contract
npm run lint
npm run build
npm run dev
# quay lại repo root trước lệnh Docker
```

```bash
# Profile ai chỉ chạy khi yêu cầu; không cần khởi động MySQL để thử retrieval.
docker compose --profile ai up -d --build qdrant ai-service
curl http://localhost:8010/internal/health
curl -X POST http://localhost:8010/internal/qdrant/search \
  -H 'Content-Type: application/json' \
  -d '{"query":"space exploration","mode":"dense","limit":5,"filters":{"countries":["US"],"rating_min":7}}'
# Đổi mode thành sparse để thử lexical retrieval.
```

Docker build context là repo root; Python 3.11 theo CI, CPU PyTorch, dependencies từ `requirements.txt`, user không phải root, port 8010. Model tải lúc search đầu tiên, cache volume riêng; không đóng gói secret/model weights. Qdrant container dùng `http://qdrant:6333`, host dùng `http://localhost:6335`. Collection cần được tạo/index bằng pipeline có sẵn trước khi search thật. Không tự import hoặc cập nhật ID sample.
