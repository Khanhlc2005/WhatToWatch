package com.project.movie_recommendation.dto.response;

import lombok.*;
import lombok.experimental.FieldDefaults;

import java.time.LocalDate;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@FieldDefaults(level = AccessLevel.PRIVATE)
public class MovieDetailResponse {
    String id;
    String imdbId;
    Long tmdbId;
    String title;
    String originalTitle;
    String overview;
    String tagline;
    LocalDate releaseDate;
    Integer runtimeMinutes;
    String originalLanguage;
    Boolean adult;
    Double imdbRating;
    Long imdbVoteCount;
    Double tmdbVoteAverage;
    Double tmdbPopularity;
    String status;
    String posterPath;
    String backdropPath;
    String trailerKey;
    String trailerSite;
    String trailerType;
}