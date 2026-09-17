import time
import requests
import pandas as pd
from dotenv import load_dotenv
import os

load_dotenv()
API_KEY = os.getenv("TMDB_API")
BASE_URL = "https://api.themoviedb.org/3"

def get_movie(movie_id):
    url = f"{BASE_URL}/movie/{movie_id}"
    params = {"api_key": API_KEY, "append_to_response": "credits,keywords,videos"}
    return requests.get(url, params=params, timeout=10)

# 0. Kiểm tra key hợp lệ trước khi chạy hàng loạt
check = get_movie(157336)
if check.status_code == 401:
    raise SystemExit(
        f"API key không hợp lệ (401): {check.json()}\n"
        "-> Vào themoviedb.org/settings/api và copy đúng ô 'API Key (v3 auth)', "
        "không dùng 'API Read Access Token'."
    )
print("Key hợp lệ, status:", check.status_code)

# 1. Đo rate limit: gọi liên tiếp, xem lúc nào bị chặn (429)
sample_ids = list(range(1, 61))
status_codes = []
start = time.time()

for mid in sample_ids:
    r = get_movie(mid)
    status_codes.append(r.status_code)
    if r.status_code == 429:
        print(f"Bị rate-limit ở request thứ {len(status_codes)}")
        print("Retry-After header:", r.headers.get("Retry-After"))
        break

elapsed = time.time() - start
print(f"Gọi {len(status_codes)} request trong {elapsed:.2f}s")
print("Status code khác 200:", [c for c in status_codes if c != 200])

# 2. Kiểm tra field hay bị null trên một mẫu phim
FIELDS_TO_CHECK = [
    "overview", "tagline", "poster_path", "backdrop_path",
    "release_date", "runtime", "original_language",
]
sample_ids_real = [157336, 550, 27205, 11, 603, 238, 424, 13, 429, 278]
rows = []

for mid in sample_ids_real:
    r = get_movie(mid)
    if r.status_code != 200:
        print(f"Bỏ qua id {mid}, status {r.status_code}: {r.text[:200]}")
        continue
    data = r.json()
    row = {"id": mid, "title": data.get("title")}
    for f in FIELDS_TO_CHECK:
        row[f] = data.get(f)
    videos = data.get("videos", {}).get("results", [])
    trailer = next((v for v in videos if v["site"] == "YouTube" and v["type"] == "Trailer"), None)
    row["has_trailer"] = trailer is not None
    crew = data.get("credits", {}).get("crew", [])
    director = next((c for c in crew if c["job"] == "Director"), None)
    row["has_director"] = director is not None
    rows.append(row)

df = pd.DataFrame(rows)
print(df)

if df.empty:
    print("Không có phim nào lấy được dữ liệu — kiểm tra lại API key/kết nối mạng trước khi tiếp tục.")
else:
    print("\nTỉ lệ null theo field:")
    print(df.isnull().mean().sort_values(ascending=False))
    print(f"\nTỉ lệ có trailer: {df['has_trailer'].mean():.0%}")
    print(f"Tỉ lệ có director: {df['has_director'].mean():.0%}")