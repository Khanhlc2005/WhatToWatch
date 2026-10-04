package com.project.movie_recommendation.dto.response;

import lombok.*;
import lombok.experimental.FieldDefaults;

import java.time.LocalDateTime;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@FieldDefaults(level = AccessLevel.PRIVATE)
public class WatchHistoryResponse {
    Long id;
    Long movieId;
    String title;
    String posterPath;
    String eventType;
    Integer progressSeconds;
    LocalDateTime createdAt;
}