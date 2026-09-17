import os
import csv
import urllib.request
import pandas as pd

os.makedirs("data/raw", exist_ok=True)

FILES = [
    "title.basics", "title.ratings", "title.crew",
    "title.principals", "title.akas", "name.basics",
]

# 1. Tải file (bỏ qua nếu đã có)
for name in FILES:
    dest = f"data/raw/{name}.tsv.gz"
    if not os.path.exists(dest):
        url = f"https://datasets.imdbws.com/{name}.tsv.gz"
        print(f"Downloading {name} ...")
        urllib.request.urlretrieve(url, dest)
    else:
        print(f"{name} đã có sẵn, bỏ qua tải lại")

CHUNK_SIZE = 100_000
TARGET_TYPES = ["movie", "tvMovie"]

# 2. Đọc title.basics theo chunk (tránh tràn RAM với ~12.7 triệu dòng), lọc ngay từng chunk
basics_chunks = []
total_raw_rows = 0

for chunk in pd.read_csv(
    "data/raw/title.basics.tsv.gz",
    sep="\t",
    na_values="\\N",
    low_memory=False,
    compression="gzip",
    quoting=csv.QUOTE_NONE,   # tránh lỗi parse do dấu " trong tên phim
    chunksize=CHUNK_SIZE,
):
    total_raw_rows += len(chunk)
    chunk = chunk[chunk["titleType"].isin(TARGET_TYPES)].copy()
    basics_chunks.append(chunk)

basics = pd.concat(basics_chunks, ignore_index=True)
del basics_chunks

print(f"Tổng số dòng title.basics gốc (chưa lọc): {total_raw_rows:,}")
print(f"Số lượng sau lọc movie + tvMovie: {len(basics):,}")
print(basics["titleType"].value_counts())

# 3. Đọc title.ratings theo chunk, chỉ giữ rating của phim đã lọc
movie_ids = set(basics["tconst"])
ratings_chunks = []

for chunk in pd.read_csv(
    "data/raw/title.ratings.tsv.gz",
    sep="\t",
    na_values="\\N",
    low_memory=False,
    compression="gzip",
    quoting=csv.QUOTE_NONE,
    chunksize=CHUNK_SIZE,
):
    chunk = chunk[chunk["tconst"].isin(movie_ids)].copy()
    ratings_chunks.append(chunk)

ratings = pd.concat(ratings_chunks, ignore_index=True)
del ratings_chunks, movie_ids

# 4. Join với ratings
movies = basics.merge(ratings, on="tconst", how="left")
del basics, ratings

# 5. Lọc theo ngưỡng vote tối thiểu
MIN_VOTES = 50
movies_filtered = movies[movies["numVotes"] >= MIN_VOTES].copy()
del movies
print(f"Số movie sau lọc numVotes >= {MIN_VOTES}: {len(movies_filtered):,}")

# 6. Thống kê nhanh
print(movies_filtered["startYear"].describe())
print(movies_filtered["genres"].dropna().head(10))

# 7. Lưu lại bản đã lọc
os.makedirs("data/processed", exist_ok=True)
movies_filtered.to_csv("data/processed/movies_filtered_step1.csv", index=False)
print("Đã lưu data/processed/movies_filtered_step1.csv")