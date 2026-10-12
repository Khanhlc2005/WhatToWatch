package com.project.movie_recommendation.dto.response;

import com.project.movie_recommendation.dto.ai.AiChatResponse;
import lombok.*;
import lombok.experimental.FieldDefaults;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@FieldDefaults(level = AccessLevel.PRIVATE)
public class ChatMessageResponse {
    Long conversationId;
    String status;
    String reply;
    List<AiChatResponse.AiMovieItem> recommendedMovies;
    Map<String, Object> appliedFilters;
    String toolName;
    LocalDateTime createdAt;
}
