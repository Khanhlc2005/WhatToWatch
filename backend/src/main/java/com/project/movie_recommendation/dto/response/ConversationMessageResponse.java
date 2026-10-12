package com.project.movie_recommendation.dto.response;

import com.project.movie_recommendation.dto.ai.AiChatResponse;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.List;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ConversationMessageResponse {
    private Long id;
    private String role;
    private String content;
    private List<AiChatResponse.AiMovieItem> recommendedMovies;
    private String toolName;
    private LocalDateTime createdAt;
}
