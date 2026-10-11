package com.project.movie_recommendation.dto.ai;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.*;
import lombok.experimental.FieldDefaults;

import java.util.Collections;
import java.util.List;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@FieldDefaults(level = AccessLevel.PRIVATE)
public class AiMovieSearchResponse {
    String collection;
    String mode;

    @Builder.Default
    List<Hit> hits = Collections.emptyList();

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @FieldDefaults(level = AccessLevel.PRIVATE)
    public static class Hit {
        @JsonProperty("point_id")
        String pointId;

        @JsonProperty("movie_id")
        Long movieId;

        @JsonProperty("imdb_id")
        String imdbId;

        @JsonProperty("tmdb_id")
        Long tmdbId;

        String title;
        List<String> genres;
        Double score;

        @JsonProperty("id_status")
        String idStatus;
    }
}
