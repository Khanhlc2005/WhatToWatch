package com.project.movie_recommendation.dto.response;

import lombok.*;
import lombok.experimental.FieldDefaults;

import java.util.Collections;
import java.util.List;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@FieldDefaults(level = AccessLevel.PRIVATE)
public class HomeFeedResponse {
    MovieDetailResponse heroMovie;
    String recommendationStatus;

    @Builder.Default
    List<MovieSummaryResponse> recommendedForYou = Collections.emptyList();

    @Builder.Default
    List<MovieSummaryResponse> topRated = Collections.emptyList();

    @Builder.Default
    List<MovieSummaryResponse> newest = Collections.emptyList();

    @Builder.Default
    List<GenreRowResponse> genreRows = Collections.emptyList();

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @FieldDefaults(level = AccessLevel.PRIVATE)
    public static class GenreRowResponse {
        Long genreId;
        String genreName;

        @Builder.Default
        List<MovieSummaryResponse> movies = Collections.emptyList();
    }
}