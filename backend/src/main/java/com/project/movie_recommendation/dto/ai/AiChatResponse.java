package com.project.movie_recommendation.dto.ai;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.*;
import lombok.experimental.FieldDefaults;

import java.util.List;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@FieldDefaults(level = AccessLevel.PRIVATE)
public class AiChatResponse {
    String status;
    String answer;
    String reply;
    List<AiMovieItem> movies;

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @FieldDefaults(level = AccessLevel.PRIVATE)
    public static class AiMovieItem {
        @JsonProperty("movie_id")
        String movieId;
        String title;
        String reason;
    }
}