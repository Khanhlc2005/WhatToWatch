package com.project.movie_recommendation.dto.response;

import lombok.*;
import lombok.experimental.FieldDefaults;

import java.time.LocalDate;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@FieldDefaults(level = AccessLevel.PRIVATE)
public class MovieSummaryResponse {
    String id;
    String title;
    String posterUrl;
    String backdropUrl;
    Double voteAverage;
    LocalDate releaseDate;
    String overview;
    String genres;
}