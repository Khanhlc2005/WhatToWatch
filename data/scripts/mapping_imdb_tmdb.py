import time
import requests
import pandas as pd
from dotenv import load_dotenv
import os

load_dotenv()
API_KEY = os.getenv("TMDB_API")

# 0. Kiểm tra key hợp lệ trước khi chạy hàng loạt
_check = requests.get(
    "https://api.themoviedb.org/3/movie/157336",
    params={"api_key": API_KEY}, timeout=10,
)
if _check.status_code == 401:
    raise SystemExit(f"API key không hợp lệ: {_check.json()}")
print("Key hợp lệ.")

# 1. Đọc lại kết quả IMDb
movies = pd.read_csv("data/processed/movies_filtered_step1.csv")
print("Số phim cần mapping:", len(movies))

# 2. tìm tmdb_id qua endpoint /find
def find_by_imdb_id(imdb_id):
    url = f"https://api.themoviedb.org/3/find/{imdb_id}"
    params = {"api_key": API_KEY, "external_source": "imdb_id"}
    r = requests.get(url, params=params, timeout=10)
    if r.status_code != 200:
        return None
    results = r.json().get("movie_results", [])
    return results[0]["id"] if results else None

# Test trên một mẫu nhỏ
sample = movies.head(50).copy()
sample["tmdb_id"] = None
for idx, row in sample.iterrows():
    tmdb_id = find_by_imdb_id(row["tconst"])
    sample.loc[idx, "tmdb_id"] = tmdb_id
    time.sleep(0.05)  # tránh dồn request quá nhanh

matched = sample["tmdb_id"].notna().sum()
print(f"Mapping được {matched}/{len(sample)} phim qua /find")

# 3. Đối chiếu với dữ liệu từ MovieLens
# links.csv: https://files.grouplens.org/datasets/movielens/ml-32m.zip
links = pd.read_csv("data/raw/links.csv")  # columns: movieId, imdbId, tmdbId
links["tconst"] = "tt" + links["imdbId"].astype(str).str.zfill(7)

merged = sample.merge(links[["tconst", "tmdbId"]], on="tconst", how="left")
mismatch = merged[
    merged["tmdb_id"].notna()
    & merged["tmdbId"].notna()
    & (merged["tmdb_id"].astype(float) != merged["tmdbId"].astype(float))
]
print(f"Số phim tmdb_id lệch giữa /find và MovieLens: {len(mismatch)}")

# 4. Log các phim không map được ở cả 2 cách
unmatched = merged[merged["tmdb_id"].isna() & merged["tmdbId"].isna()]
unmatched.to_csv("data/processed/unmatched_step3.csv", index=False)
print(f"Số phim không map được (log ra unmatched_step3.csv): {len(unmatched)}")