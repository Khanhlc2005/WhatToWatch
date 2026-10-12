package com.project.movie_recommendation.dto.ai;

import lombok.*;
import lombok.experimental.FieldDefaults;
import java.util.List;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@FieldDefaults(level = AccessLevel.PRIVATE)
public class AiChatRequest {
    String message;
    List<AiChatHistoryMessage> history;
    String summary;
}
