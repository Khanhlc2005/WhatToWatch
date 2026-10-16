package com.project.movie_recommendation.dto.response;

import lombok.*;
import lombok.experimental.FieldDefaults;

import java.time.LocalDateTime;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@FieldDefaults(level = AccessLevel.PRIVATE)
public class WatchlistResponse {
    Long id;
    String name;
    long movieCount;
    LocalDateTime createdAt;
}