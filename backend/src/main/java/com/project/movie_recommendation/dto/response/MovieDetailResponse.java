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
    String title;
    String overview;
    String posterUrl;
    LocalDate releaseDate;
    Double voteAverage;
    Integer runtime;
    String trailerYoutubeKey;
    String genres;
    String cast;
}