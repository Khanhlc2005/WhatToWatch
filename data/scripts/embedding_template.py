"""Tạo văn bản truy hồi chuẩn từ bản ghi phim IMDb–TMDB đã làm sạch."""

TEXT_TEMPLATE_VERSION = "movie_text_v1"
TOP_CAST_LIMIT = 5


def _names(items):
    return ", ".join(item["name"] for item in items)


def build_embedding_text(movie):
    """Tạo một văn bản nhất quán từ bản ghi do clean_movies.py sinh ra.

    Không thêm các trường số dùng để lọc hoặc xếp hạng. Bỏ qua trường ngữ nghĩa
    bị thiếu thay vì in nhãn rỗng hoặc ``None``.
    """
    fields = (
        ("Title", movie["title"]),
        ("Original Title", movie.get("original_title")),
        ("Genres", _names(movie.get("genres", []))),
        ("Keywords", _names(movie.get("keywords", []))),
        ("Overview", movie.get("overview")),
        ("Tagline", movie.get("tagline")),
        ("Director", _names(movie.get("directors", []))),
        ("Top Cast", _names(movie.get("cast", [])[:TOP_CAST_LIMIT])),
        ("Production Countries", _names(movie.get("production_countries", []))),
        ("Original Language", movie.get("original_language")),
    )
    return "\n".join(f"{label}: {value}" for label, value in fields if value)
