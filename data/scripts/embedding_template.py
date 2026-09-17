import requests
from dotenv import load_dotenv
import os

load_dotenv()
API_KEY = os.getenv("TMDB_API")

def get_full_movie(tmdb_id):
    url = f"https://api.themoviedb.org/3/movie/{tmdb_id}"
    params = {"api_key": API_KEY, "append_to_response": "credits,keywords"}
    return requests.get(url, params=params, timeout=10).json()

def build_embedding_text(data):
    genres = ", ".join(g["name"] for g in data.get("genres", []))
    keywords = ", ".join(k["name"] for k in data.get("keywords", {}).get("keywords", []))
    director_list = [c["name"] for c in data.get("credits", {}).get("crew", []) if c["job"] == "Director"]
    director = ", ".join(director_list)
    top_cast = ", ".join(c["name"] for c in data.get("credits", {}).get("cast", [])[:5])
    countries = ", ".join(c["name"] for c in data.get("production_countries", []))

    text = f"""Title: {data.get('title', '')}
Original Title: {data.get('original_title', '')}
Genres: {genres}
Keywords: {keywords}
Overview: {data.get('overview', '')}
Tagline: {data.get('tagline', '') or ''}
Director: {director}
Cast: {top_cast}
Production Countries: {countries}
Original Language: {data.get('original_language', '')}"""
    return text

# Test trên 3 phim thật
test_ids = [157336, 550, 238]  # Interstellar, Fight Club, The Godfather

for mid in test_ids:
    data = get_full_movie(mid)
    text = build_embedding_text(data)
    print("=" * 50)
    print(text)
    print()
    # Kiểm tra các field numeric KHÔNG bị lẫn vào text
    for forbidden in [str(data.get("release_date", "")), str(data.get("vote_average", "")), str(data.get("runtime", ""))]:
        assert forbidden not in text or forbidden == "", f"Cảnh báo: field numeric '{forbidden}' xuất hiện trong text!"