import pandas as pd

query_set = [
    {"query": "Interstellar", "type": "exact_title", "expected_movie_ids": [157336]},
    {"query": "phim khoa học viễn tưởng về du hành thời gian và tình cha con", "type": "semantic", "expected_movie_ids": [157336]},
    {"query": "phim của Christopher Nolan có Matthew McConaughey", "type": "actor_director", "expected_movie_ids": [157336]},
    {"query": "phim hài lãng mạn hay nhất", "type": "genre", "expected_movie_ids": []},
    {"query": "phim hành động sau 2020, đánh giá trên 7.5", "type": "combined_filter", "expected_movie_ids": []},
    {"query": "còn phim nào tương tự nhưng ngắn hơn không?", "type": "conversational_followup", "expected_movie_ids": []},
]

df = pd.DataFrame(query_set)
df.to_csv("data/processed/evaluation_query_set_v0.csv", index=False)
print(df)
print(f"\nĐã lưu {len(df)} query mẫu vào data/processed/evaluation_query_set_v0.csv")