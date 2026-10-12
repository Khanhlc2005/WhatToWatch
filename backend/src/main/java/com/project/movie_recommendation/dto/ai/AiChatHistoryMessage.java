package com.project.movie_recommendation.dto.ai;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AiChatHistoryMessage {
    private String role;
    private String content;
    @JsonProperty("movie_ids")
    private List<Integer> movieIds;
}
