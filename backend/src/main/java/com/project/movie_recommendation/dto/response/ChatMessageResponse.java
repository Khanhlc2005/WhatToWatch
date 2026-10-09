package com.project.movie_recommendation.dto.response;

import com.project.movie_recommendation.dto.ai.AiChatResponse;
import lombok.*;
import lombok.experimental.FieldDefaults;

import java.time.LocalDateTime;
import java.util.List;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@FieldDefaults(level = AccessLevel.PRIVATE)
public class ChatMessageResponse {
    Long conversationId;
    String reply;
    List<AiChatResponse.AiMovieItem> recommendedMovies;
    LocalDateTime createdAt;
}