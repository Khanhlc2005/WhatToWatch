package com.project.movie_recommendation.dto.response;

import lombok.*;
import lombok.experimental.FieldDefaults;

import java.time.LocalDate;
import java.util.List;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@FieldDefaults(level = AccessLevel.PRIVATE)
public class MovieDetailResponse {
    Long id;
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

    List<CastResponse> cast;
    List<CrewResponse> crew;

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @FieldDefaults(level = AccessLevel.PRIVATE)
    public static class CastResponse {
        Long personId;
        String name;
        String characterName;
        Integer castOrder;
    }

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @FieldDefaults(level = AccessLevel.PRIVATE)
    public static class CrewResponse {
        Long personId;
        String name;
        String job;
        String department;
    }
}