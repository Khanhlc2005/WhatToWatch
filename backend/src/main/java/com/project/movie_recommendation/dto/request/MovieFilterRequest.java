package com.project.movie_recommendation.dto.request;

import lombok.AccessLevel;
import lombok.Data;
import lombok.experimental.FieldDefaults;
import java.util.List;

@Data
@FieldDefaults(level = AccessLevel.PRIVATE)
public class MovieFilterRequest {
    List<Long> genreIds;
    Integer yearFrom;
    Integer yearTo;
    Double minRating;
    Double maxRating;
    String language;
    Integer minRuntime;
    Integer maxRuntime;
}