"""Conservative Vietnamese/English filter extraction for the indexed payload."""

import re

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.retrieval import MovieFilters


class ExtractedChatFilters(BaseModel):
    model_config = ConfigDict(extra="forbid")

    retrieval: MovieFilters = Field(default_factory=MovieFilters)
    director: str | None = Field(default=None, max_length=100)
    actor: str | None = Field(default=None, max_length=100)


GENRES = {
    "khoa học viễn tưởng": "Science Fiction", "sci-fi": "Science Fiction",
    "hành động": "Action", "action": "Action", "hài": "Comedy", "comedy": "Comedy",
    "kinh dị": "Horror", "horror": "Horror", "tâm lý": "Drama", "drama": "Drama",
    "tình cảm": "Romance", "romance": "Romance", "hoạt hình": "Animation",
    "animation": "Animation", "phiêu lưu": "Adventure", "adventure": "Adventure",
    "tội phạm": "Crime", "crime": "Crime", "bí ẩn": "Mystery", "mystery": "Mystery",
    "tài liệu": "Documentary", "documentary": "Documentary", "gia đình": "Family",
    "family": "Family", "giật gân": "Thriller", "thriller": "Thriller",
}
LANGUAGES = {"tiếng anh": "en", "english": "en", "tiếng hàn": "ko", "korean": "ko",
             "tiếng nhật": "ja", "japanese": "ja", "tiếng việt": "vi", "vietnamese": "vi",
             "tiếng pháp": "fr", "french": "fr", "tiếng trung": "zh", "chinese": "zh"}
COUNTRIES = {"mỹ": "US", "hoa kỳ": "US", "usa": "US", "hàn quốc": "KR",
             "south korea": "KR", "nhật bản": "JP", "japan": "JP", "việt nam": "VN",
             "vietnam": "VN", "pháp": "FR", "france": "FR", "anh quốc": "GB", "uk": "GB"}


def _contains(text: str, phrase: str) -> bool:
    return re.search(r"(?<!\w)" + re.escape(phrase) + r"(?!\w)", text) is not None


def _person(text: str, label: str) -> str | None:
    match = re.search(
        rf"(?:{label})\s*(?:bởi|by|là)?\s*[:：]?\s*([\wÀ-ỹ][\wÀ-ỹ .'-]{{1,98}}?)"
        r"(?=\s+(?:và|and|diễn viên|actor|đạo diễn|director|năm|phim|rating|điểm|từ|sau|trước)\b|[,;!?]|$)",
        text, re.IGNORECASE,
    )
    if not match:
        return None
    name = match.group(1).strip()
    if name.casefold().startswith(("phim", "của", "nào", "ai", "who", "which")) or " là ai" in name.casefold():
        return None
    return name


def extract_chat_filters(question: str, explicit: MovieFilters | None = None) -> ExtractedChatFilters:
    """Only emit recognized values; explicit JSON fields override extracted ones."""
    text = question.casefold()
    values: dict[str, object] = {}
    genres: list[str] = []
    excluded: list[str] = []
    for phrase, value in GENRES.items():
        for match in re.finditer(r"(?<!\w)" + re.escape(phrase) + r"(?!\w)", text):
            prefix = text[max(0, match.start() - 35):match.start()]
            target = excluded if re.search(
                r"(?:không|tránh|loại trừ|without|exclude)(?:\s+\w+){0,3}\s*$", prefix
            ) else genres
            if value not in target:
                target.append(value)
    if genres:
        values["genres"] = genres
    if excluded:
        values["exclude_genres"] = excluded
    languages = list(dict.fromkeys(value for phrase, value in LANGUAGES.items() if _contains(text, phrase)))
    countries = list(dict.fromkeys(value for phrase, value in COUNTRIES.items() if _contains(text, phrase)))
    if languages:
        values["languages"] = languages
    if countries:
        values["countries"] = countries

    between = re.search(r"(?:từ|between)\s*(?:năm\s*)?(\d{4})\s*(?:đến|tới|và|and|to|-)\s*(?:năm\s*)?(\d{4})", text)
    after = re.search(r"(?:sau|after|từ)\s*năm\s*(\d{4})", text)
    before = re.search(r"(?:trước|before|đến)\s*năm\s*(\d{4})", text)
    exact = re.search(r"\bnăm\s*(\d{4})\b", text)
    if between:
        values["year_min"], values["year_max"] = int(between[1]), int(between[2])
    elif after:
        values["year_min"] = int(after[1]) + (1 if text[after.start():after.end()].startswith(("sau", "after")) else 0)
    elif before:
        values["year_max"] = int(before[1]) - (1 if text[before.start():before.end()].startswith(("trước", "before")) else 0)
    elif exact:
        values["year_min"] = values["year_max"] = int(exact[1])

    rating = re.search(r"(?:imdb|rating|điểm|đánh giá)\s*(?:từ|trên|ít nhất|>=|≥|:)?\s*(\d{1,2}(?:[.,]\d)?)", text)
    if rating:
        values["rating_min"] = float(rating[1].replace(",", "."))
    runtime = re.search(r"(?:dưới|không quá|under|at most)\s*(\d{2,3})\s*(?:phút|minutes?|min)\b", text)
    if runtime:
        values["runtime_max"] = int(runtime[1])

    if explicit is not None:
        values.update(explicit.model_dump(include=explicit.model_fields_set))
    return ExtractedChatFilters(
        retrieval=MovieFilters.model_validate(values),
        director=_person(question, r"đạo diễn|director(?: by)?"),
        actor=_person(question, r"diễn viên|actor(?: starring)?|starring"),
    )
