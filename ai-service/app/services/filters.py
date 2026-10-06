from qdrant_client import models

from app.schemas.retrieval import MovieFilters


def build_payload_filter(filters: MovieFilters) -> models.Filter | None:
    must = []
    must_not = []
    for field, values in (
        ("genres", filters.genres),
        ("language", filters.languages),
        ("country", filters.countries),
    ):
        if values:
            must.append(models.FieldCondition(key=field, match=models.MatchAny(any=values)))
    if filters.exclude_genres:
        must_not.append(models.FieldCondition(
            key="genres", match=models.MatchAny(any=filters.exclude_genres)
        ))
    for field, lower, upper in (
        ("year", filters.year_min, filters.year_max),
        ("rating", filters.rating_min, None),
        ("runtime", None, filters.runtime_max),
    ):
        if lower is not None or upper is not None:
            must.append(models.FieldCondition(key=field, range=models.Range(gte=lower, lte=upper)))
    return models.Filter(must=must, must_not=must_not) if must or must_not else None
