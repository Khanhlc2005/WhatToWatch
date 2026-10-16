package com.project.movie_recommendation.dto.request;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.*;
import lombok.experimental.FieldDefaults;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@FieldDefaults(level = AccessLevel.PRIVATE)
public class WatchlistRequest {
    @NotBlank(message = "WATCHLIST_NAME_REQUIRED")
    @Size(max = 255, message = "WATCHLIST_NAME_INVALID")
    String name;
}