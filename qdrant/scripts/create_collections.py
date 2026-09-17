from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, SparseVectorParams, PointStruct,
)

client = QdrantClient(url="http://localhost:6333")

# 1. Tạo collection "movies": named vectors dense + sparse
if client.collection_exists("movies"):
    client.delete_collection("movies")
client.create_collection(
    collection_name="movies",
    vectors_config={
        "dense": VectorParams(size=1024, distance=Distance.COSINE),  # BGE-M3 dense = 1024 chiều
    },
    sparse_vectors_config={
        "sparse": SparseVectorParams(),
    },
)

# 2. Tạo collection "user_profiles": chỉ cần dense vector
if client.collection_exists("user_profiles"):
    client.delete_collection("user_profiles")
client.create_collection(
    collection_name="user_profiles",
    vectors_config={
        "dense": VectorParams(size=1024, distance=Distance.COSINE),
    },
)

print(client.get_collections())

# 3. Ví dụ insert thử 1 point vào "movies" để kiểm tra payload đúng schema
example_payload = {
    "movie_id": 157336,
    "genres": ["Science Fiction", "Drama"],
    "year": 2014,
    "rating": 8.6,
    "language": "en",
    "country": ["US", "GB"],
    "runtime": 169,
    "keywords": ["space travel", "wormhole"],
    "adult": False,
    "status": "Released",
}
dummy_dense = [0.0] * 1024  # thay bằng vector thật khi có BGE-M3

client.upsert(
    collection_name="movies",
    points=[
        PointStruct(id=157336, vector={"dense": dummy_dense}, payload=example_payload)
    ],
)
print(client.retrieve(collection_name="movies", ids=[157336]))