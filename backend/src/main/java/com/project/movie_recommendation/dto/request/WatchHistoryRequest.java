package com.project.movie_recommendation.dto.request;

import jakarta.validation.constraints.NotNull;
import lombok.*;
import lombok.experimental.FieldDefaults;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@FieldDefaults(level = AccessLevel.PRIVATE)
public class WatchHistoryRequest {
    @NotNull(message = "Movie ID is required")
    Long movieId;
    String eventType;
    Integer progressSeconds;
}