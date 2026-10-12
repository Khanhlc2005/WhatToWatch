package com.project.movie_recommendation.dto.ai;

import lombok.*;
import lombok.experimental.FieldDefaults;
import com.fasterxml.jackson.annotation.JsonProperty;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@FieldDefaults(level = AccessLevel.PRIVATE)
public class AiMovieSearchRequest {
    String query;

    @Builder.Default
    String mode = "hybrid";

    @Builder.Default
    int limit = 20;

    @Builder.Default
    boolean rerank = true;

    @JsonProperty("candidate_k")
    Integer candidateK;
}
