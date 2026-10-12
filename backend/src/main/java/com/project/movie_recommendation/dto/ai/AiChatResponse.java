package com.project.movie_recommendation.dto.ai;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.*;
import lombok.experimental.FieldDefaults;

import java.util.List;
import java.util.Map;

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
    @JsonProperty("applied_filters")
    Map<String, Object> appliedFilters;
    @JsonProperty("tool_name")
    String toolName;

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
