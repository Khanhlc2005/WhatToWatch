package com.project.movie_recommendation.dto.response;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ConversationDetailResponse {
    private Long id;
    private String title;
    private List<ConversationMessageResponse> messages;
}
