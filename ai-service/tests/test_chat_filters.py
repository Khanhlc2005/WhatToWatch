import pytest
from pydantic import ValidationError

from app.schemas.retrieval import MovieFilters
from app.services.chat_filters import extract_chat_filters


def test_vietnamese_filters_are_validated_json() -> None:
    result = extract_chat_filters(
        "Gợi ý phim khoa học viễn tưởng từ năm 2010 đến 2020 điểm IMDb trên 7.5 dưới 150 phút"
    )
    assert result.model_dump(mode="json", exclude_none=True) == {
        "retrieval": {
            "genres": ["Science Fiction"], "exclude_genres": [], "languages": [],
            "countries": [], "year_min": 2010, "year_max": 2020,
            "rating_min": 7.5, "runtime_max": 150,
        }
    }


def test_country_language_person_and_explicit_override() -> None:
    result = extract_chat_filters(
        "Phim Hàn Quốc tiếng Hàn do đạo diễn Bong Joon-ho",
        MovieFilters(year_min=2019),
    )
    assert result.retrieval.countries == ["KR"]
    assert result.retrieval.languages == ["ko"]
    assert result.retrieval.year_min == 2019
    assert result.director == "Bong Joon-ho"


def test_factual_questions_do_not_extract_people_as_filter() -> None:
    assert extract_chat_filters("Ai đạo diễn phim này?").director is None
    assert extract_chat_filters("Phim này có diễn viên nào?").actor is None


def test_invalid_natural_range_is_rejected() -> None:
    with pytest.raises(ValidationError):
        extract_chat_filters("Phim từ năm 2020 đến 2010")


def test_negative_genre_becomes_exclusion() -> None:
    result = extract_chat_filters("Gợi ý phim hành động nhưng tránh phim kinh dị")
    assert result.retrieval.genres == ["Action"]
    assert result.retrieval.exclude_genres == ["Horror"]
